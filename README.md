### 产品愿景（Vision）

打造一个**具备世界状态一致性（World-State Consistency）**的 AI 角色互动系统，使用户能够在高自由度的剧情中，与 AI 角色进行长期、可信、沉浸式的互动，而不破坏故事逻辑。

该系统不是“陪聊模型”，而是一个 **具备因果约束的叙事引擎（Narrative Engine）**。

---

### 核心问题（Core Problem）

当前 LLM 在叙事互动中存在严重的「世界状态崩坏」问题：

1. **实体状态不一致（Entity State Inconsistency）**

   - 角色拥有/失去物品不一致
   - 死亡角色复活、活人被当作已死

2. **时间线混乱（Temporal Incoherence）**

   - 事件顺序错乱
   - 因果倒置

3. **空间逻辑错误（Spatial Inconsistency）**

   - 瞬移
   - 地点归属混乱

4. **关系与情感漂移（Relational Drift）**

   - 角色对玩家态度无连续性
   - 情感状态不累积、不记忆

👉 本质问题：  
**缺乏“单一真实世界模型（Single Source of Truth）”与“硬约束验证层”。**

---

### 产品目标（Product Goal）

构建一个 **剧情可变、但世界状态一致** 的 AI 剧情系统：

- 玩家可以：
  - 改变剧情走向
  - 拯救或牺牲角色
  - 改写关键历史节点
- 系统必须：
  - 永远遵守已经发生的事实
  - 不允许违反因果、时间、空间、生命状态

---

### MVP 范围（第一阶段）

**内容范围**

- 固定世界观：三国演义
- 单一主线时间线（不做分支宇宙）
- 核心角色：曹操、董卓、吕布、貂蝉、何太后等

**能力范围**

- 支持玩家自由语言输入推动剧情
- 支持有限但真实的“剧情分叉”
- 实时维护以下状态：
  - 角色生死（alive/dead）
  - 所属关系（faction / loyalty）
  - 关键物品归属（items）
  - 对玩家的关系值（affinity）

---

### 成功标准（OKRs）

#### 🎯 Objective

构建一个**不会自相矛盾的叙事 AI 系统**。

#### 📏 Key Results

1. **一致性（Consistency）**

   - 在 100 轮交互中，不出现违反已记录世界状态的叙述（0 hallucination）

2. **可控性（Controllability）**

   - 玩家行为能真实影响后续剧情（可验证变化）

3. **可解释性（Explainability）**

   - 任一状态变化都能追溯原因（哪一行为触发）

4. **沉浸感（Immersion）**

   - 角色语言与行为符合设定（不 OOC）

# 三国 MVP - AI 驱动叙事引擎

一个基于 FastAPI 的 AI 驱动叙事引擎，具有持久化世界状态、动作协议、LLM 集成和智能检索系统。

## 核心特性

- 🎮 **世界状态管理**：持久化的 JSON 状态文件，支持原子写入
- 🎯 **动作协议**：结构化的动作系统，支持验证和应用
- 🤖 **LLM 集成**：使用 OpenAI SDK 与 AI Builder Student Portal API 集成
- 🔍 **智能检索**：基于关键字匹配的故事片段检索系统
- 🎨 **Web 界面**：现代化的聊天界面，支持实时状态查看
- ✅ **自动化测试**：完整的 pytest 测试套件

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

- **主页（聊天界面）**: http://localhost:8000/
- **API 文档**: http://localhost:8000/docs
- **替代文档**: http://localhost:8000/redoc

## 项目结构

```
StoryMVP/
├── main.py                 # FastAPI 应用主文件
├── requirements.txt        # Python 依赖
├── templates/
│   └── index.html         # 前端聊天界面
├── static/                # 静态文件目录
├── data/
│   ├── state.json        # 世界状态文件
│   └── story.md          # 故事内容（用于检索）
├── tests/
│   └── test_validator.py    # 自动化测试
└── README.md             # 本文档
```

## API 端点

### 基础端点

- `GET /` - 返回聊天界面（HTML）
- `GET /state` - 返回当前世界状态 (JSON)
- `GET /lore` - 返回故事内容的前 2000 字符 (JSON)

### 动作端点

- `POST /act` - 执行动作（需要先验证，再应用，最后保存状态）

### AI 对话端点

- `POST /chat` - AI 对话接口：根据用户输入生成动作和叙述

## AI 调用说明

所有 AI 调用都使用 OpenAI SDK，配置如下：

- **Base URL**: `https://space.ai-builders.com/backend/v1`
- **模型**: `supermind-agent-v1`
- **认证**: 通过 Bearer Token (从环境变量读取)

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
2. **检索相关故事片段**：根据用户消息和当前时间检索 top-3 相关 chunks
3. 构建 system prompt（强调遵守 state、不得编造事实等规则）
4. 构建 user prompt，包含：
   - `STATE`: 序列化后的 state.json
   - `USER_MESSAGE`: 用户输入
   - `LORE_CONTEXT`: 检索到的相关故事片段（用 `---` 分隔）
5. 调用 LLM 生成 JSON 响应：
   ```json
   {
     "proposed_action": <Action>,
     "narration": "..."
   }
   ```
6. 验证和应用 `proposed_action`
7. 保存状态

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
- `events`: 事件列表，每个事件包含：
  - `id`: 事件唯一标识
  - `time`: 事件发生时间
  - `type`: 动作类型
  - `actor`: 执行者

