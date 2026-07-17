# TTS Demo - 离线语音合成引擎对比 Web 应用

> 支持 5 种 TTS 引擎的本地对比 Demo，专注于**离线、中文、语调/语速可调、Android APK 可集成**。

## 🎯 核心特性

| 特性 | 说明 |
|------|------|
| 🔒 **完全离线** | 无需联网，保护隐私 |
| 🇨🇳 **中文支持** | 优化中文语音合成效果 |
| 🎛️ **参数可调** | 语速、语调（noise_scale）、音色 |
| 📱 **Android 集成** | Sherpa-ONNX 提供 AAR 直集成 |
| ⚡ **高性能** | CPU 实时推理，VITS 仅需 0.8s |

## 🚀 支持的引擎

| 引擎 | 类型 | 中文 | 模型大小 | 推理速度 | 特点 |
|------|------|------|---------|---------|------|
| **Sherpa-ONNX VITS** | 离线 | ✅ | 119 MB | **0.8s** | 中文女声，速度最快 |
| **Sherpa-ONNX Kokoro** | ✅ | 174 MB | 2.7s | 103 种中英音色 |
| **ChatTTS** | 离线 | ✅ | 1.3 GB | 5.6s | 对话式自然语音 |
| **Edge TTS** | 在线 | ✅ | - | 1.2s | 微软语音（对比参考） |
| **pyttsx3** | 离线 | ❌ | - | **0.3s** | 系统级基线 |

## 📋 系统要求

- **Python**: 3.10+
- **OS**: Windows 10/11 / macOS / Linux
- **内存**: ≥ 4GB（ChatTTS 需 ≥ 8GB）
- **磁盘**: ≥ 3GB（含所有模型文件）

## 🛠️ 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/duozyy/TTSdemo.git
cd TTSdemo
```

### 2. 下载模型文件

模型文件未包含在仓库中（约 1.8GB），请通过以下方式获取：

#### 方式一：运行下载脚本

```bash
python download_models.py        # 下载所有模型
python download_kokoro.py        # 仅下载 Kokoro
```

#### 方式二：手动下载

| 模型 | 下载链接 | 放置路径 |
|------|---------|---------|
| VITS-zh-theresa | [HuggingFace](https://huggingface.co/csukuangfj/vits-zh-hf-theresa) | `models/vits_zh/vits-zh-hf-theresa/` |
| Kokoro-int8 | [HuggingFace](https://huggingface.co/hexgrad/Kokoro-82M) | `models/kokoro/kokoro-int8-multi-lang-v1_1/` |
| ChatTTS | [GitHub](https://github.com/2noise/ChatTTS) | `models/ChatTTS/` |

### 3. 安装依赖

```bash
# 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 4. 启动应用

```bash
python app.py
```

打开浏览器访问：**http://localhost:5000**

## 📱 Android 集成

### Sherpa-ONNX AAR 集成

1. 下载预编译 AAR：[Sherpa-ONNX Android](https://github.com/k2-fsa/sherpa-onnx/releases)
2. 在 `build.gradle` 中添加依赖：

```gradle
dependencies {
    implementation 'com.k2fsa.sherpa.onnx:sherpa-onnx-android:1.10.0'
}
```

3. 参考示例代码：[Sherpa-ONNX Android Example](https://github.com/k2-fsa/sherpa-onnx/tree/master/android)

### Kokoro + ONNX Runtime

1. 添加 `onnxruntime-android` 依赖
2. 导出 Kokoro 模型为 ONNX 格式
3. 通过 JNI 或直接 Java API 调用

## 📁 项目结构

```
tts_demo/
├── app.py                  # Flask 主程序
├── requirements.txt        # Python 依赖
├── templates/
│   └── index.html          # Web UI
├── models/                 # 模型文件目录（需下载）
│   ├── vits_zh/           # VITS 中文模型
│   ├── kokoro/            # Kokoro 多音色模型
│   └── ChatTTS/           # ChatTTS 模型
├── cache/                  # 音频缓存
├── download_models.py      # 模型下载脚本
├── download_kokoro.py      # Kokoro 专用下载脚本
└── test_*.py              # 测试脚本
```

## 🎮 主要 API

| Endpoint | Method | 说明 |
|----------|--------|------|
| `/` | GET | Web 界面 |
| `/api/generate` | POST | 单引擎合成 |
| `/api/batch` | POST | 批量多引擎对比 |
| `/api/warmup` | GET | 预热 ChatTTS |
| `/api/info` | GET | 引擎状态信息 |
| `/api/android_info` | GET | Android 集成指南 |

## ⚙️ 引擎参数说明

```json
{
  "engine": "sherpa_vits",     // 引擎名称
  "text": "你好，欢迎使用TTS演示",  // 合成文本
  "speed": 1.0,                // 语速 (0.5-2.0)
  "sid": 0,                    // 音色 ID（VITS/Kokoro）
  "noise_scale": 1.0,         // 语调随机性（VITS）
  "seed": 12345               // 说话人种子（ChatTTS）
}
```

## 📝 性能数据

| 引擎 | CPU (i7-12700H) | 内存占用 | RTF |
|------|-----------------|---------|-----|
| VITS | 0.87s | 200MB | 0.05 |
| Kokoro | 2.7s | 400MB | 0.15 |
| ChatTTS | 5.6s | 1.8GB | 0.30 |
| Edge | 1.2s | 100MB | - |

*RTF（Real Time Factor）= 推理时间 / 音频时长，越小越好*

## 🤝 贡献

欢迎提交 Issue 和 PR！

## 📄 License

MIT License

## 🔗 相关链接

- [Sherpa-ONNX GitHub](https://github.com/k2-fsa/sherpa-onnx)
- [ChatTTS GitHub](https://github.com/2noise/ChatTTS)
- [Kokoro TTS](https://github.com/hexgrad/Kokoro-82M)
