from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from openai import OpenAI
import os
from pydantic import BaseModel
from typing import Optional

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