状态管理函数：

- `load_state()`: 读取 state.json，如果文件不存在或损坏则返回默认状态
- `save_state(state)`: 原子写入 state.json（使用临时文件+重命名，避免写坏文件）

故事管理函数：

- `load_story()`: 读取 story.md 文件内容，如果文件不存在则返回空字符串

## 智能检索系统

系统实现了基于关键字匹配的故事片段检索功能：

### 检索流程

1. **Chunk 分割**：将 `story.md` 按段落/空行切分成 chunks
2. **打分机制**：
   - 角色名称匹配：权重 20.0（最高优先级）
   - 普通关键字匹配：权重 `len(word) / 5.0`
3. **Top-K 检索**：返回分数最高的 top-3 chunks

### 检索函数

- `chunk_story(story_text)`: 将故事文本切分成 chunks
- `score_chunk(chunk, user_message, current_time)`: 对 chunk 进行打分
- `retrieve_relevant_chunks(story_text, user_message, current_time, top_k=3)`: 检索相关 chunks

### 特性

- **角色名称优先**：当用户提到"董卓"、"貂蝉"、"吕布"等角色时，能准确检索到相关片段
- **Prompt 体积可控**：平均 prompt 大小约 3,341 字符，最大不超过 10,000 字符
- **相关性区分**：能区分相关和不相关的查询

## 动作协议（Action Schema）

动作协议定义了玩家可以执行的操作。每个动作包含：

- `type`: 动作类型，可选值：`"talk"`, `"give_item"`, `"move"`, `"attack"`, `"rescue"`
- `actor`: 执行者，默认为 `"player"`
- `target`: 目标角色或物品（可选）
- `to_location`: 目标位置（用于 `move`，可选）
- `item`: 物品 ID（用于 `give_item`，可选）
- `intent`: 自然语言描述动作意图（必需）
- `event`: 可选的事件 ID，用于 timeline 验证

### 动作验证规则

系统实现了 4 类崩坏防护：

1. **Ownership（所有权）**：

   - `give_item` 必须保证 `items[item].owner == actor` 才能给

2. **Life（生死状态）**：

   - 不能对 `alive=false` 的角色执行交互（`talk`/`rescue`/`give_item`）
   - 死亡角色不能执行动作

3. **Timeline（时间线）**：

   - 不能重复发生同一唯一事件
   - 事件必须按 `state.time` 单调递增

4. **Location（位置）**：
   - `move` 必须提供 `to_location`

### 动作效果

- `move`: 更新 actor 的 location，时间 +1
- `give_item`: 更新物品 owner，时间 +1
- `talk`: 影响 `affinity_to_player`（如果 intent 包含"救/帮/保护"则 +10，否则不变），时间 +1
- `attack`: 降低目标好感度 -20，时间 +1
- `rescue`: 增加目标好感度 +30，时间 +1

如果动作包含 `event`，会将事件添加到 `state.events` 列表中。

## 前端界面

项目包含一个现代化的 Web 聊天界面：

### 功能特性

- **聊天窗口**：消息列表，支持用户和助手消息
- **输入框和发送按钮**：支持回车发送
- **状态面板**：右侧可折叠显示当前 state（JSON 格式化）
- **错误提示**：当 `action_ok=false` 时，用红色样式显示错误信息
- **自动更新**：每次聊天后自动更新状态显示

### 界面特点

- 响应式设计，适配不同屏幕
- 加载状态指示（发送时显示 loading 动画）
- 自动滚动到最新消息
- 状态面板可折叠/展开

## 自动化测试

项目使用 pytest 进行自动化测试：

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_validator.py -v

# 运行检索系统验收测试
pytest test_retrieval_final.py -v
```

### 测试覆盖

- **状态管理测试** (`test_state_validation.py`): 测试状态加载和保存
- **动作验证测试** (`test_action_validation.py`): 测试动作协议和验证规则
- **验证器测试** (`tests/test_validator.py`): 覆盖 4 类崩坏场景（至少 15 个测试用例）
- **检索系统测试** (`test_retrieval_final.py`): 验收测试检索系统

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

# 测试 POST /chat
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

## 开发指南

### 核心原则

1. **单一数据源（SSOT）**：世界状态存储在 `data/state.json`，所有状态变更必须通过验证器
2. **显式状态转换**：所有状态变更必须通过 `validate_action` 和 `apply_action`
3. **确定性验证**：验证逻辑必须是确定性的，可测试的
4. **不编造事实**：LLM 输出不得与当前世界状态矛盾

### 代码结构

- **状态管理**：`load_state()`, `save_state()`
- **动作处理**：`validate_action()`, `apply_action()`
- **检索系统**：`chunk_story()`, `score_chunk()`, `retrieve_relevant_chunks()`
- **LLM 集成**：`build_chat_prompt()`, `parse_llm_response()`, `explain_action_failure()`

## 许可证

本项目为内部项目。

## 更新日志

### 最新版本

- ✅ 实现智能检索系统（基于关键字匹配）
- ✅ 添加前端聊天界面
- ✅ 实现 Timeline 机制（events 列表）
- ✅ 完善自动化测试（pytest）
- ✅ 优化角色名称检索权重
