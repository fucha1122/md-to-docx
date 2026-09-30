---
name: "md-to-docx"
description: "把 Markdown 转成格式化的 Word (.docx)。含 mermaid 图时，由你在读懂图意后手写绘图脚本（工具包 + 自检），产出结构正确的图再嵌入。当用户要 .md 转 .docx、交付 Word 版文档时调用。"
license: Apache-2.0
---

# md-to-docx：Markdown → Word 转换 Skill

把 Markdown 转成可直接交付的 Word 文档，**其中的图由你亲手绘制**——工具只提供绘图原语和自检。

## 为什么图要手绘（先读这段，别走弯路）

本 skill **刻意不做 mermaid 自动渲染**。

自动布局（mermaid 的 dagre 那一类）要解决的是"给定任意图求美观布局"，这是 NP-hard，且它**拿不到语义**：
哪些节点该并排、哪些该分组、哪条是主链路——这些信息在图的**含义**里，不在语法里。
自动算法只能给出"不重叠"的几何结果，结构经常是错的（该并排的被拆开、主链路被拉成对角线）。

而你（agent）的强项是写代码。所以正确姿势是：**你读懂图意 → 显式指定坐标 → 用工具包画 → 跑自检迭代**。
`diagrams/architecture.py`（分层带）、`diagrams/pipeline.py`（主链 + 分叉）、
`diagrams/sequence.py`（时序图）是三个可直接抄的范例，共用同一套默认配色。

## 依赖

```bash
pip install -r requirements.txt      # python-docx, matplotlib
```

## 工作流

### 情况 A：Markdown 里含 ` ```mermaid ` 块

```
① 数一下有几个 mermaid 块，记下顺序
② 对每一块，执行「四步法」写一个 diagrams/<图名>.py，产出 diagrams/assets/diagram_<序号>.png
③ python scripts/md_to_docx.py 输入.md --diagrams diagrams/assets
④ 核验 docx（见下方「成功判据」）
```

> **命名约定（硬性）**：md 里第 N 个 mermaid 块 ↔ `<diagrams 目录>/diagram_N.png`。
> 顺序错位会让图和章节对不上，转换后必须抽查。

### 情况 B：纯文本 Markdown（无图）

直接 `python scripts/md_to_docx.py 输入.md` 即可。

---

## 四步法（画图的标准流程）

### 第 1 步 · 读懂图，先写注释

从 mermaid（或用户描述）提炼三件事，**写进脚本注释再动手**：

- 有哪些节点、各自文字是什么
- 节点怎么分组（mermaid 的 `subgraph` → 用 `band()`）
- 箭头方向与主干链路（哪些是主链、哪些是分支/旁路）

### 第 2 步 · 选布局范式（重要：这一步决定结构对不对）

| 范式 | 适用 | 做法 |
| --- | --- | --- |
| **纵向分层带** | 层次分明的系统架构 | 每条带一个 `band()`，带内节点横排 |
| **横向分区框** | 按业务域并列的模块图 | 每域一个 `band()`，域间用箭头 |
| **竖向主链 + 分叉** | 流程 / 流水线 | 主链竖向排一列，末端向右分结果 |
| **矩阵网格** | 并列的清单式对比 | 行 = 类别，列 = 维度 |
| **时序网格** | 时序图 / 交互时序 | 列 = 参与者（`lifeline()`），行 = 时间（`msg()`） |

选一个范式，**一次性把 0~1 的坐标分配好**，不要边画边想。

### 第 3 步 · 摆节点、连边

```python
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
from diagram_kit import canvas, band, box, arrow, finalize

OUT = os.path.join(HERE, "assets", "diagram_1.png")   # 序号必须对上

def build():
    fig, ax = canvas(11, 8.2, title="系统总体架构")
    band(ax, 0.02, 0.85, 0.98, 0.95, "邮件源")            # 分组容器（虚线框）
    box(ax, 0.24, 0.90, 0.20, 0.06, "IMAP / POP3 邮箱")   # 节点，(x,y) 是中心
    arrow(ax, (0.24, 0.85), (0.24, 0.80), "投递")         # 箭头
    return finalize(fig, ax, OUT)                          # 自检 + 保存

if __name__ == "__main__":
    raise SystemExit(0 if build()["ok"] else 1)
```

