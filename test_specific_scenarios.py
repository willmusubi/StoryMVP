#!/usr/bin/env python3
"""
特定场景测试脚本

测试内容：
1. move 能更新地点
2. give_item 在不拥有时会被拒绝，并返回 reason
3. dead 角色不能被 talk/rescue
"""

import json
import sys
from pathlib import Path

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️  requests 模块未安装，无法运行 API 测试")
    print("   请运行: pip install requests")
    sys.exit(1)

# 状态文件路径
STATE_FILE = Path(__file__).parent / "data" / "state.json"

def load_state() -> dict:
    """读取状态"""
    if not STATE_FILE.exists():
        return {}
    with open(STATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_state(state: dict) -> None:
    """保存状态"""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temp_file = STATE_FILE.with_suffix(".tmp")
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        temp_file.replace(STATE_FILE)
    except Exception as e:
        if temp_file.exists():
            temp_file.unlink()
        raise e

def print_test(name: str):
    """打印测试标题"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"{'='*60}")

def print_result(success: bool, message: str):
    """打印测试结果"""
    status = "✅ 通过" if success else "❌ 失败"
    print(f"{status}: {message}")

def test_1_move_updates_location():
    """
    测试 1: move 能更新地点
    """
    print_test("测试 1: move 能更新地点")
    
    try:
        # 准备测试状态
        test_state = {
            "time": 0,
            "characters": {
                "player": {
                    "alive": True,
                    "location": "xu_zhou",
                    "affinity_to_player": 100
                }
            },
            "items": {}
        }
        save_state(test_state)
        print("已准备测试状态：player 在 xu_zhou")
        
        # 执行 move 动作
        move_action = {
            "type": "move",
            "actor": "player",
            "to_location": "luo_yang",
            "intent": "前往洛阳"
        }
        
        print(f"\n执行 move 动作: {json.dumps(move_action, ensure_ascii=False)}")
        
        response = requests.post(
            "http://localhost:8000/act",
            json=move_action,
            timeout=5
        )
        
        if response.status_code != 200:
            print_result(False, f"API 返回状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        data = response.json()
        
        if not data.get("ok"):
            print_result(False, f"动作被拒绝: {data.get('error')}")
            return False
        
        # 验证结果
        new_state = data.get("state", {})
        player = new_state.get("characters", {}).get("player", {})
        new_location = player.get("location")
        new_time = new_state.get("time", 0)
        
        print(f"\n结果检查:")
        print(f"  新位置: {new_location}")
        print(f"  新时间: {new_time}")
        
        if new_location == "luo_yang" and new_time == 1:
            print_result(True, f"move 成功：位置从 xu_zhou 更新为 {new_location}")
            return True
        else:
            print_result(False, f"位置更新失败：期望 luo_yang，实际 {new_location}")
            return False
        
    except requests.exceptions.ConnectionError:
        print_result(False, "无法连接到服务，请先启动: uvicorn main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_2_give_item_rejects_when_not_owned():
    """
    测试 2: give_item 在不拥有时会被拒绝，并返回 reason
    """
    print_test("测试 2: give_item 在不拥有时会被拒绝，并返回 reason")
    
    try:
        # 准备测试状态：物品属于 liu_bei，player 尝试给
        test_state = {
            "time": 0,
            "characters": {
                "player": {
                    "alive": True,
                    "location": "xu_zhou",
                    "affinity_to_player": 100
                },
                "liu_bei": {
                    "alive": True,
                    "location": "xu_zhou",
                    "affinity_to_player": 50
                },
                "guan_yu": {
                    "alive": True,
                    "location": "xu_zhou",
                    "affinity_to_player": 60
                }
            },
            "items": {
                "sword_1": {
                    "owner": "liu_bei"  # 物品属于 liu_bei，不属于 player
                }
            }
        }
        save_state(test_state)
        print("已准备测试状态：sword_1 属于 liu_bei")
        
        # 尝试执行 give_item（player 不拥有该物品）
        give_action = {
            "type": "give_item",
            "actor": "player",
            "target": "guan_yu",
            "item": "sword_1",
            "intent": "把剑给你"
        }
        
        print(f"\n执行 give_item 动作: {json.dumps(give_action, ensure_ascii=False)}")
        print("预期：应该被拒绝，因为 player 不拥有 sword_1")
        
        response = requests.post(
            "http://localhost:8000/act",
            json=give_action,
            timeout=5
        )
        
        if response.status_code != 200:
            print_result(False, f"API 返回状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        data = response.json()
        
        # 验证被拒绝
        if data.get("ok"):
            print_result(False, "动作应该被拒绝，但却通过了")
            return False
        
        # 验证返回了 reason/error
        error = data.get("error") or data.get("reason")
        if not error:
            print_result(False, "动作被拒绝，但没有返回 reason/error")
            print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return False
        
        print(f"\n结果检查:")
        print(f"  动作被拒绝: ✅")
        print(f"  错误信息: {error}")
        
        # 验证错误信息包含所有权相关内容
        if "不属于" in error or "owner" in error.lower() or "拥有者" in error:
            print_result(True, f"正确拒绝并返回原因: {error}")
            return True
        else:
            print_result(False, f"错误信息不明确: {error}")
            return False
        
    except requests.exceptions.ConnectionError:
        print_result(False, "无法连接到服务，请先启动: uvicorn main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3_dead_character_cannot_be_talked_or_rescued():
    """
    测试 3: dead 角色不能被 talk/rescue
    """
    print_test("测试 3: dead 角色不能被 talk/rescue")
    
    try:
        # 准备测试状态：包含死亡角色
        test_state = {
            "time": 0,
            "characters": {
                "player": {
                    "alive": True,
                    "location": "xu_zhou",
                    "affinity_to_player": 100
                },
                "dead_char": {
                    "alive": False,  # 死亡角色
                    "location": "grave",
                    "affinity_to_player": 0
                }
            },
            "items": {}
        }
        save_state(test_state)
        print("已准备测试状态：dead_char 已死亡 (alive=false)")
        
        results = []
        
        # 测试 3.1: talk 死亡角色
        print("\n--- 测试 3.1: talk 死亡角色 ---")
        talk_action = {
            "type": "talk",
            "target": "dead_char",
            "intent": "说话"
        }
        
        print(f"执行 talk 动作: {json.dumps(talk_action, ensure_ascii=False)}")
        print("预期：应该被拒绝，因为目标已死亡")
        
        response = requests.post(
            "http://localhost:8000/act",
            json=talk_action,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("ok"):
                error = data.get("error") or data.get("reason")
                if error and ("死亡" in error or "alive" in error.lower() or "dead" in error.lower()):
                    print(f"  ✅ talk 被正确拒绝: {error}")
                    results.append(True)
                else:
                    print(f"  ❌ talk 被拒绝但原因不明确: {error}")
                    results.append(False)
            else:
                print("  ❌ talk 应该被拒绝，但却通过了")
                results.append(False)
        else:
            print(f"  ❌ API 返回状态码: {response.status_code}")
            results.append(False)
        
        # 测试 3.2: rescue 死亡角色
        print("\n--- 测试 3.2: rescue 死亡角色 ---")
        rescue_action = {
            "type": "rescue",
            "target": "dead_char",
            "intent": "救援"
        }
        
        print(f"执行 rescue 动作: {json.dumps(rescue_action, ensure_ascii=False)}")
        print("预期：应该被拒绝，因为目标已死亡")
        
        response = requests.post(
            "http://localhost:8000/act",
            json=rescue_action,
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if not data.get("ok"):
                error = data.get("error") or data.get("reason")
                if error and ("死亡" in error or "alive" in error.lower() or "dead" in error.lower()):
                    print(f"  ✅ rescue 被正确拒绝: {error}")
                    results.append(True)
                else:
                    print(f"  ❌ rescue 被拒绝但原因不明确: {error}")
                    results.append(False)
            else:
                print("  ❌ rescue 应该被拒绝，但却通过了")
                results.append(False)
        else:
            print(f"  ❌ API 返回状态码: {response.status_code}")
            results.append(False)
        
        # 汇总结果
        all_passed = all(results)
        if all_passed:
            print_result(True, "所有死亡角色交互测试通过")
        else:
            print_result(False, f"部分测试失败: {results}")
        
        return all_passed
        
    except requests.exceptions.ConnectionError:
        print_result(False, "无法连接到服务，请先启动: uvicorn main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """运行所有测试"""
    print("\n" + "="*60)
    print("特定场景测试")
    print("="*60)
    print("\n⚠️  请确保服务正在运行: uvicorn main:app --reload")
    
    results = []
    
    # 运行测试
    results.append(("测试 1: move 能更新地点", test_1_move_updates_location()))
    results.append(("测试 2: give_item 不拥有时被拒绝", test_2_give_item_rejects_when_not_owned()))
    results.append(("测试 3: dead 角色不能被 talk/rescue", test_3_dead_character_cannot_be_talked_or_rescued()))
    
    # 汇总结果
    print("\n" + "="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {name}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败")
        return 1

if __name__ == "__main__":
    sys.exit(main())

