# 三国 MVP FastAPI 项目

## 安装依赖

```bash
pip install -r requirements.txt
```

## 配置环境变量

创建 `.env` 文件，添加你的 API Key：

```env
SUPER_MIND_API_KEY=your_api_key_here
```

或者使用 `AI_BUILDER_TOKEN`：

```env
AI_BUILDER_TOKEN=your_api_key_here
```

## 运行项目

使用 uvicorn 启动服务：

```bash
uvicorn main:app --reload
```

或者指定主机和端口：

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## 访问

- 主页: http://localhost:8000/
- API 文档: http://localhost:8000/docs
- 替代文档: http://localhost:8000/redoc

## API 端点

- `GET /` - 返回 "Hello 三国 MVP" 静态页面
- `GET /state` - 返回当前世界状态 (JSON)
- `GET /lore` - 返回故事内容的前 2000 字符 (JSON)
- `POST /act` - 执行动作（需要先验证，再应用，最后保存状态）
- `POST /chat` - AI 对话接口（第一版）：根据用户输入生成动作和叙述

## AI 调用说明

所有 AI 调用都使用 OpenAI SDK，配置如下：

- Base URL: `https://space.ai-builders.com/backend/v1`
- 模型: `supermind-agent-v1`
- 认证: 通过 Bearer Token (从环境变量读取)

### LLM 接口设计

系统使用可替换的 LLM 接口抽象 (`LLMProvider`)，当前实现为 `OpenAIProvider`。可以轻松替换为其他 LLM 服务。

### POST /chat 端点说明

**输入：**

```json
{
  "message": "用户输入的自然语言"
}
```

**处理流程：**

1. 加载当前世界状态 (`load_state()`)
2. 构建 system prompt（强调遵守 state、不得编造事实等规则）
3. 构建 user prompt，包含：
   - `STATE`: 序列化后的 state.json
   - `USER_MESSAGE`: 用户输入
   - `LORE_SNIPPET`: story.md 前 2000 字符（可选）
4. 调用 LLM 生成 JSON 响应：
   ```json
   {
     "proposed_action": <Action>,
     "narration": "..."
   }
   ```
5. 验证和应用 `proposed_action`
6. 保存状态

**返回：**

```json
{
  "ok": true,
  "narration": "叙述文字",
  "action_ok": true/false,
  "error": "错误信息（如果 action_ok 为 false）",
  "state": <new_state>
}
```

**特殊处理：**

- 如果 `proposed_action` 验证失败，会调用 LLM 生成合理的失败解释（但仍不编造事实）
- 即使动作失败，也会返回 `ok: true`（请求处理成功），但 `action_ok: false`

## 世界状态管理

项目使用 `data/state.json` 文件存储持久化的世界状态。状态结构包含：

- `time`: 当前章节/回合进度或 tick (整数)
- `characters`: 角色字典，每个角色包含：
  - `alive`: 是否存活 (布尔值)
  - `location`: 当前位置 (字符串)
  - `affinity_to_player`: 对玩家的好感度 (-100~100)
- `items`: 物品字典，每个物品包含：
  - `owner`: 拥有者 (字符串，角色 ID)

状态管理函数：

- `load_state()`: 读取 state.json，如果文件不存在或损坏则返回默认状态
- `save_state(state)`: 原子写入 state.json（使用临时文件+重命名，避免写坏文件）

故事管理函数：

- `load_story()`: 读取 story.md 文件内容，如果文件不存在则返回空字符串

## 动作协议（Action Schema）

动作协议定义了玩家可以执行的操作。每个动作包含：

- `type`: 动作类型，可选值：`"talk"`, `"give_item"`, `"move"`, `"attack"`, `"rescue"`
- `actor`: 执行者，默认为 `"player"`
- `target`: 目标角色或物品（可选）
- `to_location`: 目标位置（用于 `move`，可选）
- `item`: 物品 ID（用于 `give_item`，可选）
- `intent`: 自然语言描述动作意图（必需）

### 动作验证规则

- 不能对 `alive=false` 的角色执行交互（`talk`/`rescue`/`give_item`）
- `move` 必须提供 `to_location`
- `give_item` 必须保证 `items[item].owner == actor` 才能给
- `attack`/`rescue` 需要 `target` 存在且 `alive=true`

### 动作效果

- `move`: 更新 actor 的 location
- `give_item`: 更新物品 owner
- `talk`: 影响 `affinity_to_player`（如果 intent 包含"救/帮/保护"则 +10，否则不变）
- `attack`: 降低目标好感度 -20
- `rescue`: 增加目标好感度 +30

## 示例请求

```bash
# 获取当前世界状态
curl http://localhost:8000/state

# 获取故事内容（前 2000 字符）
curl http://localhost:8000/lore

# 执行 move 动作
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "move",
    "actor": "player",
    "to_location": "luo_yang",
    "intent": "前往洛阳"
  }'

# 执行 talk 动作
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "talk",
    "actor": "player",
    "target": "liu_bei",
    "intent": "我要帮助你"
  }'

# 执行 give_item 动作
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "give_item",
    "actor": "player",
    "target": "liu_bei",
    "item": "sword_1",
    "intent": "把剑给你"
  }'

# 测试 POST /chat（第一版）
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "我要前往洛阳"}'

# 预期返回：
# {
#   "ok": true,
#   "narration": "你决定前往洛阳...",
#   "action_ok": true,
#   "state": { ... }
# }
```
