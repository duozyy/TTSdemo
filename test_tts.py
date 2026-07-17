#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTS 引擎对比测试 - 健康报告播报场景
测试文本：模拟 AI 健康报告播报内容
"""

import os
import time
import asyncio
import edge_tts
import pyttsx3
import numpy as np
import wave
import json
from pathlib import Path

# 测试文本 - 模拟健康报告播报
TEST_TEXTS = {
    "简短问候": "您好，您的健康报告已生成，请查收。",
    "报告摘要": "根据您最近三十天的健康数据分析，您的平均心率为七十八次每分钟，血压稳定在一百二十到八十毫米汞柱之间，睡眠质量良好，平均每晚深睡时长达到一小时四十二分钟。",
    "详细播报": "综合评估显示，您的心血管健康指数为优秀，建议保持当前每周三次的有氧运动习惯。需要注意的是，您近期的压力指数略有上升，建议适当增加休息时间，并关注心理健康。如有异常症状，请及时就医咨询。"
}

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

def test_edge_tts():
    """测试 Edge TTS（在线，作为质量基准）"""
    print("\n" + "="*60)
    print("🎯 测试 Edge TTS（在线基准）")
    print("="*60)
    
    results = []
    for name, text in TEST_TEXTS.items():
        output_file = OUTPUT_DIR / f"edge_tts_{name}.mp3"
        start = time.time()
        
        async def generate():
            communicate = edge_tts.Communicate(
                text=text,
                voice="zh-CN-XiaoxiaoNeural",
                rate="+10%",
                volume="+0%",
                pitch="+0Hz"
            )
            await communicate.save(str(output_file))
        
        asyncio.run(generate())
        elapsed = time.time() - start
        
        file_size = output_file.stat().st_size / 1024
        print(f"  ✅ {name}: {elapsed:.2f}s, {file_size:.1f}KB")
        results.append({
            "engine": "Edge TTS",
            "text": name,
            "time": elapsed,
            "size": file_size
        })
    
    return results

def test_pyttsx3():
    """测试 pyttsx3（离线，作为速度基准）"""
    print("\n" + "="*60)
    print("🎯 测试 pyttsx3（离线基准）")
    print("="*60)
    
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    
    # 尝试找到中文语音
    chinese_voice = None
    for voice in voices:
        if 'chinese' in voice.name.lower() or 'zh' in voice.id.lower():
            chinese_voice = voice
            break
    
    if chinese_voice:
        engine.setProperty('voice', chinese_voice.id)
        print(f"  使用语音: {chinese_voice.name}")
    else:
        print(f"  ⚠️ 未找到中文语音，使用默认语音")
        print(f"  可用语音: {[v.name for v in voices[:5]]}...")
    
    engine.setProperty('rate', 150)
    engine.setProperty('volume', 0.9)
    
    results = []
    for name, text in TEST_TEXTS.items():
        output_file = OUTPUT_DIR / f"pyttsx3_{name}.wav"
        start = time.time()
        
        engine.save_to_file(text, str(output_file))
        engine.runAndWait()
        
        elapsed = time.time() - start
        
        if output_file.exists():
            file_size = output_file.stat().st_size / 1024
        else:
            file_size = 0
        
        print(f"  ✅ {name}: {elapsed:.2f}s, {file_size:.1f}KB")
        results.append({
            "engine": "pyttsx3",
            "text": name,
            "time": elapsed,
            "size": file_size
        })
    
    return results

def test_sherpa_onnx():
    """测试 Sherpa-ONNX（离线，重点测试）"""
    print("\n" + "="*60)
    print("🎯 测试 Sherpa-ONNX（离线重点）")
    print("="*60)
    
    try:
        import sherpa_onnx
        print("  ✅ sherpa-onnx 已安装")
    except ImportError:
        print("  ❌ sherpa-onnx 未安装")
        return []
    
    # 检查模型文件
    model_dir = Path(__file__).parent / "models"
    if not model_dir.exists():
        print(f"  ⚠️ 模型目录不存在: {model_dir}")
        print("  请先下载模型文件")
        return []
    
    # 查找可用模型
    models = list(model_dir.glob("*.onnx"))
    if not models:
        print(f"  ⚠️ 未找到 ONNX 模型文件")
        return []
    
    print(f"  找到 {len(models)} 个模型文件")
    
    results = []
    # TODO: 实现具体模型加载和推理
    # 需要先下载模型
    
    return results

def main():
    print("🚀 TTS 引擎对比测试开始")
    print(f"📁 输出目录: {OUTPUT_DIR}")
    
    all_results = []
    
    # 测试 Edge TTS
    try:
        all_results.extend(test_edge_tts())
    except Exception as e:
        print(f"  ❌ Edge TTS 测试失败: {e}")
    
    # 测试 pyttsx3
    try:
        all_results.extend(test_pyttsx3())
    except Exception as e:
        print(f"  ❌ pyttsx3 测试失败: {e}")
    
    # 测试 Sherpa-ONNX
    try:
        all_results.extend(test_sherpa_onnx())
    except Exception as e:
        print(f"  ❌ Sherpa-ONNX 测试失败: {e}")
    
    # 输出汇总
    print("\n" + "="*60)
    print("📊 测试结果汇总")
    print("="*60)
    
    if all_results:
        print(f"{'引擎':<15} {'文本':<12} {'耗时(s)':<10} {'大小(KB)':<10}")
        print("-" * 50)
        for r in all_results:
            print(f"{r['engine']:<15} {r['text']:<12} {r['time']:<10.2f} {r['size']:<10.1f}")
    
    print("\n✅ 测试完成！")
    print(f"📁 音频文件保存在: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
