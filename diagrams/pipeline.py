# -*- coding: utf-8 -*-
"""范例 B：邮件处理流水线 —— 对应 Markdown 中**第 2 个** mermaid 块。

布局思路：
  6 个阶段做**竖向主链**（竖向比横向更适合 A4 竖版页面，且阶段顺序一目了然）；
  主链末端（mail.act）向右分叉出 3 个结果分支，其中「人工审核队列」获批后再汇入「发信」。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from diagram_kit import ACCENT_EC, ACCENT_FC, arrow, box, canvas, finalize  # noqa: E402

OUT = os.path.join(HERE, "assets", "diagram_2.png")


def build():
    fig, ax = canvas(9, 7.6, title="邮件处理流水线")

    w, h = 0.36, 0.075
    cx = 0.30
    ys = [0.905, 0.780, 0.655, 0.530, 0.405, 0.280]
    steps = [
        "邮件到达",
        "mail.fetch　幂等入库",
        "mail.analyze　意图 / 实体 / 摘要",
        "mail.parseAttachment　逐附件解析",
        "mail.extract　汇总与复核标记",
        "mail.act　规则引擎",
    ]
    for y, t in zip(ys, steps):
        box(ax, cx, y, w, h, t, bold=(t == "邮件到达"))
    for i in range(len(ys) - 1):
        arrow(ax, (cx, ys[i] - h / 2), (cx, ys[i + 1] + h / 2))

    bx = 0.76
    by = {"g": 0.360, "h": 0.235, "i": 0.110}
    box(ax, bx, by["g"], 0.38, h, "发信 / 标准回执", fc=ACCENT_FC, ec=ACCENT_EC)
    box(ax, bx, by["h"], 0.38, h, "人工审核队列")
    box(ax, bx, by["i"], 0.38, h, "Webhook / 飞书 / 钉钉")

    fx, fy = cx + w / 2, ys[5]
    arrow(ax, (fx, fy + 0.02), (bx - 0.19, by["g"]), label="命中自动回复且达置信门禁", rad=0.12)
    arrow(ax, (fx, fy), (bx - 0.19, by["h"]), label="低置信度")
    arrow(ax, (fx, fy - 0.02), (bx - 0.19, by["i"]), label="外部推送", rad=-0.12)
    arrow(ax, (bx, by["h"] + h / 2), (bx, by["g"] - h / 2), label="人工批准")

    return finalize(fig, ax, OUT)


if __name__ == "__main__":
    raise SystemExit(0 if build()["ok"] else 1)
