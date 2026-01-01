from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv
from openai import OpenAI
import os
import json
from pathlib import Path
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, Literal, TYPE_CHECKING, Protocol
from abc import ABC, abstractmethod

if TYPE_CHECKING:
    from pydantic import BaseModel as _BaseModel
else:
    _BaseModel = BaseModel

# 加载环境变量
load_dotenv()

app = FastAPI()

# ==================== LLM 接口抽象 ====================

class LLMProvider(ABC):
    """可替换的 LLM 接口"""
    
    @abstractmethod
    def chat_completion(self, messages: list[Dict[str, str]], model: str = "supermind-agent-v1") -> str:
        """
        调用 LLM 生成回复
        
        Args:
            messages: 消息列表，格式 [{"role": "system", "content": "..."}, ...]
            model: 模型名称
        
        Returns:
            LLM 生成的文本内容
        """
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI SDK 实现"""
    
    def __init__(self, base_url: str, api_key: str):
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
    
    def chat_completion(self, messages: list[Dict[str, str]], model: str = "supermind-agent-v1") -> str:
        completion = self.client.chat.completions.create(
            model=model,
            messages=messages
        )
        return completion.choices[0].message.content if completion.choices else ""

# 初始化 LLM Provider
api_key = os.getenv("SUPER_MIND_API_KEY") or os.getenv("AI_BUILDER_TOKEN")
if not api_key:
    raise ValueError("请设置 SUPER_MIND_API_KEY 或 AI_BUILDER_TOKEN 环境变量")

llm_provider: LLMProvider = OpenAIProvider(
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

def build_chat_prompt(state: Dict[str, Any], user_message: str, lore_snippet: Optional[str] = None) -> list[Dict[str, str]]:
    """
    构建聊天 prompt
    
    Returns:
        messages 列表，用于 LLM 调用
    """
    # System prompt
    system_prompt = """你是三国剧情引擎。你的职责是根据用户输入和当前世界状态，生成合理的动作和叙述。

**重要规则（必须严格遵守）：**
1. 必须遵守 state 中的世界状态
2. 不得编造已死角色存活（alive=false 的角色不能出现）
3. 不得让物品瞬移（物品必须在当前拥有者手中）
4. 不得修改 state（只能通过 proposed_action 来改变状态）
5. 只能输出严格 JSON 格式，不要添加任何其他文本

**输出格式（必须是有效的 JSON）：**
{
  "proposed_action": {
    "type": "talk" | "give_item" | "move" | "attack" | "rescue",
    "actor": "player",
    "target": "角色ID或物品ID（可选）",
    "to_location": "位置（仅 move 需要）",
    "item": "物品ID（仅 give_item 需要）",
    "intent": "自然语言描述动作意图"
  },
  "narration": "一段叙述文字，描述发生了什么"
}

**动作类型说明：**
- talk: 与角色对话
- give_item: 给角色物品
- move: 移动到新位置
- attack: 攻击角色
- rescue: 救援角色

**注意事项：**
- proposed_action 必须符合动作协议规范
- narration 应该生动描述动作和结果
- 如果用户意图不合理（如对死亡角色说话），narration 应该合理解释为什么无法执行
"""
    
    # 构建用户 prompt
    user_prompt = f"""STATE:
{json.dumps(state, ensure_ascii=False, indent=2)}

USER_MESSAGE: {user_message}"""
    
    if lore_snippet:
        user_prompt += f"""

LORE_SNIPPET:
{lore_snippet}"""
    
    user_prompt += """

