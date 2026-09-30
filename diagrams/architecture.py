# -*- coding: utf-8 -*-
"""范例 A：系统总体架构 —— 对应 Markdown 中**第 1 个** mermaid 块。

布局思路（语义驱动，不是自动布局）：
  纵向排 6 条「分层带」，体现自外而内的层次：
    邮件源 → 接入层 → 后台处理引擎 → 数据层 → Web 应用 → 外部系统与模型

  四条硬规则（都是踩过坑总结的）：
  1. **层名放带外左侧、横排**（`caption`）。竖排标题的高度等于文字长度，
     0.09 高的带根本装不下「Web 应用进程（Next.js）」这种长名——曾导致字体重叠。
  2. **带与带之间留 0.062 的间隙**，层间箭头就落在间隙里；间隙太小时箭头只有十几个
     pt，几乎看不见，还会上下粘连。
  3. **跨层连线走右侧通道**（`route_arrow`，lane_x），不要直接画斜线——
     斜线会压在中间那些层上。
  4. **同一行相邻节点的中心距 ≥ (w1+w2)/2 + 0.02**。`box(w,h)` 的声明尺寸就是可见尺寸，
     间距太小时视觉上会粘在一起、看着像重叠。

配色与坐标**分离**：`draw(ax, palette)` 只认调色板，换个 palette 就能出不同风格
（`_style_preview.py` 用它生成备选样式对比）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from diagram_kit import (ARROW_C, BAND_EC, BAND_FC, BOX_EC, BOX_FC, GROUP_C,  # noqa: E402
                         arrow, band, box, canvas, caption, finalize, icon,
                         route_arrow)

OUT = os.path.join(HERE, "assets", "diagram_1.png")

BG_X0, BG_X1 = 0.160, 0.790          # 带区左右边界
ICON_X = 0.026                       # 层图标（带外左侧）
LABEL_X = 0.052                      # 层名放在带外左侧
LANE_REVIEW, LANE_DELIVER = 0.830, 0.900   # 右侧两条跨层通道

# ---------------------------------------------------------------- 坐标表
# (层键, 层名, 带下沿, 带上沿, [(行 y, [(节点 x, 文字, 宽), ...]), ...])
BANDS = [
    ("mail", "邮件源", 0.878, 0.960, [
        (0.919, [(0.360, "IMAP / POP3 邮箱", 0.200), (0.590, "Microsoft Graph", 0.200)]),
    ]),
    ("ingest", "接入层", 0.734, 0.816, [
        (0.775, [(0.360, "IMAP IDLE 实时监听", 0.200), (0.590, "计划拉取调度", 0.200)]),
    ]),
    ("engine", "处理引擎\n（Worker 进程）", 0.457, 0.672, [
        (0.620, [(0.238, "mail.fetch\n增量收信", 0.138),
                 (0.396, "mail.analyze\n正文理解", 0.138),
                 (0.554, "mail.parseAttachment\n附件解析 / OCR", 0.138),
                 (0.712, "mail.extract\n汇总", 0.138)]),
        (0.509, [(0.238, "mail.act\n规则动作", 0.138),
                 (0.396, "mail.send\n发信", 0.138),
                 (0.554, "mail.deliver\n外部投递", 0.138),
                 (0.712, "mail.cleanup\n到期清理", 0.138)]),
    ]),
    ("data", "数据层", 0.313, 0.395, [
        (0.354, [(0.320, "PostgreSQL 18\n（业务数据 + 任务队列）", 0.280),
                 (0.630, "附件对象存储\n（本地卷 / S3）", 0.280)]),
    ]),
    ("web", "Web 应用\n（Next.js）", 0.169, 0.251, [
        (0.210, [(0.265, "管理后台", 0.180), (0.475, "人工审核工作台", 0.180),
                 (0.685, "对外开放 API", 0.180)]),
    ]),
    ("ext", "外部系统\n与模型", 0.025, 0.107, [
        (0.066, [(0.265, "ERP / CRM / OA", 0.180), (0.475, "飞书 / 钉钉", 0.180),
                 (0.685, "OpenAI 兼容模型", 0.180)]),
    ]),
]

# 层图标（名字见 assets/fonts/fa-codepoints.json；字体缺失时自动降级为不画）
BAND_ICONS = {
    "mail": "envelope", "ingest": "tower-broadcast", "engine": "microchip",
    "data": "database", "web": "window-restore", "ext": "cloud",
}

# 默认调色板：直接复用 diagram_kit 的默认样式（清爽商务），只补两层强调色。
# 这样「总体架构图」与其余示例共用同一套配色——全局换样式只需改 diagram_kit 一处。
PALETTE = {
    "band_fc": BAND_FC, "band_ec": BAND_EC,              # slate-50 / slate-300
    "node_fc": BOX_FC, "node_ec": BOX_EC,                # white / slate-500
    "arrow": ARROW_C,                                    # slate-500
    "label": GROUP_C,                                    # slate-700
    "note": ARROW_C,                                     # slate-500
    "band_node": {                                       # 逐层强调（可选）
        "engine": ("#EFF6FF", "#3B82F6"),                # blue-50 / blue-500
        "data": ("#F5F3FF", "#8B5CF6"),                  # violet-50 / violet-500
    },
}


def draw(ax, palette=None):
    """按调色板画图。坐标是固定的，只有颜色随 palette 变。"""
    P = {**PALETTE, **(palette or {})}
    per = P.get("band_node", {})

    # 带 + 层图标 + 层名 + 带内节点
    for key, name, y0, y1, rows in BANDS:
        band(ax, BG_X0, y0, BG_X1, y1, fc=P["band_fc"], ec=P["band_ec"])
        fc, ec = per.get(key, (P["node_fc"], P["node_ec"]))
        cy = (y0 + y1) / 2
        if P.get("icons", True):
            icon(ax, ICON_X, cy, BAND_ICONS.get(key, ""), size=13, color=ec)
        caption(ax, LABEL_X, cy, name, ha="left", va="center",
                fontweight="bold", color=P["label"])
        for y, nodes in rows:
            for x, text, w in nodes:
                box(ax, x, y, w, 0.058, text, fc=fc, ec=ec, fs=9.0)

    # 层间主干箭头（落在带间隙里）
    A = {"color": P["arrow"], "lw": P.get("arrow_lw", 1.0), "head": P.get("arrow_head", 12)}
    for x in (0.360, 0.590):
        arrow(ax, (x, 0.878), (x, 0.816), **A)
        arrow(ax, (x, 0.734), (x, 0.672), **A)
    arrow(ax, (0.410, 0.457), (0.410, 0.395), **A)
    arrow(ax, (0.630, 0.395), (0.630, 0.457), dashed=True, **A)
    arrow(ax, (0.360, 0.313), (0.360, 0.251), **A)
    arrow(ax, (0.590, 0.251), (0.590, 0.313), dashed=True, **A)
    arrow(ax, (0.410, 0.169), (0.410, 0.107), dashed=True, **A)

    for x, y, t in ((0.425, 0.426, "入库 / 查询"), (0.375, 0.282, "读写"),
                    (0.425, 0.138, "发信 / 推送")):
        caption(ax, x, y, t, ha="left", va="center", fs=8.0, color=P["note"])

    # 跨层连线走右侧通道
    route_arrow(ax, (BG_X1, 0.509), (BG_X1, 0.210), LANE_REVIEW,
                label="→ 审核台", fs=8.0, color=P["arrow"])
    route_arrow(ax, (BG_X1, 0.620), (BG_X1, 0.066), LANE_DELIVER,
                label="→ 外部投递", fs=8.0, color=P["arrow"])


def build(out=None, palette=None):
    fig, ax = canvas(12.6, 8.6, title="系统总体架构")
    draw(ax, palette)
    return finalize(fig, ax, out or OUT)


if __name__ == "__main__":
    raise SystemExit(0 if build()["ok"] else 1)
