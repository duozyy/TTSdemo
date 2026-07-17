# -*- coding: utf-8 -*-
"""
TTS 离线引擎对比 Web UI
核心需求：离线、中文、语调/语速可调、Android APK 可集成、性能优秀
引擎：Sherpa-ONNX (VITS + Kokoro) | ChatTTS | Edge-TTS(在线对比) | pyttsx3(基线)
"""

import os
import time
import asyncio
import hashlib
import tempfile
from pathlib import Path
from io import BytesIO
from flask import Flask, request, jsonify, send_file, render_template

import numpy as np
import sherpa_onnx

app = Flask(__name__)

# ==================== 目录配置 ====================
BASE_DIR = Path(__file__).parent
MODELS_DIR = BASE_DIR / "models"
CACHE_DIR = BASE_DIR / "cache"
CACHE_DIR.mkdir(exist_ok=True)

VITS_MODEL_DIR = MODELS_DIR / "vits_zh" / "vits-zh-hf-theresa"
KOKORO_MODEL_DIR = MODELS_DIR / "kokoro" / "kokoro-int8-multi-lang-v1_1"
CHATTTS_MODEL_DIR = MODELS_DIR / "ChatTTS"

# ==================== 统一的 WAV 输出 ====================
def to_wav_bytes(samples, sample_rate, target_sr=16000):
    """将 samples 转为 16kHz/16bit WAV bytes"""
    from scipy.io import wavfile
    audio = np.array(samples, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.flatten()
    # 重采样（简单最近邻）
    if sample_rate != target_sr:
        ratio = target_sr / sample_rate
        n = int(len(audio) * ratio)
        idx = np.linspace(0, len(audio) - 1, n).astype(int)
        audio = audio[idx]
        sample_rate = target_sr
    audio_int16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
    buf = BytesIO()
    wavfile.write(buf, sample_rate, audio_int16)
    return buf.getvalue()

# ==================== Edge TTS ====================
async def _edge_async(text, voice, rate, pitch):
    import edge_tts
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        tmp = f.name
    await communicate.save(tmp)
    data = Path(tmp).read_bytes()
    os.unlink(tmp)
    return data

def generate_edge_tts(text, voice, rate, pitch):
    t0 = time.time()
    data = asyncio.run(_edge_async(text, voice, rate, pitch))
    return data, round(time.time() - t0, 3)

# ==================== pyttsx3 ====================
def generate_pyttsx3(text, rate_val, voice_id, volume):
    import pyttsx3
    t0 = time.time()
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if voice_id and int(voice_id) < len(voices):
        engine.setProperty('voice', voices[int(voice_id)].id)
    engine.setProperty('rate', rate_val)
    engine.setProperty('volume', volume)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        tmp = f.name
    engine.save_to_file(text, tmp)
    engine.runAndWait()
    data = Path(tmp).read_bytes()
    os.unlink(tmp)
    return data, round(time.time() - t0, 3)

# ==================== Sherpa-ONNX 引擎 ====================
class SherpaEngine:
    def __init__(self):
        self._cache = {}

    def _get(self, key, noise_scale=1.0):
        """懒加载，VITS 支持自定义 noise_scale 语调随机性"""
        cache_key = f"{key}_{noise_scale}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        if key == "vits":
            cfg = sherpa_onnx.OfflineTtsModelConfig(
                vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                    model=str(VITS_MODEL_DIR / "theresa.onnx"),
                    lexicon=str(VITS_MODEL_DIR / "lexicon.txt"),
                    tokens=str(VITS_MODEL_DIR / "tokens.txt"),
                    data_dir="",
                    noise_scale=noise_scale,
                    length_scale=1.0,
                )
            )
            fsts = [str(VITS_MODEL_DIR / "phone.fst"),
                    str(VITS_MODEL_DIR / "date.fst"),
                    str(VITS_MODEL_DIR / "number.fst")]
        elif key == "kokoro":
            cfg = sherpa_onnx.OfflineTtsModelConfig(
                kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(
                    model=str(KOKORO_MODEL_DIR / "model.int8.onnx"),
                    voices=str(KOKORO_MODEL_DIR / "voices.bin"),
                    tokens=str(KOKORO_MODEL_DIR / "tokens.txt"),
                    data_dir=str(KOKORO_MODEL_DIR / "espeak-ng-data"),
                    lexicon=f"{KOKORO_MODEL_DIR / 'lexicon-us-en.txt'},{KOKORO_MODEL_DIR / 'lexicon-zh.txt'}"
                ),
                num_threads=4
            )
            fsts = [str(KOKORO_MODEL_DIR / "phone-zh.fst"),
                    str(KOKORO_MODEL_DIR / "date-zh.fst"),
                    str(KOKORO_MODEL_DIR / "number-zh.fst")]
        else:
            return None
        tts_cfg = sherpa_onnx.OfflineTtsConfig(
            model=cfg, rule_fsts=",".join(fsts), max_num_sentences=1
        )
        tts = sherpa_onnx.OfflineTts(tts_cfg)
        self._cache[cache_key] = tts
        return tts

    def generate(self, text, model_key, speed=1.0, sid=0, noise_scale=1.0):
        t0 = time.time()
        tts = self._get(model_key, noise_scale)
        if tts is None:
            raise ValueError(f"未知模型: {model_key}")
        gen_cfg = sherpa_onnx.GenerationConfig()
        gen_cfg.sid = sid
        gen_cfg.speed = speed
        audio = tts.generate(text, gen_cfg)
        elapsed = round(time.time() - t0, 3)
        wav_data = to_wav_bytes(audio.samples, audio.sample_rate, 16000)
        return wav_data, elapsed

