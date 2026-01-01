#!/usr/bin/env python3
"""
测试检索功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 只导入检索相关的函数，避免触发 OpenAI 初始化
import re
from typing import Dict, Any

def chunk_story(story_text: str) -> list[str]:
    """将 story.md 按段落/空行切分成 chunks"""
    if not story_text:
        return []
    chunks = [chunk.strip() for chunk in story_text.split('\n\n') if chunk.strip()]
    return chunks

def score_chunk(chunk: str, user_message: str, current_time: int) -> float:
    """对 chunk 进行简单打分"""
    score = 0.0
    user_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', user_message.lower()))
    chunk_lower = chunk.lower()
    
    for word in user_words:
        if len(word) > 1:
            count = chunk_lower.count(word)
            score += count * (len(word) / 10.0)
    
    return score

def retrieve_relevant_chunks(story_text: str, user_message: str, current_time: int, top_k: int = 3) -> list[str]:
    """检索相关的 chunks"""
    chunks = chunk_story(story_text)
    if not chunks:
        return []
    
    scored_chunks = []
    for chunk in chunks:
        score = score_chunk(chunk, user_message, current_time)
        scored_chunks.append((score, chunk))
    
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]
    
    return top_chunks

def test_retrieval():
    """测试检索功能"""
    # 读取 story.md
    story_file = Path("data/story.md")
    if not story_file.exists():
        print("❌ story.md 不存在")
        return
    
    with open(story_file, "r", encoding="utf-8") as f:
        story_text = f.read()
    
    print(f"✅ 读取 story.md，共 {len(story_text)} 字符")
    
    # 测试 chunk 分割
    chunks = chunk_story(story_text)
    print(f"✅ 分割成 {len(chunks)} 个 chunks")
    
    # 测试检索
    test_cases = [
        ("我要前往洛阳", 0),
        ("张飞在哪里", 0),
        ("攻击曹操", 5),
        ("给刘备物品", 0),
    ]
    
    for user_message, current_time in test_cases:
        print(f"\n📝 测试: '{user_message}' (time={current_time})")
        relevant_chunks = retrieve_relevant_chunks(story_text, user_message, current_time, top_k=3)
        print(f"   检索到 {len(relevant_chunks)} 个相关 chunks")
        for i, chunk in enumerate(relevant_chunks, 1):
            preview = chunk[:100].replace('\n', ' ')
            print(f"   {i}. {preview}...")

if __name__ == "__main__":
    test_retrieval()

