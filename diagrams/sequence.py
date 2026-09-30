# -*- coding: utf-8 -*-
"""范例 C：时序图 —— 一次邮件收信与分析的调用时序。

布局思路（时序图专用）：
  列 = 参与者（等距排布），行 = 时间（自上而下）。
  先排好参与者的 x，再按"谁在什么时候跟谁说话"自上而下排 y。
  返回/异步消息用虚线（dashed=True），同步调用用实线。

改这个文件时：加消息就同时下调后续 y，保持相邻间距 > 0.042（否则自检会报"消息过密"）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from diagram_kit import canvas, finalize, lifeline, msg  # noqa: E402

OUT = os.path.join(HERE, "assets", "diagram_3.png")


def build():
    fig, ax = canvas(11, 7.4, title="邮件收信与分析时序")

    # 列：参与者
    x_mail = lifeline(ax, 0.10, 0.90, 0.20, "邮箱（IMAP）")
    x_sched = lifeline(ax, 0.30, 0.90, 0.20, "调度器")
    x_worker = lifeline(ax, 0.50, 0.90, 0.20, "Worker")
    x_model = lifeline(ax, 0.70, 0.90, 0.20, "模型（LLM）")
    x_db = lifeline(ax, 0.90, 0.90, 0.20, "数据库")

    # 行：消息，自上而下
    row = 0.80
    step = 0.075
    msg(ax, x_mail, x_sched, row, "新邮件到达（IMAP IDLE）")
    msg(ax, x_sched, x_worker, row - step, "投递 mail.fetch")
    msg(ax, x_worker, x_mail, row - step * 2, "增量拉取（UID 游标）")
    msg(ax, x_mail, x_worker, row - step * 3, "邮件原文 MIME", dashed=True)
    msg(ax, x_worker, x_db, row - step * 4, "幂等入库")
    msg(ax, x_worker, x_model, row - step * 5, "正文理解")
    msg(ax, x_model, x_worker, row - step * 6, "意图 / 实体（结构化）", dashed=True)
    msg(ax, x_worker, x_db, row - step * 7, "写入分析结果")
    msg(ax, x_worker, x_mail, row - step * 8, "推进 UIDVALIDITY 游标")

    return finalize(fig, ax, OUT)


if __name__ == "__main__":
    raise SystemExit(0 if build()["ok"] else 1)