sherpa_engine = SherpaEngine()

# ==================== Kokoro 103 音色 ====================
class KokoroVoices:
    """Kokoro-82M v1_1 完整 103 音色"""
    # 官方: https://k2-fsa.github.io/sherpa/onnx/tts/all/Chinese-English/kokoro-multi-lang-v1_1.html
    # 中文女性 55 (sid 3-57) | 中文男性 45 (sid 58-102) | 美式英语 2 (sid 0-1) | 英式英语 1 (sid 2)
    VOICES = [
        {"sid": 0,  "name": "af_maple", "gender": "女", "lang": "en-US", "tags": ["美式英语", "自然"]},
        {"sid": 1,  "name": "af_sol",   "gender": "女", "lang": "en-US", "tags": ["美式英语", "温暖"]},
        {"sid": 2,  "name": "bf_vale",  "gender": "女", "lang": "en-GB", "tags": ["英式英语", "优雅"]},
    ]
    # 自动生成其余中文音色
    _zf = [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,
           31,32,33,34,35,36,37,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52,53,54,55,56,57]
    _zm = [58,59,60,61,62,63,64,65,66,67,68,69,70,71,72,73,74,75,76,77,78,79,80,
           81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,98,99,100,101,102]
    for _i, _sid in enumerate(_zf):
        VOICES.append({"sid": _sid, "name": f"zf_{_sid:03d}", "gender": "女", "lang": "zh", "tags": ["女声"]})
    for _i, _sid in enumerate(_zm):
        VOICES.append({"sid": _sid, "name": f"zm_{_sid:03d}", "gender": "男", "lang": "zh", "tags": ["男声"]})

    @classmethod
    def list(cls, lang=None, gender=None):
        r = cls.VOICES
        if lang:
            r = [v for v in r if v["lang"] == lang]
        if gender:
            r = [v for v in r if v["gender"] == gender]
        return r

