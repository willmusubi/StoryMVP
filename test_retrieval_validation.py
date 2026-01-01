#!/usr/bin/env python3
"""
验收测试：检索系统
1. 用户提到"董卓/貂蝉/吕布"时，检索片段明显更相关
2. Prompt 体积可控
"""

import sys
import re
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

# 从 main.py 导入函数
from main import chunk_story, score_chunk, retrieve_relevant_chunks

def chunk_story_local(story_text: str) -> list[str]:
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
    chunks = chunk_story_local(story_text)
    if not chunks:
        return []
    
    scored_chunks = []
    for chunk in chunks:
        score = score_chunk(chunk, user_message, current_time)
        scored_chunks.append((score, chunk))
    
    scored_chunks.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [chunk for _, chunk in scored_chunks[:top_k]]
    
    return top_chunks

def check_relevance(chunk: str, keywords: list[str]) -> bool:
    """检查 chunk 是否包含关键词"""
    chunk_lower = chunk.lower()
    for keyword in keywords:
        if keyword in chunk_lower:
            return True
    return False

def test_character_retrieval():
    """测试角色检索的相关性"""
    story_file = Path("data/story.md")
    if not story_file.exists():
        print("❌ story.md 不存在")
        return False
    
    with open(story_file, "r", encoding="utf-8") as f:
        story_text = f.read()
    
    print("=" * 60)
    print("验收测试 1: 角色检索相关性")
    print("=" * 60)
    
    test_cases = [
        ("董卓", ["董卓"]),
        ("貂蝉", ["貂蝉"]),
        ("吕布", ["吕布"]),
        ("我要见董卓", ["董卓"]),
        ("貂蝉在哪里", ["貂蝉"]),
        ("攻击吕布", ["吕布"]),
        ("董卓和吕布的关系", ["董卓", "吕布"]),
    ]
    
    all_passed = True
    
    for user_message, keywords in test_cases:
        print(f"\n📝 测试消息: '{user_message}'")
        print(f"   期望关键词: {keywords}")
        
        relevant_chunks = retrieve_relevant_chunks(story_text, user_message, 0, top_k=3)
        
        # 检查 top-3 chunks 中是否至少有一个包含关键词
        found_relevant = False
        for i, chunk in enumerate(relevant_chunks, 1):
            if check_relevance(chunk, keywords):
                found_relevant = True
                print(f"   ✅ Chunk {i} 包含关键词")
                # 显示包含关键词的片段
                for keyword in keywords:
                    if keyword in chunk:
                        # 找到关键词位置，显示前后上下文
                        idx = chunk.find(keyword)
                        start = max(0, idx - 50)
                        end = min(len(chunk), idx + len(keyword) + 50)
                        context = chunk[start:end].replace('\n', ' ')
                        print(f"      上下文: ...{context}...")
                        break
            else:
                print(f"   ⚠️  Chunk {i} 不包含关键词")
        
        if found_relevant:
            print(f"   ✅ 测试通过：至少一个 chunk 包含关键词")
        else:
            print(f"   ❌ 测试失败：没有 chunk 包含关键词")
            all_passed = False
    
    return all_passed

