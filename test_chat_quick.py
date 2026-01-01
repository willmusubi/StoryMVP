#!/usr/bin/env python3
"""
POST /chat 端点快速测试

快速验证核心功能
"""

import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("⚠️  requests 模块未安装")
    sys.exit(1)

def test_chat_quick():
    """快速测试"""
    print("="*60)
    print("POST /chat 快速测试")
    print("="*60)
    
    # 测试 1: 基本请求
    print("\n测试 1: 发送聊天请求...")
    try:
        response = requests.post(
            "http://localhost:8000/chat",
            json={"message": "我要前往洛阳"},
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 请求成功")
            print(f"  ok: {data.get('ok')}")
            print(f"  action_ok: {data.get('action_ok')}")
            print(f"  narration: {data.get('narration', '')[:100]}...")
            
            # 验证必需字段
            required = ["ok", "narration", "action_ok", "state"]
            missing = [f for f in required if f not in data]
            if missing:
                print(f"❌ 缺少字段: {missing}")
                return False
            else:
                print(f"✅ 所有必需字段存在")
                return True
        else:
            print(f"❌ HTTP {response.status_code}: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接服务，请先启动: uvicorn main:app --reload")
        return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时（LLM 调用可能需要更长时间）")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

if __name__ == "__main__":
    success = test_chat_quick()
    sys.exit(0 if success else 1)

