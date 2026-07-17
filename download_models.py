#!/usr/bin/env python3
"""下载 Sherpa-ONNX TTS 模型"""
import os
import sys
import urllib.request
import zipfile
import tarfile
import shutil

MODELS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")

# 模型下载列表
MODELS = {
    "matcha_zh": {
        "name": "Matcha-TTS 中文 (Baker)",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/matcha-icefall-zh-baker.tar.bz2",
        "filename": "matcha-icefall-zh-baker.tar.bz2",
        "size": "~100MB",
        "description": "中文质量最佳，适合健康报告播报"
    },
    "vits_zh": {
        "name": "VITS 中文 (Huifengyu)",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-zh-hf-theresa.tar.bz2",
        "filename": "vits-zh-hf-theresa.tar.bz2",
        "size": "~50MB",
        "description": "响应快，模型小，适合低端设备"
    },
    "kokoro": {
        "name": "Kokoro-82M 多语言",
        "url": "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-en-zh-v0_19.tar.bz2",
        "filename": "kokoro-en-zh-v0_19.tar.bz2",
        "size": "~80MB",
        "description": "音质最佳，支持中英文混合"
    }
}

def download_file(url, dest_path, desc=""):
    """带进度条的下载"""
    print(f"  下载: {url}")
    print(f"  目标: {dest_path}")
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(downloaded * 100 / total_size, 100)
            mb = downloaded / 1024 / 1024
            total_mb = total_size / 1024 / 1024
            sys.stdout.write(f"\r  进度: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)")
            sys.stdout.flush()
    
    try:
        urllib.request.urlretrieve(url, dest_path, progress_hook)
        print()  # 换行
        return True
    except Exception as e:
        print(f"\n  下载失败: {e}")
        return False

def extract_archive(archive_path, dest_dir):
    """解压归档文件"""
    print(f"  解压: {archive_path}")
    try:
        if archive_path.endswith('.tar.bz2') or archive_path.endswith('.tar.gz'):
            with tarfile.open(archive_path, 'r:*') as tar:
                tar.extractall(dest_dir)
        elif archive_path.endswith('.zip'):
            with zipfile.ZipFile(archive_path, 'r') as z:
                z.extractall(dest_dir)
        print(f"  解压完成 -> {dest_dir}")
        return True
    except Exception as e:
        print(f"  解压失败: {e}")
        return False

def main():
    print("=" * 60)
    print("Sherpa-ONNX TTS 模型下载器")
    print("=" * 60)
    print()
    
    # 选择要下载的模型
    print("可用模型:")
    for key, info in MODELS.items():
        print(f"  [{key}] {info['name']} ({info['size']})")
        print(f"       {info['description']}")
    print()
    
    if len(sys.argv) > 1:
        selected = sys.argv[1].split(',')
    else:
        selected = list(MODELS.keys())
    
    print(f"将下载: {', '.join(selected)}")
    print()
    
    for model_key in selected:
        if model_key not in MODELS:
            print(f"未知模型: {model_key}")
            continue
        
        model_info = MODELS[model_key]
        model_dir = os.path.join(MODELS_DIR, model_key)
        archive_path = os.path.join(MODELS_DIR, model_info['filename'])
        
        print(f"--- {model_info['name']} ---")
        
        # 检查是否已存在
        if os.path.exists(model_dir) and os.listdir(model_dir):
            print(f"  模型目录已存在: {model_dir}")
            response = input("  是否重新下载? (y/N): ").strip().lower()
            if response != 'y':
                print("  跳过")
                print()
                continue
        
        # 下载
        os.makedirs(model_dir, exist_ok=True)
        
        if not os.path.exists(archive_path):
            success = download_file(model_info['url'], archive_path, model_info['name'])
            if not success:
                print(f"  跳过 {model_key}")
                print()
                continue
        else:
            print(f"  归档文件已存在: {archive_path}")
        
        # 解压
        extract_archive(archive_path, model_dir)
        
        # 清理归档文件
        try:
            os.remove(archive_path)
            print(f"  已清理归档文件")
        except:
            pass
        
        print()
    
    print("=" * 60)
    print("下载完成！模型目录:")
    for key in selected:
        model_dir = os.path.join(MODELS_DIR, key)
        if os.path.exists(model_dir):
            files = os.listdir(model_dir)
            print(f"  {key}: {len(files)} 个文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
