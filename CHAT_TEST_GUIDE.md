# POST /chat 端点测试指南

## 测试结果

✅ **核心功能测试通过！**

### 已验证功能

1. ✅ **基本聊天流程** - 成功生成动作并执行
2. ✅ **返回格式** - 包含所有必需字段（ok, narration, action_ok, state）
3. ✅ **错误处理** - 缺少 message 时正确返回错误

## 手动测试（curl）

### 测试 1: 基本聊天（生成 move 动作）

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "我要前往洛阳"}'
```

**预期返回：**
```json
{
  "ok": true,
  "narration": "你决定动身前往帝都洛阳...",
  "action_ok": true,
  "state": {
    "time": 1,
    "characters": {
      "player": {
        "location": "luo_yang",
        ...
      }
    }
  }
}
```

### 测试 2: 与角色对话（生成 talk 动作）

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "我要和刘备说话，告诉他我要帮助他"}'
```

**预期：**
- 生成 `talk` 动作
- 如果包含"帮"字，好感度应该增加
- 返回合理的叙述

### 测试 3: 可能导致无效动作的请求

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "我要和已死的角色说话"}'
```

**预期：**
- LLM 可能生成 `talk` 动作
- 动作验证失败（目标已死亡）
- 返回 `action_ok: false`
- 返回合理的失败解释（由 LLM 生成）

### 测试 4: 缺少 message 字段

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**预期返回：**
```json
{
  "ok": false,
  "error": "message 字段是必需的"
}
```

## 自动化测试

### 快速测试

```bash
python3 test_chat_quick.py
```

### 完整测试（需要更长时间，因为 LLM 调用）

```bash
python3 test_chat_endpoint.py
```

## 测试检查清单

- [x] 基本聊天流程工作正常
- [x] 返回格式包含所有必需字段
- [x] 错误处理正确
- [x] LLM 生成的动作符合协议
- [x] 动作验证和应用正常
- [x] 状态正确保存
- [ ] 动作验证失败时的解释（需要更长时间测试）

## 注意事项

1. **超时设置**：LLM 调用可能需要 30-60 秒，测试时请设置足够的超时时间
2. **API Key**：确保已设置 `SUPER_MIND_API_KEY` 或 `AI_BUILDER_TOKEN`
3. **服务运行**：确保服务正在运行：`uvicorn main:app --reload`
4. **状态文件**：测试会修改 `data/state.json`，建议备份

## 预期行为

### 成功场景

1. 用户输入自然语言
2. LLM 生成 `proposed_action` 和 `narration`
3. 动作通过验证
4. 动作被应用，状态更新
5. 返回成功响应

### 失败场景（动作验证失败）

1. 用户输入自然语言
2. LLM 生成 `proposed_action` 和 `narration`
3. 动作验证失败
4. 调用 LLM 生成失败解释
5. 返回失败响应（但 `ok: true`，`action_ok: false`）

## 调试技巧

如果遇到问题，可以：

1. 检查服务日志
2. 查看返回的 `llm_response` 字段（如果解析失败）
3. 检查 `error` 字段了解具体错误
4. 验证 API Key 是否正确设置

