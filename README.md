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
- `POST /chat` - 使用 `supermind-agent-v1` 模型进行 AI 对话

## AI 调用说明

所有 AI 调用都使用 OpenAI SDK，配置如下：
- Base URL: `https://space.ai-builders.com/backend/v1`
- 模型: `supermind-agent-v1`
- 认证: 通过 Bearer Token (从环境变量读取)

## 示例请求

```bash
# 测试 POST /chat
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "你好"}'
```