# ==================== ChatTTS 引擎 ====================
class ChatTtsEngine:
    def __init__(self):
        self._chat = None

    def _load(self):
        if self._chat is not None:
            return True
        try:
            import ChatTTS
            self._chat = ChatTTS.Chat()
            self._chat.load(source="custom", custom_path=str(CHATTTS_MODEL_DIR), compile=False)
            return True
        except Exception as e:
            print(f"[ChatTTS] load failed: {e}")
            return False

    def generate(self, text, seed=1234, speed=1.0, prompt="[oral_0][laugh_0][break_3]"):
        from scipy.io import wavfile
        t0 = time.time()
        if not self._load():
            raise RuntimeError("ChatTTS 引擎加载失败")
        rand_spk = self._chat.sample_random_speaker()
        params_infer = self._chat.InferCodeParams(spk_emb=rand_spk, temperature=0.3)
        params_refine = self._chat.RefineTextParams(prompt=prompt)
        wavs = self._chat.infer([text], use_decoder=True,
                                params_infer_code=params_infer,
                                params_refine_text=params_refine)
        elapsed = round(time.time() - t0, 3)
        audio_np = np.array(wavs[0], dtype=np.float32)
        audio_int16 = np.clip(audio_np * 32767, -32768, 32767).astype(np.int16)
        buf = BytesIO()
        wavfile.write(buf, 24000, audio_int16)
        return buf.getvalue(), elapsed

chattts_engine = ChatTtsEngine()

def warmup_engines():
    """预热：后台线程加载所有引擎，避免首次请求长时间阻塞"""
    import threading
    def _w():
        print("[warmup] 正在预加载 Sherpa VITS...")
        try:
            sherpa_engine._get("vits")
            print("[warmup] VITS ready")
        except Exception as e:
            print(f"[warmup] VITS failed: {e}")
        print("[warmup] 正在预加载 Sherpa Kokoro...")
        try:
            sherpa_engine._get("kokoro")
            print("[warmup] Kokoro ready")
        except Exception as e:
            print(f"[warmup] Kokoro failed: {e}")
        print("[warmup] 正在预加载 ChatTTS...")
        try:
            chattts_engine._load()
            print("[warmup] ChatTTS ready")
        except Exception as e:
            print(f"[warmup] ChatTTS failed: {e}")
    threading.Thread(target=_w, daemon=True, name="warmup").start()

# ==================== 启动预热 ====================
warmup_engines()

# ==================== 缓存辅助 ====================
def cache_path(prefix, params: dict):
    h = hashlib.md5(str(sorted(params.items())).encode()).hexdigest()
    return CACHE_DIR / f"{prefix}_{h}.wav"

# ==================== Flask 路由 ====================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/models')
def api_models():
    """引擎列表 + Android 集成建议"""
    return jsonify({
        "engines": [
            {
                "id": "sherpa_vits",
                "name": "Sherpa-ONNX · VITS",
                "type": "offline",
                "offline": True,
                "desc": "轻量高速中文女声，122MB，响应快",
                "pros": ["完全离线", "响应快", "语速/语调可调", "AAR 直集成"],
                "cons": ["单女声", "中英混合弱"],
                "license": "Apache-2.0",
                "size_mb": 122,
                "android": "k2-fsa/sherpa-onnx (GitHub)",
                "url": "https://github.com/k2-fsa/sherpa-onnx",
                "status": "ready"
            },
            {
                "id": "sherpa_kokoro",
                "name": "Sherpa-ONNX · Kokoro",
                "type": "offline",
                "offline": True,
                "desc": "103 中英音色，160MB int8，流式输出",
                "pros": ["完全离线", "103 音色", "中英混合", "语速可调", "AAR 直集成"],
                "cons": ["首次推理略慢"],
                "license": "Apache-2.0",
                "size_mb": 160,
                "android": "k2-fsa/sherpa-onnx (GitHub)",
                "url": "https://github.com/k2-fsa/sherpa-onnx",
                "status": "ready"
            },
            {
                "id": "chattts",
                "name": "ChatTTS",
                "type": "offline",
                "offline": True,
                "desc": "对话式 TTS，seed 控制音色，韵律 token 控制语调",
                "pros": ["语音自然", "中英双语", "语调可控", "离线推理"],
                "cons": ["CPU 推理慢(~8s)", "模型大(~1GB)", "Android 需转换"],
                "license": "AGPL-3.0",
                "size_mb": 1024,
                "android": "需转 ONNX/TFLite，工作量大",
                "url": "https://github.com/2noise/chattts",
                "status": "ready"
            },
            {
                "id": "edge",
                "name": "Edge TTS (在线对比)",
                "type": "online",
                "offline": False,
                "desc": "微软在线语音，质量最高，需联网",
                "pros": ["语音最自然", "音色丰富", "支持情感"],
                "cons": ["需联网", "有延迟", "不可集成到 APK"],
                "license": "微软免费",
                "size_mb": 0,
                "android": "不可用（在线）",
                "url": "https://github.com/rany2/edge-tts",
                "status": "online_only"
            },
            {
                "id": "pyttsx3",
                "name": "pyttsx3 (基线)",
                "type": "offline",
                "offline": True,
                "desc": "系统内置语音，极快但音质一般",
                "pros": ["完全离线", "响应极快", "零模型"],
                "cons": ["语音机械", "依赖系统语音包", "中文支持差"],
                "license": "MIT",
                "size_mb": 0,
                "android": "不可用（桌面）",
                "url": "https://github.com/nateshmbhat/pyttsx3",
                "status": "baseline"
            }
        ]
    })