`diagram_kit` 原语：

| 原语 | 说明 |
| --- | --- |
| `canvas(w, h, title)` | 新建画布，返回 `(fig, ax)`；坐标用 0~1 |
| `box(ax, x, y, w, h, text, fc=, ec=, bold=)` | 节点；`text` 里的 `\n` 换行 |
| `band(ax, x0, y0, x1, y1, title)` | 分组虚线框（容器，不参与重叠判定） |
| `arrow(ax, p1, p2, label=, rad=, dashed=, double=)` | 箭头；`rad` 调弯曲，`double=True` 双向 |
| `caption(ax, x, y, text)` | 纯文字标注 |
| `icon(ax, x, y, name, size=, color=)` | 图标（Font Awesome Free）。名字查 `assets/fonts/fa-codepoints.json`（1915 个可用） |
| `lifeline(ax, x, y_top, y_bot, name)` | **时序图**：参与者生命线（顶部名称框 + 虚线），返回该列 x |
| `msg(ax, x1, x2, y, text, dashed=)` | **时序图**：同一条消息；`x1 == x2` 画自消息回环 |
| `route_arrow(ax, p1, p2, lane_x, label=)` | 直角绕行箭头，**跨层连线专用**（走侧边通道） |
| `finalize(fig, ax, out)` | **自检 + 保存 + 打印报告** |

**图的默认样式**：「清爽商务」——白卡片 + 中性灰描边（slate）+ 少量强调色（蓝 / 紫）。
色值集中在 `scripts/diagram_kit.py` 顶部常量（`BOX_FC`/`BOX_EC`/`BAND_FC`/`BAND_EC`/
`ACCENT_FC`/`ACCENT_EC`/`ACTOR_FC`/`ARROW_C`/`MUTED` …），**改一处全局生效**；
`diagrams/architecture.py` 的 `PALETTE` 只额外声明逐层强调色。
边线与箭头按 WCAG 非文本对比度 ≥3.0 选取——别为了"清淡"调到看不清。

**分层带布局的四条硬规则**（都是踩坑总结的，务必遵守）：

1. **层名放带外左侧、横排**（用 `caption`），不要用 `band(title=...)` 竖排。
   竖排文字的高度 = **文字长度**，0.09 高的带装不下「Web 应用进程（Next.js）」这类长名，
   会上下溢出、和相邻层的名字叠在一起（实测溢出 2.66 倍）。
2. **带与带之间留 ≥ 0.06 的间隙**，层间箭头就落在间隙里。
   间隙只有 0.02 时箭头长度不到 20pt，几乎看不见，还会和相邻层的箭头粘连。
3. **跨层连线走侧边通道**（`route_arrow(..., lane_x=...)`）。
   直接画斜线会压在中间那些层上；`lane_x` 取带区右侧的空白通道。
4. **同一行相邻节点的中心距 ≥ (w1+w2)/2 + 0.02**。
   `box(w, h)` 的声明尺寸**就是**可见尺寸（圆角所需的内边距已在工具包内部消化），
   所以中心距只比 (w1+w2)/2 大 0.005 时，视觉上就粘在一起、看着像重叠。

### 第 4 步 · 自检迭代（看不到图时的唯一信号）

`finalize` 会打印五项检查：

| 检查 | 触发条件 | 怎么改 |
| --- | --- | --- |
| **文字溢出** | 盒内文字超出盒宽/高（比 > 0.98） | 加宽盒子 / 缩短文字 / 拆两行 |
| **容器标题溢出** | `band()` 的标题超出所属容器 | 标题移到带外（`caption`），或加高容器 |
| **节点重叠** | 两个 `box` 矩形相交 | 拉开坐标 |
| **超出画布** | 坐标越出 0~1 | 往里收 |
| **消息过密** | 时序图相邻消息 y 间距 < 0.042 | 拉开 y 间距 |

反复调到三项全 `PASS` 为止。**只要有一项 FAIL，就不要进入转换步骤。**

---

## 转换

```bash
python scripts/md_to_docx.py 方案.md                                  # 无图场景
python scripts/md_to_docx.py 方案.md --diagrams diagrams/assets       # 有图场景
python scripts/md_to_docx.py 方案.md -o out/方案.docx --title "定制标题"
```

