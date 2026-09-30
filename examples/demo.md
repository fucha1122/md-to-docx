# 示例文档：md-to-docx 能力演示

> 本文件用于验证转换器的各类 Markdown 元素，并演示「图由 agent 手绘」的完整链路。
> 运行 `python scripts/md_to_docx.py examples/demo.md --diagrams diagrams/assets`
> 生成 `examples/demo.docx`。
>
> 注意第 7 节的 mermaid 文本与 `diagrams/architecture.py`、`diagrams/pipeline.py`、
> `diagrams/sequence.py` 画的图**一一对应**——这是 skill 的硬约定：md 里第 N 个
> mermaid 块必须与 `diagram_N.png` 内容一致。

---

## 1. 文本与行内格式

这是一段普通正文，用来检查**首行缩进**、**1.5 倍行距**与中文字体。
行内可以出现 **粗体**、*斜体*、`行内代码` 以及[链接](https://example.com)。

#### 1.1 四级标题

四级标题（`####`）以较小字号呈现；本节同时验证这一层级。

## 2. 列表

### 2.1 无序列表

- 第一项：邮件接入
- 第二项：正文理解
  - 子项：意图识别
  - 子项：实体抽取
- 第三项：附件处理

### 2.2 有序列表

1. 收信
2. 分析
3. 规则动作
4. 人工审核

## 3. 表格

表格单元格内同样支持**粗体**与`行内代码`：

| 模块 | 职责 | 状态 |
| --- | --- | --- |
| `mail.fetch` | 增量收信、**幂等**入库 | 已实现 |
| `mail.analyze` | 意图 / 实体 / 摘要 | 已实现 |
| `mail.parseAttachment` | 附件解析与 OCR | 已实现 |
| `mail.extract` | 汇总与复核标记 | 已实现 |

## 4. 引用块

> 预期内的失败用返回值表达，只有真正的意外才抛异常。

## 5. 代码块

围栏代码块按等宽字体（Consolas 9pt）逐行呈现，语言标记不参与排版：

```python
def ingest(mail):
    """幂等入库：uid 已存在则跳过。"""
    if db.exists(uid=mail.uid):
        return "skip"
    return db.insert(mail)
```

```bash
python scripts/md_to_docx.py examples/demo.md --diagrams diagrams/assets
```

## 6. 独立图片

独立图片用 `![alt](路径)` 插入，路径相对本文件解析；下例指向 `../diagrams/assets/diagram_2.png`：

![邮件处理流水线](../diagrams/assets/diagram_2.png)

## 7. Mermaid 流程图

### 7.1 系统总体架构（对应 diagram_1.png）

```mermaid
flowchart TB
  subgraph SRC["邮件源"]
    IMAP["IMAP / POP3 邮箱"]
    GRAPH["Microsoft Graph"]
  end
  subgraph INGEST["接入层"]
    IDLE["IMAP IDLE 实时监听"]
    SCHED["计划拉取调度"]
  end
  subgraph ENGINE["后台处理引擎（Worker 进程）"]
    FETCH["mail.fetch 增量收信"]
    ANALYZE["mail.analyze 正文理解"]
    ATTACH["mail.parseAttachment 附件解析 / OCR"]
    EXTRACT["mail.extract 汇总"]
    ACT["mail.act 规则动作"]
    SEND["mail.send 发信"]
    DELIVER["mail.deliver 外部投递"]
    CLEAN["mail.cleanup 到期清理"]
  end
  subgraph DATA["数据层"]
    PG[("PostgreSQL 18 业务数据 + 任务队列")]
    OBJ[("附件对象存储 本地卷 / S3")]
  end
  subgraph WEB["Web 应用进程（Next.js）"]
    UI["管理后台"]
    REVIEW["人工审核工作台"]
    API["对外开放 API"]
  end
  subgraph EXT["外部系统与模型"]
    BIZ["ERP / CRM / OA"]
    IM["飞书 / 钉钉"]
    LLM["OpenAI 兼容模型"]
  end
  IMAP --> IDLE --> FETCH
  IMAP --> SCHED --> FETCH
  GRAPH --> SCHED --> FETCH
  FETCH --> PG
  FETCH -->|投递任务| ANALYZE
  ANALYZE <--> LLM
  ANALYZE --> ATTACH
  ATTACH <--> LLM
  ATTACH --> EXTRACT --> ACT
  ACT --> SEND
  ACT --> DELIVER --> BIZ
  DELIVER --> IM
  ACT -->|低置信度| REVIEW --> UI
  UI --> PG
  API --> PG
  ATTACH --> OBJ
  CLEAN --> PG
```

### 7.2 邮件处理流水线（对应 diagram_2.png）

```mermaid
flowchart LR
  A["邮件到达"] --> B["mail.fetch 幂等入库"]
  B --> C["mail.analyze 意图 / 实体 / 摘要"]
  C --> D["mail.parseAttachment 逐附件解析"]
  D --> E["mail.extract 汇总与复核标记"]
  E --> F["mail.act 规则引擎"]
  F -->|命中自动回复且达置信门禁| G["发信 / 标准回执"]
  F -->|低置信度| H["人工审核队列"]
  F -->|外部推送| I["Webhook / 飞书 / 钉钉"]
  H -->|人工批准| G
```

### 7.3 邮件收信与分析时序（对应 diagram_3.png）

```mermaid
sequenceDiagram
  participant M as 邮箱（IMAP）
  participant S as 调度器
  participant W as Worker
  participant L as 模型（LLM）
  participant D as 数据库
  M->>S: 新邮件到达（IMAP IDLE）
  S->>W: 投递 mail.fetch
  W->>M: 增量拉取（UID 游标）
  M-->>W: 邮件原文 MIME
  W->>D: 幂等入库
  W->>L: 正文理解
  L-->>W: 意图 / 实体（结构化）
  W->>D: 写入分析结果
  W->>M: 推进 UIDVALIDITY 游标
```

## 8. 收尾

以上元素都能在生成的 Word 中正确呈现；mermaid 图会被替换为
`diagrams/assets/` 下手绘产出的图片，而不是代码文本。