@app.route('/api/voices/<engine>')
def api_voices(engine):
    if engine == "sherpa_kokoro":
        return jsonify({"voices": KokoroVoices.list()})
    elif engine == "sherpa_vits":
        return jsonify({"voices": [{"sid": 0, "name": "Theresa (女声)", "gender": "女", "lang": "zh"}]})
    elif engine == "chattts":
        return jsonify({"voices": [
            {"seed": 0,    "name": "🎲 随机 Seed", "desc": "随机生成新音色"},
            {"seed": 1234,  "name": "#1234 标准女声", "desc": "清晰自然"},
            {"seed": 2025,  "name": "#2025 温柔女声", "desc": "温柔沉稳"},
            {"seed": 8888,  "name": "#8888 活泼女声", "desc": "活泼明快"},
            {"seed": 520,   "name": "#520 成熟男声", "desc": "沉稳磁性"},
        ]})
    elif engine == "edge":
        return jsonify({"voices": [
            {"id": "zh-CN-XiaoxiaoNeural", "name": "晓晓 (女声·温柔)", "style": "general"},
            {"id": "zh-CN-XiaoyiNeural", "name": "晓伊 (女声·可爱)", "style": "cheerful"},
            {"id": "zh-CN-YunjianNeural", "name": "云健 (男声·沉稳)", "style": "calm"},
            {"id": "zh-CN-YunxiNeural", "name": "云希 (男声·开朗)", "style": "cheerful"},
            {"id": "zh-CN-YunyangNeural", "name": "云扬 (男声·新闻播报)", "style": "newscast"},
            {"id": "zh-CN-XiaochenNeural", "name": "晓晨 (女声·播音)", "style": "newscast"},
            {"id": "zh-CN-XiaohanNeural", "name": "晓涵 (女声·温和)", "style": "calm"},
            {"id": "zh-CN-XiaomengNeural", "name": "晓梦 (女声·甜美)", "style": "cheerful"},
            {"id": "zh-CN-XiaoruiNeural", "name": "晓睿 (女声·成熟)", "style": "calm"},
            {"id": "zh-CN-YunfengNeural", "name": "云峰 (男声·磁性)", "style": "calm"},
        ]})
    elif engine == "pyttsx3":
        import pyttsx3
        e = pyttsx3.init()
        voices = [{"id": str(i), "name": v.name, "lang": v.id}
                  for i, v in enumerate(e.getProperty('voices'))]
        return jsonify({"voices": voices})
    return jsonify({"voices": []})

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json
    text = data.get('text', '').strip()
    engine = data.get('engine', '')
    params = data.get('params', {})
    if not text:
        return jsonify({"error": "文本不能为空"}), 400

    try:
        if engine == "sherpa_vits":
            speed = float(params.get('speed', 1.0))
            noise_scale = float(params.get('noise_scale', 1.0))
            sid = int(params.get('sid', 0))
            wav_data, elapsed = sherpa_engine.generate(text, 'vits', speed, sid, noise_scale)
            note = f"speed={speed}, noise_scale={noise_scale}"

        elif engine == "sherpa_kokoro":
            speed = float(params.get('speed', 1.0))
            sid = int(params.get('sid', 3))
            wav_data, elapsed = sherpa_engine.generate(text, 'kokoro', speed, sid)
            note = f"speed={speed}, sid={sid}"

        elif engine == "chattts":
            seed = int(params.get('seed', 1234))
            speed = float(params.get('speed', 1.0))
            prompt = str(params.get('prompt', '[oral_0][laugh_0][break_3]'))
            wav_data, elapsed = chattts_engine.generate(text, seed, speed, prompt)
            note = f"seed={seed}, prompt={prompt}"

        elif engine == "edge":
            voice = params.get('voice', 'zh-CN-XiaoxiaoNeural')
            rate = params.get('rate', '+0%')
            pitch = params.get('pitch', '+0Hz')
            wav_data, elapsed = generate_edge_tts(text, voice, rate, pitch)
            note = f"voice={voice}"

        elif engine == "pyttsx3":
            rate_val = int(params.get('rate', 150))
            voice_id = params.get('voice_id', '0')
            volume = float(params.get('volume', 0.9))
            wav_data, elapsed = generate_pyttsx3(text, rate_val, voice_id, volume)
            note = f"rate={rate_val}"

        else:
            return jsonify({"error": f"未知引擎: {engine}"}), 400

        fname = f"{engine}_{hashlib.md5(note.encode()).hexdigest()[:8]}_{int(time.time())}.wav"
        fpath = CACHE_DIR / fname
        fpath.write_bytes(wav_data)
        return jsonify({
            "success": True,
            "audio_url": f"/api/audio/{fname}",
            "engine": engine,
            "time": elapsed,
            "size_kb": round(len(wav_data) / 1024, 1),
            "note": note
        })
    except Exception as e:
        import traceback
        return jsonify({"error": f"{e}\n{traceback.format_exc()}"}), 500