| 参数 | 说明 |
| --- | --- |
| `input` | 输入 `.md` |
| `-o, --output` | 输出 `.docx`（默认与输入同目录同名） |
| `--diagrams` | 手绘图目录（默认 `<输入目录>/diagrams`），按序取 `diagram_1.png` … |
| `--title` | 覆盖 `#` 标题 |

mermaid 块**找不到对应图**时：保留为代码文本 + 打印警告 + 退出码 1（提示你先去画图）。

## 支持的 Markdown 语法

标题 `#`~`######`（`#` 作封面标题；`##` 起每章分页）、段落（自动合并硬换行）、`**粗体**`、
`*斜体*`、`` `行内代码` ``、`[链接](url)`、无序/有序列表、管道表格（Table Grid + 表头底纹）、
`> 引用`、`---` 分隔线、`![alt](路径)` 图片、` ```lang ` 代码块。

## 样式规范

| 元素 | 中文字体 | 西文 | 字号 | 其他 |
| --- | --- | --- | --- | --- |
| 正文 | 宋体 | Times New Roman | 12pt | 1.5 倍行距，首行缩进 0.74cm |
| 封面标题 | 宋体 | Times New Roman | 22pt | 居中加粗 |
| 一级(`##`) | 宋体 | Times New Roman | 22pt | 加粗 + 段前分页 |
| 二级(`###`) | 宋体 | Times New Roman | 16pt | 加粗 |
| 表格 | 宋体 | Times New Roman | 10.5pt | 表头底纹 `#D9E2F3` |
| 代码 | Consolas | Consolas | 9pt | 等宽 |

页面 A4 / 四边 2.54cm。

## 成功判据（转换后必须核验，不要只看 exit code）

1. **图和文本对得上**（最重要）：每个 mermaid 块的节点数，应与对应绘图脚本
   `finalize` 报告里的 `boxes` 数一致。**数量对不上，说明图画漏了或画多了**——
   图比文本多、比文本少，都是缺陷。
2. **图数对得上**：`内嵌图片数` == md 里 mermaid 块数 + 其它独立图片数。
3. **没有代码残留**：正文里不应出现 ` ``` ` 或 `flowchart` 字样。
4. **结构没塌**：抽查首段、一张表、一处列表的文字与层级。

```bash
python - <<'PY'
from docx import Document
d = Document("方案.docx")
print("段落", len(d.paragraphs), "表格", len(d.tables), "图片", len(d.inline_shapes))
txt = "\n".join(p.text for p in d.paragraphs)
print("残留代码:", ("```" in txt) or ("flowchart" in txt))
PY
```

若你有视觉能力，**再看一眼生成的图**确认观感；没有的话，以 `finalize` 的自检报告为准。

## 目录结构

```
md-to-docx/
├── SKILL.md                 本文件（操作手册）
├── README.md                项目说明
├── requirements.txt
├── assets/fonts/            图标字体（Font Awesome Free，见该目录 README 的许可说明）
├── scripts/
│   ├── md_to_docx.py        md → docx（CLI）
│   └── diagram_kit.py       绘图原语 + 自检
├── diagrams/
│   ├── _template.py         新图骨架（复制它开始画）
│   ├── _style_preview.py    样式候选对照（历史存档；当前默认 = style_2_clean）
│   ├── architecture.py      范例 A：纵向分层带
│   ├── pipeline.py          范例 B：竖向主链 + 分叉
│   ├── sequence.py          范例 C：时序图（列 = 参与者，行 = 时间）
│   └── assets/              产出的 PNG（diagram_1.png …）
└── examples/
    └── demo.md              含各类语法的示例输入
```

## 已知限制

- 表格仅处理标准管道表；单元格内不支持嵌套表格/图片。
- 不支持脚注、目录(TOC)、参考文献。
- 图完全靠手写坐标，**没有自动布局兜底**——这是刻意的取舍，换取结构正确。
- **时序图有专用原语**（`lifeline` / `msg`），见范例 C；`gantt` / `classDiagram` 等仍需自行用原语表达。
- 时序图的生命线是长竖线，不参与「节点重叠」判定；消息只检查**相邻 y 间距**，不检查标签的横向碰撞。