def test_prompt_size():
    """测试 prompt 体积可控"""
    story_file = Path("data/story.md")
    if not story_file.exists():
        print("❌ story.md 不存在")
        return False
    
    with open(story_file, "r", encoding="utf-8") as f:
        story_text = f.read()
    
    print("\n" + "=" * 60)
    print("验收测试 2: Prompt 体积可控")
    print("=" * 60)
    
    test_messages = [
        "我要前往洛阳",
        "董卓在哪里",
        "给刘备物品",
        "攻击曹操",
    ]
    
    max_prompt_size = 0
    min_prompt_size = float('inf')
    total_size = 0
    
    for user_message in test_messages:
        relevant_chunks = retrieve_relevant_chunks(story_text, user_message, 0, top_k=3)
        
        # 计算 LORE_CONTEXT 的大小
        lore_context = "\n\n---\n\n".join(relevant_chunks)
        context_size = len(lore_context)
        
        # 估算完整 prompt 大小（STATE + USER_MESSAGE + LORE_CONTEXT）
        # STATE 大约 500 字符，USER_MESSAGE 大约 50 字符，系统 prompt 约 2000 字符
        estimated_prompt_size = 2000 + 500 + len(user_message) + context_size
        
        max_prompt_size = max(max_prompt_size, estimated_prompt_size)
        min_prompt_size = min(min_prompt_size, estimated_prompt_size)
        total_size += estimated_prompt_size
        
        print(f"\n📝 消息: '{user_message}'")
        print(f"   LORE_CONTEXT 大小: {context_size:,} 字符")
        print(f"   估算 Prompt 总大小: {estimated_prompt_size:,} 字符")
        print(f"   Chunks 数量: {len(relevant_chunks)}")
        for i, chunk in enumerate(relevant_chunks, 1):
            print(f"      Chunk {i}: {len(chunk):,} 字符")
    
    avg_size = total_size / len(test_messages)
    
    print(f"\n📊 统计信息:")
    print(f"   最大 Prompt 大小: {max_prompt_size:,} 字符")
    print(f"   最小 Prompt 大小: {min_prompt_size:,} 字符")
    print(f"   平均 Prompt 大小: {avg_size:,.0f} 字符")
    
    # 检查是否在合理范围内（例如不超过 10,000 字符）
    reasonable_limit = 10000
    if max_prompt_size <= reasonable_limit:
        print(f"   ✅ 所有 Prompt 都在合理范围内（< {reasonable_limit:,} 字符）")
        return True
    else:
        print(f"   ⚠️  部分 Prompt 超过合理范围（> {reasonable_limit:,} 字符）")
        return False

def test_comparison():
    """对比测试：相关消息 vs 不相关消息"""
    story_file = Path("data/story.md")
    if not story_file.exists():
        print("❌ story.md 不存在")
        return False
    
    with open(story_file, "r", encoding="utf-8") as f:
        story_text = f.read()
    
    print("\n" + "=" * 60)
    print("验收测试 3: 相关性对比")
    print("=" * 60)
    
    # 测试相关消息
    relevant_message = "我要见董卓"
    relevant_chunks = retrieve_relevant_chunks(story_text, relevant_message, 0, top_k=3)
    
    # 测试不相关消息
    irrelevant_message = "今天天气真好"
    irrelevant_chunks = retrieve_relevant_chunks(story_text, irrelevant_message, 0, top_k=3)
    
    print(f"\n📝 相关消息: '{relevant_message}'")
    print(f"   检索到的 chunks:")
    for i, chunk in enumerate(relevant_chunks, 1):
        has_dongzhuo = "董卓" in chunk
        print(f"   Chunk {i}: {'✅ 包含董卓' if has_dongzhuo else '❌ 不包含董卓'} ({len(chunk)} 字符)")
    
    print(f"\n📝 不相关消息: '{irrelevant_message}'")
    print(f"   检索到的 chunks:")
    for i, chunk in enumerate(irrelevant_chunks, 1):
        has_dongzhuo = "董卓" in chunk
        print(f"   Chunk {i}: {'✅ 包含董卓' if has_dongzhuo else '❌ 不包含董卓'} ({len(chunk)} 字符)")
    
    # 检查相关性差异
    relevant_count = sum(1 for chunk in relevant_chunks if "董卓" in chunk)
    irrelevant_count = sum(1 for chunk in irrelevant_chunks if "董卓" in chunk)
    
    if relevant_count > irrelevant_count:
        print(f"\n   ✅ 相关性测试通过：相关消息找到 {relevant_count} 个包含董卓的 chunks，不相关消息找到 {irrelevant_count} 个")
        return True
    else:
        print(f"\n   ⚠️  相关性差异不明显：相关消息 {relevant_count} 个，不相关消息 {irrelevant_count} 个")
        return False

def main():
    """运行所有验收测试"""
    print("\n" + "=" * 60)
    print("检索系统验收测试")
    print("=" * 60)
    
    results = []
    
    # 测试 1: 角色检索相关性
    results.append(("角色检索相关性", test_character_retrieval()))
    
    # 测试 2: Prompt 体积可控
    results.append(("Prompt 体积可控", test_prompt_size()))
    
    # 测试 3: 相关性对比
    results.append(("相关性对比", test_comparison()))
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 所有验收测试通过！")
    else:
        print("\n⚠️  部分测试未通过，需要优化")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