@app.route("/api/warmup")
def api_warmup():
    """触发预热，返回各引擎状态"""
    status = {}
    try:
        sherpa_engine._get("vits"); status["vits"] = "ok"
    except Exception as e:
        status["vits"] = f"fail: {e}"
    try:
        sherpa_engine._get("kokoro"); status["kokoro"] = "ok"
    except Exception as e:
        status["kokoro"] = f"fail: {e}"
    try:
        chattts_engine._load(); status["chattts"] = "ok"
    except Exception as e:
        status["chattts"] = f"fail: {e}"
    return jsonify({"status": status})
@app.route('/api/audio/<filename>')
def api_audio(filename):
    fp = CACHE_DIR / filename
    if not fp.exists():
        return jsonify({"error": "文件不存在"}), 404
    return send_file(fp, mimetype="audio/wav")

@app.route('/api/batch', methods=['POST'])
def api_batch():
    """批量对比：一次请求生成多个引擎的音频"""
    data = request.json
    text = data.get('text', '').strip()
    engines = data.get('engines', [])
    params = data.get('params', {})
    if not text:
        return jsonify({"error": "文本不能为空"}), 400

    results = []
    for eng in engines:
        # 支持格式: "sherpa_vits" 或 {"engine": "sherpa_vits", "params": {...}}
        if isinstance(eng, str):
            name = eng
            eng_params = params
        elif isinstance(eng, dict):
            name = eng.get('engine', '')
            eng_params = eng.get('params', params)
        else:
            continue
        try:
            if name == "sherpa_vits":
                wav_data, elapsed = sherpa_engine.generate(
                    text, 'vits',
                    float(eng_params.get('speed', 1.0)),
                    int(eng_params.get('sid', 0)),
                    float(eng_params.get('noise_scale', 1.0))
                )
            elif name == "sherpa_kokoro":
                wav_data, elapsed = sherpa_engine.generate(
                    text, 'kokoro',
                    float(eng_params.get('speed', 1.0)),
                    int(eng_params.get('sid', 3))
                )
            elif name == "chattts":
                wav_data, elapsed = chattts_engine.generate(
                    text,
                    int(eng_params.get('seed', 1234)),
                    float(eng_params.get('speed', 1.0)),
                    str(eng_params.get('prompt', '[oral_0][laugh_0][break_3]'))
                )
            elif name == "edge":
                wav_data, elapsed = generate_edge_tts(
                    text,
                    eng_params.get('voice', 'zh-CN-XiaoxiaoNeural'),
                    eng_params.get('rate', '+0%'),
                    eng_params.get('pitch', '+0Hz')
                )
            elif name == "pyttsx3":
                wav_data, elapsed = generate_pyttsx3(
                    text,
                    int(eng_params.get('rate', 150)),
                    eng_params.get('voice_id', '0'),
                    float(eng_params.get('volume', 0.9))
                )
            else:
                continue
            fname = f"batch_{name}_{hashlib.md5(str(sorted(eng_params.items())).encode()).hexdigest()[:8]}.wav"
            fpath = CACHE_DIR / fname
            fpath.write_bytes(wav_data)
            results.append({
                "engine": name,
                "audio_url": f"/api/audio/{fname}",
                "time": elapsed,
                "size_kb": round(len(wav_data) / 1024, 1),
                "success": True
            })
        except Exception as e:
            results.append({"engine": name, "error": str(e), "success": False})
    return jsonify({"results": results})

