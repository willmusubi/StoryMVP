from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from pydantic import BaseModel as _BaseModel
else:
    _BaseModel = BaseModel

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

def validate_action(state: Dict[str, Any], action: "Action") -> Dict[str, Any]:
    """
    验证动作是否合法
    
    返回: {ok: bool, reason?: str}
    """
    characters = state.get("characters", {})
    items = state.get("items", {})
    
    # 检查 actor 是否存在
    if action.actor != "player" and action.actor not in characters:
        return {"ok": False, "reason": f"执行者 {action.actor} 不存在"}
    
    # 检查 actor 是否存活（如果不是 player）
    if action.actor != "player":
        actor_char = characters.get(action.actor)
        if actor_char and not actor_char.get("alive", True):
            return {"ok": False, "reason": f"执行者 {action.actor} 已死亡"}
    
    # 根据动作类型进行验证
    if action.type in ["talk", "rescue", "give_item"]:
        # 不能对 alive=false 的角色执行交互
        if action.target and action.target in characters:
            target_char = characters[action.target]
            if not target_char.get("alive", True):
                return {"ok": False, "reason": f"目标角色 {action.target} 已死亡，无法执行 {action.type}"}
    
    if action.type == "move":
        # move 必须提供 to_location
        if not action.to_location:
            return {"ok": False, "reason": "move 动作必须提供 to_location"}
    
    if action.type == "give_item":
        # give_item 必须提供 item
        if not action.item:
            return {"ok": False, "reason": "give_item 动作必须提供 item"}
        
        # 必须保证 items[item].owner == actor 才能给
        if action.item not in items:
            return {"ok": False, "reason": f"物品 {action.item} 不存在"}
        
        item_owner = items[action.item].get("owner")
        if item_owner != action.actor:
            return {"ok": False, "reason": f"物品 {action.item} 不属于 {action.actor}，当前拥有者: {item_owner}"}
        
        # 必须提供 target（接收者）
        if not action.target:
            return {"ok": False, "reason": "give_item 动作必须提供 target（接收者）"}
        
        # 检查接收者是否存在
        if action.target not in characters:
            return {"ok": False, "reason": f"接收者 {action.target} 不存在"}
    
    if action.type in ["attack", "rescue"]:
        # attack/rescue 需要 target 存在且 alive=true
        if not action.target:
            return {"ok": False, "reason": f"{action.type} 动作必须提供 target"}
        
        if action.target not in characters:
            return {"ok": False, "reason": f"目标角色 {action.target} 不存在"}
        
        target_char = characters[action.target]
        if not target_char.get("alive", True):
            return {"ok": False, "reason": f"目标角色 {action.target} 已死亡，无法执行 {action.type}"}
    
    return {"ok": True}

def apply_action(state: Dict[str, Any], action: "Action") -> Dict[str, Any]:
    """
    应用动作到状态，返回新状态
    
    注意：不修改原状态，返回新状态
    """
    # 深拷贝状态（简单方式：通过 JSON 序列化/反序列化）
    import copy
    new_state = copy.deepcopy(state)
    
    characters = new_state.get("characters", {})
    items = new_state.get("items", {})
    
    # 更新时间
    new_state["time"] = new_state.get("time", 0) + 1
    
    if action.type == "move":
        # 更新 actor 的 location
        if action.actor == "player":
            # player 没有在 characters 中，可以创建一个简单的记录
            # 或者假设 player 的位置存储在 state 的其他地方
            # 这里我们假设 player 的位置可以存储在 state 的顶层
            if "player" not in characters:
                characters["player"] = {
                    "alive": True,
                    "location": action.to_location,
                    "affinity_to_player": 100  # 玩家对自己的好感度
                }
            else:
                characters["player"]["location"] = action.to_location
        else:
            if action.actor in characters:
                characters[action.actor]["location"] = action.to_location
    
    elif action.type == "give_item":
        # 更新物品 owner
        if action.item in items:
            items[action.item]["owner"] = action.target
    
    elif action.type == "talk":
        # 只影响 affinity_to_player
        if action.target and action.target in characters:
            target_char = characters[action.target]
            current_affinity = target_char.get("affinity_to_player", 0)
            
            # 简单规则：如果 intent 包含"救/帮/保护"则 +10，否则 0
            intent_lower = action.intent.lower()
            if any(keyword in intent_lower for keyword in ["救", "帮", "保护", "救", "助", "援"]):
                new_affinity = min(100, current_affinity + 10)
            else:
                new_affinity = current_affinity  # 保持不变
            
            target_char["affinity_to_player"] = new_affinity
    
    elif action.type == "attack":
        # 攻击：降低目标的好感度
        if action.target and action.target in characters:
            target_char = characters[action.target]
            current_affinity = target_char.get("affinity_to_player", 0)
            target_char["affinity_to_player"] = max(-100, current_affinity - 20)
    
    elif action.type == "rescue":
        # 救援：增加目标的好感度
        if action.target and action.target in characters:
            target_char = characters[action.target]
            current_affinity = target_char.get("affinity_to_player", 0)
            target_char["affinity_to_player"] = min(100, current_affinity + 30)
    
    return new_state

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

class Action(BaseModel):
    """
    动作协议 Schema
    """
    type: Literal["talk", "give_item", "move", "attack", "rescue"]
    actor: str = Field(default="player", description="执行动作的角色，默认为 player")
    target: Optional[str] = Field(default=None, description="目标角色或物品")
    to_location: Optional[str] = Field(default=None, description="目标位置（用于 move）")
    item: Optional[str] = Field(default=None, description="物品ID（用于 give_item）")
    intent: str = Field(description="自然语言描述动作意图")

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

@app.post("/act")
async def act(action: Action):
    """
    执行动作
    
    输入 action，先 validate 再 apply，再 save_state，返回 {ok, state, error?}
    """
    try:
        # 加载当前状态
        state = load_state()
        
        # 验证动作
        validation = validate_action(state, action)
        if not validation["ok"]:
            return {
                "ok": False,
                "error": validation.get("reason", "动作验证失败"),
                "state": state
            }
        
        # 应用动作
        new_state = apply_action(state, action)
        
        # 保存状态
        save_state(new_state)
        
        return {
            "ok": True,
            "state": new_state
        }
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "state": load_state()  # 返回当前状态
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

