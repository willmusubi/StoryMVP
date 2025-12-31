# 动作协议系统测试指南

## 测试结果

✅ 所有测试通过！

## 测试覆盖

### 1. Action Schema 测试
- ✅ 所有动作类型（move, talk, give_item, attack, rescue）结构正确
- ✅ 必需字段验证
- ✅ 可选字段处理

### 2. validate_action() 验证规则测试
- ✅ move 必须提供 to_location
- ✅ give_item 必须提供 item 和 target
- ✅ give_item 物品所有权验证
- ✅ 不能对死亡角色执行交互
- ✅ attack/rescue 需要 target 且存活

### 3. apply_action() 动作效果测试
- ✅ move 更新位置
- ✅ give_item 更新物品拥有者
- ✅ talk 影响好感度（帮助性对话 +10）
- ✅ time 自动递增

### 4. POST /act API 端点测试
- ✅ 有效动作成功执行
- ✅ 无效动作正确拒绝
- ✅ 状态正确保存

## 手动测试示例

### 测试 move 动作

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "move",
    "actor": "player",
    "to_location": "luo_yang",
    "intent": "前往洛阳"
  }'
```

**预期结果：**
- `ok: true`
- `state.characters.player.location` 变为 `"luo_yang"`
- `state.time` 增加 1

### 测试 talk 动作（增加好感度）

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "talk",
    "target": "liu_bei",
    "intent": "我要帮助你"
  }'
```

**预期结果：**
- `ok: true`
- `state.characters.liu_bei.affinity_to_player` 增加 10（如果包含"帮"字）

### 测试 talk 动作（普通对话）

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "talk",
    "target": "liu_bei",
    "intent": "你好"
  }'
```

**预期结果：**
- `ok: true`
- `state.characters.liu_bei.affinity_to_player` 保持不变

### 测试 give_item 动作

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "give_item",
    "actor": "player",
    "target": "liu_bei",
    "item": "sword_1",
    "intent": "把剑给你"
  }'
```

**预期结果：**
- `ok: true`
- `state.items.sword_1.owner` 变为 `"liu_bei"`

### 测试 attack 动作

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "attack",
    "target": "enemy_1",
    "intent": "攻击敌人"
  }'
```

**预期结果：**
- `ok: true`
- `state.characters.enemy_1.affinity_to_player` 减少 20

### 测试 rescue 动作

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "rescue",
    "target": "liu_bei",
    "intent": "救援刘备"
  }'
```

**预期结果：**
- `ok: true`
- `state.characters.liu_bei.affinity_to_player` 增加 30

## 错误场景测试

### 测试无效的 move（缺少 to_location）

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "move",
    "intent": "移动"
  }'
```

**预期结果：**
- `ok: false`
- `error: "move 动作必须提供 to_location"`

### 测试无效的 give_item（物品不属于 actor）

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "give_item",
    "actor": "player",
    "target": "liu_bei",
    "item": "sword_2",
    "intent": "给物品"
  }'
```

**预期结果：**
- `ok: false`
- `error: "物品 sword_2 不属于 player，当前拥有者: liu_bei"`

### 测试对死亡角色执行 talk

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "talk",
    "target": "dead_char",
    "intent": "说话"
  }'
```

**预期结果：**
- `ok: false`
- `error: "目标角色 dead_char 已死亡，无法执行 talk"`

## 运行自动化测试

```bash
# 运行测试脚本
python3 test_action_validation.py
```

## 测试检查清单

- [x] Action Schema 定义正确
- [x] validate_action() 实现所有验证规则
- [x] apply_action() 实现所有动作效果
- [x] POST /act 端点正确处理请求
- [x] 状态正确保存到文件
- [x] 错误场景正确处理
- [x] 时间自动递增
- [x] 好感度变化正确

## 注意事项

1. 测试前确保服务正在运行：`uvicorn main:app --reload`
2. 测试会修改 `data/state.json`，建议备份
3. 某些测试需要特定的状态数据，确保状态文件包含必要的角色和物品