请根据以上信息，生成 proposed_action 和 narration。输出必须是有效的 JSON。"""
    
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """
    解析 LLM 返回的 JSON
    
    Returns:
        {"proposed_action": Action, "narration": str} 或 None（如果解析失败）
    """
    try:
        # 尝试提取 JSON（可能包含 markdown 代码块）
        text = response_text.strip()
        
        # 如果包含 ```json 或 ```，提取其中的 JSON
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                text = text[start:end].strip()
        
        # 解析 JSON
        data = json.loads(text)
        
        if "proposed_action" not in data or "narration" not in data:
            return None
        
        return data
    except (json.JSONDecodeError, KeyError) as e:
        return None

def explain_action_failure(action: "Action", validation_result: Dict[str, Any], state: Dict[str, Any]) -> str:
    """
    当 action 验证失败时，让 LLM 生成合理的解释
    
    Returns:
        解释失败原因的叙述文字
    """
    error_reason = validation_result.get("reason", "未知错误")
    
    # 兼容 Pydantic v1 和 v2
    try:
        action_dict = action.model_dump()  # Pydantic v2
    except AttributeError:
        action_dict = action.dict()  # Pydantic v1
    
    prompt = f"""动作验证失败，需要生成合理的叙述来解释为什么无法执行。

失败的动作:
{json.dumps(action_dict, ensure_ascii=False, indent=2)}

失败原因: {error_reason}

当前状态:
{json.dumps(state, ensure_ascii=False, indent=2)}

请生成一段合理的叙述，解释为什么这个动作无法执行。叙述应该：
1. 符合三国背景
2. 合理解释失败原因（但不要编造事实）
3. 保持角色一致性

只输出叙述文字，不要输出 JSON 或其他格式。"""
    
    try:
        messages = [
            {"role": "system", "content": "你是一个三国剧情叙述者，负责解释为什么某些动作无法执行。"},
            {"role": "user", "content": prompt}
        ]
        explanation = llm_provider.chat_completion(messages, model="supermind-agent-v1")
        return explanation.strip()
    except Exception as e:
        # 如果 LLM 调用失败，返回简单解释
        return f"无法执行该动作：{error_reason}"

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
    Chat endpoint - 第一版实现
    
    输入: {message: string}
    处理流程:
    1. load_state()
    2. 构建 prompt（包含 STATE、USER_MESSAGE、LORE_SNIPPET）
    3. 调用 LLM 生成 proposed_action 和 narration
    4. 验证和应用 action
    5. 返回结果
    """
    if not request or not request.message:
        return {
            "ok": False,
            "error": "message 字段是必需的"
        }
    
    try:
        # 1. 加载状态
        state = load_state()
        
        # 2. 加载故事片段（前 2000 字符）
        story = load_story()
        lore_snippet = story[:2000] if len(story) > 2000 else story if story else None
        
        # 3. 构建 prompt
        messages = build_chat_prompt(state, request.message, lore_snippet)
        
        # 4. 调用 LLM
        llm_response = llm_provider.chat_completion(messages, model="supermind-agent-v1")
        
        # 5. 解析 LLM 响应
        parsed = parse_llm_response(llm_response)
        
        if not parsed:
            return {
                "ok": False,
                "error": "无法解析 LLM 响应为有效 JSON",
                "llm_response": llm_response[:500] if llm_response else None,
                "state": state
            }
        
        proposed_action_dict = parsed.get("proposed_action")
        narration = parsed.get("narration", "")
        
        if not proposed_action_dict:
            return {
                "ok": False,
                "error": "LLM 响应中缺少 proposed_action",
                "narration": narration,
                "state": state
            }
        
        # 6. 创建 Action 对象并验证
        try:
            proposed_action = Action(**proposed_action_dict)
        except Exception as e:
            return {
                "ok": False,
                "error": f"proposed_action 格式错误: {str(e)}",
                "narration": narration,
                "state": state
            }
        
        # 7. 验证动作
        validation = validate_action(state, proposed_action)
        
        if not validation["ok"]:
            # 动作验证失败，让 LLM 生成合理的解释
            failure_narration = explain_action_failure(proposed_action, validation, state)
            
            return {
                "ok": True,  # 请求处理成功，只是动作未执行
                "narration": failure_narration,
                "action_ok": False,
                "error": validation.get("reason"),
                "state": state  # 状态未改变
            }
        
        # 8. 应用动作
        new_state = apply_action(state, proposed_action)
        
        # 9. 保存状态
        save_state(new_state)
        
        # 10. 返回结果
        return {
            "ok": True,
            "narration": narration,
            "action_ok": True,
            "state": new_state
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "ok": False,
            "error": str(e),
            "state": load_state()  # 返回当前状态
        }