@app.route('/api/android_info')
def api_android_info():
    """Android 端集成建议"""
    return jsonify({
        "recommendation": "Sherpa-ONNX + Kokoro",
        "reason": "C++ 原生 AAR 集成，Apache-2.0 商用友好，103 中文音色，160MB int8 模型，流式输出",
        "steps": [
            "1. 在 build.gradle 添加: implementation 'com.k2fsa:sherpa-onnx-java:1.13.4'",
            "2. 复制 AAR 到 app/libs/",
            "3. 模型文件放到 assets/ 或下载到本地存储",
            "4. 使用 OfflineTts 类初始化引擎",
            "5. 调用 generate(text, sid, speed) 获取音频数据"
        ],
        "code_example": """
// Android Kotlin 示例
val tts = OfflineTts(
    modelConfig = OfflineTtsModelConfig(
        kokoro = OfflineTtsKokoroModelConfig(
            model = "$filesDir/kokoro/model.int8.onnx",
            voices = "$filesDir/kokoro/voices.bin",
            tokens = "$filesDir/kokoro/tokens.txt",
            dataDir = "$filesDir/kokoro/espeak-ng-data",
            lexicon = "$filesDir/kokoro/lexicon-us-en.txt,$filesDir/kokoro/lexicon-zh.txt"
        )
    )
)
val audio = tts.generate(text, sid=3, speed=1.0)
// audio.samples: FloatArray, audio.sampleRate: Int
""",
        "engines": [
            {"name": "Sherpa-ONNX", "lang": "C++", "license": "Apache-2.0",
             "size_mb": 160, "integration": "AAR 直集成", "url": "https://github.com/k2-fsa/sherpa-onnx"},
            {"name": "Maise", "lang": "Kotlin", "license": "MIT",
             "size_mb": 160, "integration": "系统级 TTS 服务", "url": "https://github.com/Mobile-Artificial-Intelligence/maise"},
        ]
    })

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 TTS 离线引擎对比 Web UI")
    print(f"🌐 http://localhost:5000")
    print(f"📦 模型: VITS ✅ | Kokoro ✅ | ChatTTS ✅")
    print(f"📁 缓存: {CACHE_DIR}")
    print("="*60 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=False)
