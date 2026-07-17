import urllib.request
import os
import tarfile
import shutil
from pathlib import Path

# 下载配置
BASE_DIR = Path("E:/workbuddy/2026-07-15-21-40-09/tts_demo/models/kokoro")
BASE_DIR.mkdir(parents=True, exist_ok=True)

# Kokoro int8 量化版 (推荐安卓用，体积小)
URL_INT8 = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-int8-multi-lang-v1_1.tar.bz2"
# Kokoro 全精度版 (质量更高)
URL_FP32 = "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/kokoro-multi-lang-v1_1.tar.bz2"

def download_with_progress(url, dest):
    """带进度显示的下载"""
    filename = url.split('/')[-1]
    dest_path = dest / filename
    
    def progress_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        percent = min(downloaded * 100 / total_size, 100)
        mb = downloaded / 1024 / 1024
        total_mb = total_size / 1024 / 1024
        print(f"\r  {filename}: {percent:.1f}% ({mb:.1f}/{total_mb:.1f} MB)", end="", flush=True)
    
    print(f"开始下载: {filename}")
    print(f"  URL: {url}")
    print(f"  目标: {dest_path}")
    
    urllib.request.urlretrieve(url, str(dest_path), reporthook=progress_hook)
    print(f"\n  完成! 文件大小: {dest_path.stat().st_size / 1024 / 1024:.1f} MB")
    return dest_path

def extract_tar_bz2(archive_path, dest_dir):
    """解压 tar.bz2"""
    print(f"解压中: {archive_path.name}")
    with tarfile.open(archive_path, "r:bz2") as tar:
        tar.extractall(path=str(dest_dir))
    print(f"  解压完成!")
    
    # 删除压缩包
    archive_path.unlink()
    print(f"  已删除压缩包: {archive_path.name}")

def main():
    print("=" * 60)
    print("Kokoro-82M 多语言模型下载器")
    print("支持: 中文 + 英文, 103 个音色")
    print("=" * 60)
    
    # 选择版本
    print("\n选择下载版本:")
    print("  1. int8 量化版 (~88MB) - 推荐安卓/移动设备")
    print("  2. 全精度版 (~310MB) - 质量最高")
    print("  3. 两个都下")
    
    choice = input("\n输入选择 (1/2/3): ").strip() or "1"
    
    if choice in ("1", "3"):
        print("\n--- 下载 int8 量化版 ---")
        archive = download_with_progress(URL_INT8, BASE_DIR)
        extract_tar_bz2(archive, BASE_DIR)
    
    if choice in ("2", "3"):
        print("\n--- 下载全精度版 ---")
        archive = download_with_progress(URL_FP32, BASE_DIR)
        extract_tar_bz2(archive, BASE_DIR)
    
    # 列出下载的文件
    print("\n" + "=" * 60)
    print("下载完成! 文件列表:")
    print("=" * 60)
    for item in sorted(BASE_DIR.rglob("*")):
        if item.is_file():
            rel = item.relative_to(BASE_DIR)
            size_mb = item.stat().st_size / 1024 / 1024
            print(f"  {rel} ({size_mb:.1f} MB)")

if __name__ == "__main__":
    main()
