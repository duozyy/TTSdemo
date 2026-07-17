"""测试 ChatTTS 本地模型加载与合成"""
import os, sys, time
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, r"E:/workbuddy/2026-07-15-21-40-09/tts_demo_env/Lib/site-packages")
import ChatTTS

MODEL_PATH = r"E:/workbuddy/2026-07-15-21-40-09/tts_demo/models/ChatTTS"
OUTPUT_DIR = r"E:/workbuddy/2026-07-15-21-40-09/tts_demo/cache"
os.makedirs(OUTPUT_DIR, exist_ok=True)

print(f"[1/3] Loading ChatTTS...")
t0 = time.time()
chat = ChatTTS.Chat()
chat.load(source="custom", custom_path=MODEL_PATH, compile=False)
print(f"  Loaded in {time.time()-t0:.1f}s  has_loaded={chat.has_loaded()}")

print("[2/3] Generating...")
text = "你好，欢迎使用ChatTTS合成引擎，这是一个测试语音。"
t0 = time.time()
params_refine = chat.RefineTextParams(prompt="[oral_0][laugh_0][break_3]")
params_infer = chat.InferCodeParams(spk_emb=chat.sample_random_speaker())
wavs = chat.infer([text], use_decoder=True,
                  params_refine_text=params_refine,
                  params_infer_code=params_infer)
print(f"  Generated in {time.time()-t0:.1f}s  ({len(wavs)} segments)")

print("[3/3] Saving WAV...")
for i, wav in enumerate(wavs):
    audio_np = np.array(wav, dtype=np.float32)
    audio_int16 = np.clip(audio_np * 32767, -32768, 32767).astype(np.int16)
    out_path = os.path.join(OUTPUT_DIR, f"chattts_test_{i+1}.wav")
    wavfile.write(out_path, 24000, audio_int16)
    print(f"  {out_path}  ({len(audio_np)/24000:.1f}s)")
print("\nDone!")
