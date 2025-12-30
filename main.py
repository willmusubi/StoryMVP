from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from pathlib import Path
from pydantic import BaseModel
from typing import Optional, Dict, Any

# 加载环境变量
load_dotenv()

app = FastAPI()

# 初始化 OpenAI 客户端，指向 AI Builder API
# 从环境变量读取 API Key（支持 SUPER_MIND_API_KEY 和 AI_BUILDER_TOKEN）
api_key = os.getenv("SUPER_MIND_API_KEY") or os.getenv("AI_BUILDER_TOKEN")
if not api_key:
    raise ValueError("请设置 SUPER_MIND_API_KEY 或 AI_BUILDER_TOKEN 环境变量")

client = OpenAI(
    base_url="https://space.ai-builders.com/backend/v1",
    api_key=api_key,
)

# 状态文件路径
STATE_FILE = Path(__file__).parent / "data" / "state.json"
# 故事文件路径
STORY_FILE = Path(__file__).parent / "data" / "story.md"

def load_state() -> Dict[str, Any]:
    """
    读取 state.json 文件
    如果文件不存在，返回默认状态
    """
    if not STATE_FILE.exists():
        # 确保目录存在
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # 返回默认状态
        default_state = {
            "time": 0,
            "characters": {},
            "items": {}
        }
        save_state(default_state)
        return default_state
    
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        # 如果文件损坏，返回默认状态
        default_state = {
            "time": 0,
            "characters": {},
            "items": {}
        }
        save_state(default_state)
        return default_state

def save_state(state: Dict[str, Any]) -> None:
    """
    原子写入 state.json 文件
    使用临时文件然后重命名，避免写坏文件
    """
    # 确保目录存在
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 创建临时文件
    temp_file = STATE_FILE.with_suffix(".tmp")
    
    try:
        # 写入临时文件
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
        
        # 原子重命名（在支持的系统上这是原子操作）
        temp_file.replace(STATE_FILE)
    except Exception as e:
        # 如果写入失败，删除临时文件
        if temp_file.exists():
            temp_file.unlink()
        raise e

def load_story() -> str:
    """
    读取 story.md 文件内容
    如果文件不存在，返回空字符串
    """
    if not STORY_FILE.exists():
        return ""
    
    try:
        with open(STORY_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except IOError:
        return ""

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>三国 MVP</title>
        <meta charset="utf-8">
        <style>
            body {
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            }
            h1 {
                color: white;
                font-size: 3em;
                text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            }
        </style>
    </head>
    <body>
        <h1>Hello 三国 MVP</h1>
    </body>
    </html>
    """

class ChatRequest(BaseModel):
    message: Optional[str] = None

@app.get("/state")
async def get_state():
    """
    返回当前世界状态
    """
    state = load_state()
    return state

@app.get("/lore")
async def get_lore():
    """
    返回故事内容的前 2000 字符
    避免返回过大的内容
    """
    story = load_story()
    # 返回前 2000 字符
    truncated = story[:2000] if len(story) > 2000 else story
    return {
        "content": truncated,
        "total_length": len(story),
        "truncated": len(story) > 2000
    }

@app.post("/chat")
async def chat(request: Optional[ChatRequest] = None):
    """
    Chat endpoint that uses the AI Builder API with supermind-agent-v1 model.
    All AI calls use the OpenAI SDK pointing to the correct base URL.
    
    If no message is provided, returns {"ok": true} as a simple response.
    """
    # 如果没有提供消息，返回简单的确认响应
    if not request or not request.message:
        return {"ok": True}
    
    try:
        # 使用 OpenAI SDK 调用 AI Builder API
        # 模型必须是 supermind-agent-v1
        # Base URL: https://space.ai-builders.com/backend/v1
        completion = client.chat.completions.create(
            model="supermind-agent-v1",
            messages=[
                {
                    "role": "user",
                    "content": request.message
                }
            ]
        )
        
        # 返回响应
        return {
            "ok": True,
            "response": completion.choices[0].message.content if completion.choices else None,
            "usage": {
                "prompt_tokens": completion.usage.prompt_tokens if completion.usage else 0,
                "completion_tokens": completion.usage.completion_tokens if completion.usage else 0,
                "total_tokens": completion.usage.total_tokens if completion.usage else 0,
            } if completion.usage else None
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e)
        }

