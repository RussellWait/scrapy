---
name: "scrapy-code-analysis"
description: "逐行分析 Scrapy 源码文件并写入对应 md 文件。必须在完整读取源码后再写分析，严禁估算行号或编造未读取的代码内容。仅当用户说'skill逐行分析'时调用，其他任何情况都不触发。"
---

# Scrapy 源码逐行分析 Skill

## 强制规则（执行顺序即编号顺序）

### 1. 完整读取 → 再写分析
- 循环 `Read(offset, limit=80-100)` 直到读完全部行，**严禁**只读几十行就写
- **可靠的行号算法**（禁止目测数行，禁止从全文件输出中手动计数）：
  1. 先通读全文件，了解整体结构
  2. 对每个方法/模块的**边界**（如 `def`、`@classmethod`、`class`），使用 `Read(offset=<约数>, limit=5-15)` 精确定位
  3. **只有 `Read` 头部 `Content from line N to line M` 中的 N/M 才是行号事实来源**
  4. 示例：
     ```
     Read(offset=44, limit=15) 返回 "Content from line 44 to line 58"
     → 从输出内容可知：L55=")", L56=(空), L57="@classmethod"
     → 直接使用 L57，而不是从全文件输出中数出"L56"
     ```
  5. 每个模块范围都做一次边界 Read 确认，交叉验证重叠的行号
- 标注行号时**必须逐行对照** `Read` 返回的实际行号，**严禁**估算或编造

### 2. 贴源码 → 再分析
- 每个模块/类/方法分析前，先贴源码（行号用 `L` 前缀标注在每行前，与 `.py` 文件行号一致）
- 代码块语言标注用 `python`，保留语法高亮
- **大类的处理**：类源码块只贴**骨架**（类名 + 方法签名，方法体用 `...` 省略），让读者一眼看到结构。每个方法在独立小节中贴完整体后再逐行分析：

  ````markdown
  ## 模块 X：ClassName（L10-L200）

  ### 类源码（L10-L200，骨架）
  ```python
  L10   class ClassName:
  L11       def method_a(self):
  L12           # 简述
  L13           ...
  L14       def method_b(self):
  L15           # 简述
  L16           ...
  ```

  ### method_a（L11-L13）
  **功能**：...
  #### 源码（L11-L13）
  ```python
  L11      def method_a(self):
  L12          # 完整实现
  L13          return result
  ```
  | 行号 | 代码 | 说明 |
  ...

  ### method_b（L14-L16）
  ...
  ```

### 3. 按模块逐个分析
- 每个模块包含：源码片段、功能说明（逐行）、关键点/陷阱、与其他模块关系
- 目标是让没看过源码的人看完能理解

### 4. 一次性 Write 完全覆盖
- 在内存中拼好**完整内容**（标记 + 全部分析 + 关系图）后，用 `Write` 一次性写入
- 严禁增量追加，旧文件直接覆盖

### 5. 自检行号
- 写完必须 `Read` 回来，对照源码逐条检查行号
- 检查方法：对每个模块的**首行和末行**，用 `Read(offset=<行号>, limit=3)` 验证
  - 示例：如果 md 标注 `@classmethod` 在 L57，则 `Read(offset=55, limit=5)` 看 L57 行内容是否匹配
- 发现错误 → `SearchReplace` 修正 → 再读一遍确认

### 6. 画功能关系图和调用关系图
- **功能关系图**：文件内各模块的继承、组合、数据流
- **调用关系图**：对外接口和被依赖的外部接口
- 用 Mermaid 图，放在 md 文件最后

### 7. 更新 SRC_MAP.txt（位于 `_mytools/SRC_MAP.txt`）
- 每次 `Write` 或 `SearchReplace` 修改 md 文件后，**必须同步更新** SRC_MAP.txt 中对应文件的时间戳
- 将 `文件名.py` 替换为 `文件名.py — YYYY-MM-DD HH:MM`
- 时间必须用**北京时间**（CST, UTC+8），运行 `TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M'` 获取

### 8. 批量分析规则
- 每批 **3 个文件**，自动进入下一批；**超过 500 行的文件**单独处理
- 用 `TodoWrite` 记录已完成文件；上下文快满时给出恢复指令

---

## md 文件格式

### 文件顶部（标记）
```markdown
⬜ **待分析**（AI 写入时始终保持此状态）
✅ **已分析** -- YYYY-MM-DD HH:MM（你运行 mark-done.command 后自动写入）
```

> 切换工具：`_code_analysis/_mytools/mark-done.command`（标记为已分析）`_code_analysis/_mytools/mark-pending.command`（重置为待分析）

### 分析内容（二选一）
**表格格式（适合小段代码）：**
```markdown
| 行号 | 代码 | 说明 |
|------|------|------|
| L1 | `import os` | 引入 os 模块 |
```

**代码块格式（适合大段代码，行号 L 前缀与 .py 一致）：**
```markdown
```python
L30  class SomeClass:
L31      def __init__(self, settings):
L32          pass
```

---

## 触发条件

| 用户说的话 | 是否触发 |
|------------|---------|
| "skill逐行分析" | ✅ 触发 |
| 其他任何情况 | ❌ 不触发 |

---

## 错误示例（严禁）

| 错误 | 说明 |
|------|------|
| 只读文件头就写分析 | Read 只读了前 50 行，却写了 281 行文件的分析 |
| 靠"大概位置"估算行号 | `"第 45-50 行：from_crawler"`，实际在第 43 行 |
| 写完整后不自检 | `Write` 完就结束，没有 Read 回来检查 |
| 从全文件 Read 输出手动数行号 | `Read(offset=1, limit=72)` 的输出有 72 行，手动数出 L56 是 `@classmethod`，但实际在 L57——数漏了某个空行。**必须用分段读来确认边界行号**
