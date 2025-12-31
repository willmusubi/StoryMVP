# curl 测试示例

## 测试结果

✅ 所有三个测试场景全部通过！

## 测试场景 1: move 能更新地点

### curl 命令

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

### 预期结果

```json
{
  "ok": true,
  "state": {
    "time": 1,
    "characters": {
      "player": {
        "alive": true,
        "location": "luo_yang",  // ✅ 位置已更新
        "affinity_to_player": 100
      }
    },
    "items": {}
  }
}
```

### 验证要点

- ✅ `ok: true`
- ✅ `state.characters.player.location` 变为 `"luo_yang"`
- ✅ `state.time` 增加 1

---

## 测试场景 2: give_item 在不拥有时会被拒绝，并返回 reason

### curl 命令

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "give_item",
    "actor": "player",
    "target": "guan_yu",
    "item": "sword_1",
    "intent": "把剑给你"
  }'
```

**注意：** 需要先确保 `sword_1` 不属于 `player`（例如属于 `liu_bei`）

### 预期结果

```json
{
  "ok": false,
  "error": "物品 sword_1 不属于 player，当前拥有者: liu_bei",  // ✅ 返回明确的错误原因
  "state": {
    // 当前状态（未改变）
  }
}
```

### 验证要点

- ✅ `ok: false`
- ✅ `error` 字段包含明确的拒绝原因
- ✅ 错误信息说明物品所有权问题
- ✅ `state` 未改变（动作未执行）

---

## 测试场景 3: dead 角色不能被 talk/rescue

### 3.1 测试 talk 死亡角色

#### curl 命令

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "talk",
    "target": "dead_char",
    "intent": "说话"
  }'
```

**注意：** 需要先确保 `dead_char` 的 `alive: false`

#### 预期结果

```json
{
  "ok": false,
  "error": "目标角色 dead_char 已死亡，无法执行 talk",  // ✅ 返回明确的错误原因
  "state": {
    // 当前状态（未改变）
  }
}
```

### 3.2 测试 rescue 死亡角色

#### curl 命令

```bash
curl -X POST "http://localhost:8000/act" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "rescue",
    "target": "dead_char",
    "intent": "救援"
  }'
```

#### 预期结果

```json
{
  "ok": false,
  "error": "目标角色 dead_char 已死亡，无法执行 rescue",  // ✅ 返回明确的错误原因
  "state": {
    // 当前状态（未改变）
  }
}
```

### 验证要点

- ✅ `ok: false`
- ✅ `error` 字段包含明确的拒绝原因
- ✅ 错误信息说明角色已死亡
- ✅ `state` 未改变（动作未执行）

---

## 准备测试状态

如果需要准备特定的测试状态，可以使用以下命令：

### 准备状态（包含死亡角色和不属于 player 的物品）

```bash
# 先获取当前状态
curl http://localhost:8000/state > current_state.json

# 手动编辑 current_state.json，添加：
# - dead_char 角色（alive: false）
# - sword_1 物品（owner: "liu_bei"）

# 然后直接修改 data/state.json 文件
```

或者使用 Python 脚本准备：

```python
import json
from pathlib import Path

state_file = Path("data/state.json")
state = {
    "time": 0,
    "characters": {
        "player": {
            "alive": True,
            "location": "xu_zhou",
            "affinity_to_player": 100
        },
        "dead_char": {
            "alive": False,  # 死亡角色
            "location": "grave",
            "affinity_to_player": 0
        },
        "liu_bei": {
            "alive": True,
            "location": "xu_zhou",
            "affinity_to_player": 50
        }
    },
    "items": {
        "sword_1": {
            "owner": "liu_bei"  # 不属于 player
        }
    }
}

with open(state_file, "w", encoding="utf-8") as f:
    json.dump(state, f, ensure_ascii=False, indent=2)
```

---

## 自动化测试

运行自动化测试脚本：

```bash
python3 test_specific_scenarios.py
```

---

## 测试检查清单

- [x] move 能更新地点
- [x] give_item 在不拥有时会被拒绝
- [x] give_item 返回明确的错误原因
- [x] dead 角色不能被 talk
- [x] dead 角色不能被 rescue
- [x] 所有错误都返回明确的 reason/error

---

## 注意事项

1. 确保服务正在运行：`uvicorn main:app --reload`
2. 测试会修改 `data/state.json`，建议备份
3. 某些测试需要特定的状态数据，确保状态文件包含必要的角色和物品

