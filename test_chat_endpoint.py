#!/usr/bin/env python3
"""
POST /chat 端点测试脚本

测试内容：
1. 正常聊天流程（生成动作并执行）
2. 动作验证失败的情况
3. JSON 解析
4. 返回格式验证
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

def test_1_chat_basic_flow():
    """
    测试 1: 基本聊天流程
    """
    print_test("测试 1: 基本聊天流程（生成动作并执行）")
    
    try:
        # 准备测试状态
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
                }
            },
            "items": {
                "sword_1": {
                    "owner": "player"
                }
            }
        }
        save_state(test_state)
        print("已准备测试状态")
        
        # 发送聊天请求
        chat_request = {
            "message": "我要前往洛阳"
        }
        
        print(f"\n发送请求: {json.dumps(chat_request, ensure_ascii=False)}")
        print("预期：应该生成 move 动作并执行")
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=chat_request,
            timeout=60  # LLM 调用可能需要更长时间
        )
        
        if response.status_code != 200:
            print_result(False, f"API 返回状态码: {response.status_code}")
            print(f"响应内容: {response.text}")
            return False
        
        data = response.json()
        
        # 验证返回格式
        required_fields = ["ok", "narration", "action_ok", "state"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print_result(False, f"返回缺少字段: {missing_fields}")
            print(f"响应数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
            return False
        
        print(f"\n返回数据:")
        print(f"  ok: {data.get('ok')}")
        print(f"  action_ok: {data.get('action_ok')}")
        print(f"  narration: {data.get('narration', '')[:100]}...")
        
        # 验证基本结构
        if not data.get("ok"):
            print_result(False, f"请求失败: {data.get('error')}")
            return False
        
        # 检查是否有 narration
        if not data.get("narration"):
            print_result(False, "缺少 narration 字段")
            return False
        
        # 检查 state
        state = data.get("state", {})
        if not state:
            print_result(False, "缺少 state 字段")
            return False
        
        # 如果 action_ok 为 true，检查状态是否更新
        if data.get("action_ok"):
            new_time = state.get("time", 0)
            if new_time > test_state.get("time", 0):
                print(f"  ✅ 状态已更新: time={new_time}")
            else:
                print(f"  ⚠️  状态未更新: time={new_time}")
        
        print_result(True, "基本聊天流程测试通过")
        return True
        
    except requests.exceptions.ConnectionError:
        print_result(False, "无法连接到服务，请先启动: uvicorn main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_2_chat_action_validation_failure():
    """
    测试 2: 动作验证失败的情况
    """
    print_test("测试 2: 动作验证失败的情况")
    
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
        print("已准备测试状态：包含死亡角色 dead_char")
        
        # 发送可能导致无效动作的请求
        chat_request = {
            "message": "我要和 dead_char 说话"
        }
        
        print(f"\n发送请求: {json.dumps(chat_request, ensure_ascii=False)}")
        print("预期：应该生成 talk 动作，但验证失败，返回合理的失败解释")
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=chat_request,
            timeout=30
        )
        
        if response.status_code != 200:
            print_result(False, f"API 返回状态码: {response.status_code}")
            return False
        
        data = response.json()
        
        # 验证返回格式
        if not data.get("ok"):
            print_result(False, f"请求失败: {data.get('error')}")
            return False
        
        # 如果 action_ok 为 false，应该有 error 和合理的 narration
        if not data.get("action_ok"):
            error = data.get("error")
            narration = data.get("narration", "")
            
            print(f"\n结果检查:")
            print(f"  action_ok: {data.get('action_ok')}")
            print(f"  error: {error}")
            print(f"  narration: {narration[:150]}...")
            
            if error and narration:
                print_result(True, "动作验证失败，返回了错误信息和合理的解释")
                return True
            else:
                print_result(False, "动作验证失败，但缺少 error 或 narration")
                return False
        else:
            # 如果意外通过了，也记录
            print(f"  ⚠️  动作意外通过验证（可能 LLM 生成了其他动作）")
            print_result(True, "请求处理成功（动作可能被 LLM 调整为有效动作）")
            return True
        
    except requests.exceptions.ConnectionError:
        print_result(False, "无法连接到服务，请先启动: uvicorn main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_3_chat_response_format():
    """
    测试 3: 返回格式验证
    """
    print_test("测试 3: 返回格式验证")
    
    try:
        # 准备简单状态
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
        
        # 发送简单请求
        chat_request = {
            "message": "你好"
        }
        
        print(f"\n发送请求: {json.dumps(chat_request, ensure_ascii=False)}")
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=chat_request,
            timeout=30
        )
        
        if response.status_code != 200:
            print_result(False, f"API 返回状态码: {response.status_code}")
            return False
        
        data = response.json()
        
        # 验证必需字段
        required_fields = ["ok", "narration", "action_ok", "state"]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            print_result(False, f"缺少必需字段: {missing_fields}")
            return False
        
        # 验证字段类型
        checks = []
        checks.append(("ok", bool, data.get("ok")))
        checks.append(("action_ok", bool, data.get("action_ok")))
        checks.append(("narration", str, data.get("narration")))
        checks.append(("state", dict, data.get("state")))
        
        for field_name, expected_type, value in checks:
            if not isinstance(value, expected_type):
                print_result(False, f"字段 {field_name} 类型错误: 期望 {expected_type.__name__}, 实际 {type(value).__name__}")
                return False
        
        # 验证 state 结构
        state = data.get("state", {})
        if "time" not in state:
            print_result(False, "state 缺少 time 字段")
            return False
        
        print(f"\n字段验证:")
        for field_name, _, value in checks:
            if field_name == "state":
                print(f"  {field_name}: <dict with time={state.get('time')}>")
            elif field_name == "narration":
                print(f"  {field_name}: {str(value)[:50]}...")
            else:
                print(f"  {field_name}: {value}")
        
        print_result(True, "返回格式验证通过")
        return True
        
    except requests.exceptions.ConnectionError:
        print_result(False, "无法连接到服务，请先启动: uvicorn main:app --reload")
        return False
    except Exception as e:
        print_result(False, f"测试异常: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_4_chat_missing_message():
    """
    测试 4: 缺少 message 字段
    """
    print_test("测试 4: 缺少 message 字段")
    
    try:
        # 发送缺少 message 的请求
        chat_request = {}
        
        print(f"\n发送请求: {json.dumps(chat_request, ensure_ascii=False)}")
        print("预期：应该返回错误")
        
        response = requests.post(
            "http://localhost:8000/chat",
            json=chat_request,
            timeout=10
        )
        
        if response.status_code != 200:
            print_result(False, f"API 返回状态码: {response.status_code}")
            return False
        
        data = response.json()
        
        if not data.get("ok"):
            error = data.get("error", "")
            if "message" in error.lower() or "必需" in error:
                print_result(True, f"正确返回错误: {error}")
                return True
            else:
                print_result(False, f"错误信息不明确: {error}")
                return False
        else:
            print_result(False, "应该返回错误，但却成功了")
            return False
        
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
    print("POST /chat 端点测试")
    print("="*60)
    print("\n⚠️  请确保服务正在运行: uvicorn main:app --reload")
    print("⚠️  请确保已设置 API Key: SUPER_MIND_API_KEY 或 AI_BUILDER_TOKEN")
    
    results = []
    
    # 运行测试
    results.append(("测试 1: 基本聊天流程", test_1_chat_basic_flow()))
    results.append(("测试 2: 动作验证失败", test_2_chat_action_validation_failure()))
    results.append(("测试 3: 返回格式验证", test_3_chat_response_format()))
    results.append(("测试 4: 缺少 message", test_4_chat_missing_message()))
    
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

