# 状态管理功能验收指南

## 验收目标

1. ✅ **修改 state.json 后，GET /state 能反映出来**
2. ✅ **保存写入不会把 JSON 写坏（格式正确）**

## 验收方法

### 前置准备

1. 安装依赖并启动服务：
```bash
# 创建虚拟环境（如果需要）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt requests

# 启动服务
uvicorn main:app --reload
```

### 验收测试 1: 修改 state.json 后能正确读取

**步骤：**

1. **查看当前状态**（在浏览器或终端）：
```bash
curl http://localhost:8000/state
```

2. **直接修改 `data/state.json` 文件**：
   - 打开 `data/state.json`
   - 修改一个值，例如：
     - 将 `time` 从 `0` 改为 `100`
     - 或将某个角色的 `affinity_to_player` 改为其他值

3. **再次查询状态**：
```bash
curl http://localhost:8000/state
```

4. **验证**：
   - ✅ 返回的 JSON 应该包含你刚才修改的值
   - ✅ 说明 `load_state()` 能正确读取文件修改

**示例：**

```bash
# 1. 查看原始状态
$ curl http://localhost:8000/state
{"time":0,"characters":{"liu_bei":{...},"guan_yu":{"affinity_to_player":80},...}}

# 2. 修改 data/state.json，将 time 改为 100

# 3. 再次查询
$ curl http://localhost:8000/state
{"time":100,"characters":{...}}  # ✅ 应该显示 time=100
```

### 验收测试 2: JSON 格式正确（不会写坏文件）

**步骤：**

1. **使用 Python 交互式测试**：
```bash
python3
```

2. **在 Python 中执行**：
```python
import sys
sys.path.insert(0, '.')
from main import load_state, save_state
import json
from pathlib import Path

# 测试 1: 保存一个复杂状态
test_state = {
    "time": 999,
    "characters": {
        "test_char": {
            "alive": True,
            "location": "test_loc",
            "affinity_to_player": -50
        }
    },
    "items": {
        "test_item": {
            "owner": "test_char"
        }
    }
}

# 保存
save_state(test_state)
print("✅ save_state() 执行成功")

# 验证文件格式
state_file = Path("data/state.json")
with open(state_file, "r") as f:
    content = f.read()
    print(f"文件内容长度: {len(content)} 字符")

# 尝试解析 JSON
try:
    parsed = json.loads(content)
    print("✅ JSON 格式正确，可以解析")
    print(f"✅ 内容匹配: time={parsed.get('time')}")
except json.JSONDecodeError as e:
    print(f"❌ JSON 格式错误: {e}")
    print(f"文件内容:\n{content[:200]}")
```

3. **验证原子写入**（检查临时文件是否被清理）：
```python
from pathlib import Path
temp_file = Path("data/state.json.tmp")
if temp_file.exists():
    print("❌ 临时文件未被清理")
else:
    print("✅ 临时文件已正确清理")
```

4. **验证文件完整性**：
```python
# 多次保存，确保不会损坏
for i in range(5):
    state = load_state()
    state["time"] = i
    save_state(state)
    # 验证可以读取
    loaded = load_state()
    assert loaded["time"] == i, f"第 {i} 次保存失败"
print("✅ 连续 5 次保存/读取都成功，文件未损坏")
```

### 验收测试 3: API 端点测试（完整流程）

**步骤：**

1. **启动服务**（如果还没启动）：
```bash
uvicorn main:app --reload
```

2. **修改 state.json**：
   - 手动编辑 `data/state.json`
   - 例如：`"time": 0` → `"time": 42`

3. **通过 API 查询**：
```bash
curl http://localhost:8000/state | python3 -m json.tool
```

4. **验证返回的 JSON**：
   - ✅ 格式正确（可以被 `json.tool` 格式化）
   - ✅ 包含你修改的值
   - ✅ 所有字段完整

### 验收测试 4: 边界情况测试

**测试文件损坏恢复：**

```python
import json
from pathlib import Path

# 1. 故意写坏文件
state_file = Path("data/state.json")
with open(state_file, "w") as f:
    f.write("{ invalid json }")

# 2. 尝试读取（应该自动恢复）
from main import load_state
state = load_state()
print(f"✅ 损坏文件已恢复，返回默认状态: {state}")

# 3. 验证文件已被修复
with open(state_file, "r") as f:
    content = f.read()
    parsed = json.loads(content)  # 应该可以解析
    print("✅ 文件已被修复为有效 JSON")
```

## 快速验收脚本

运行自动化测试（需要先安装依赖）：

```bash
python3 test_state_validation.py
```

## 验收检查清单

- [ ] 修改 `data/state.json` 后，`GET /state` 返回新值
- [ ] `save_state()` 写入的 JSON 格式正确，可以被 `json.loads()` 解析
- [ ] 保存后文件格式美观（有缩进，UTF-8 编码）
- [ ] 临时文件（`.tmp`）在保存后被清理
- [ ] 文件损坏时，`load_state()` 能自动恢复默认状态
- [ ] 连续多次保存/读取不会损坏文件
- [ ] API 端点返回的 JSON 格式正确

## 常见问题

**Q: 如果测试失败怎么办？**
A: 检查：
1. 服务是否正在运行
2. `data/state.json` 文件权限是否正确
3. Python 环境是否正确安装依赖

**Q: 如何验证原子写入？**
A: 原子写入的验证：
- 保存后检查 `data/state.json.tmp` 不应该存在
- 如果写入过程中断，原文件应该保持完整

