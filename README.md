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
- `POST /chat` - 使用 `supermind-agent-v1` 模型进行 AI 对话

## AI 调用说明

所有 AI 调用都使用 OpenAI SDK，配置如下：

- Base URL: `https://space.ai-builders.com/backend/v1`
- 模型: `supermind-agent-v1`
- 认证: 通过 Bearer Token (从环境变量读取)

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

## 示例请求

```bash
# 获取当前世界状态
curl http://localhost:8000/state

# 获取故事内容（前 2000 字符）
curl http://localhost:8000/lore

# 测试 POST /chat
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```
