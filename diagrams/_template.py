# -*- coding: utf-8 -*-
"""图模板 —— 复制本文件为 <图名>.py 后按下面的四步填写。

用法：
    cp diagrams/_template.py diagrams/<图名>.py
    # 编辑 diagrams/<图名>.py
    python diagrams/<图名>.py        # 打印自检报告并产出 PNG

=== 四步法 ===

第 1 步 · 读懂图
    从 mermaid（或用户描述）里提炼三件事：
      · 有哪些节点、每个节点的文字
      · 节点之间怎么分组（对应 subgraph → 用 band()）
      · 箭头方向与主干链路（哪些是主链、哪些是分支/旁路）
    **先把这三点写成注释**，再动坐标——布局是语义决策，不是几何随机。

第 2 步 · 选布局范式
    纵向分层带     层次分明的系统架构（邮件源→接入→处理→存储→应用）
    横向分区框     按业务域并列的模块图
    竖向主链+分叉  流程/流水线（阶段顺序执行，末端分结果）
    矩阵网格       并列的清单式对比
    —— 选一个范式，再按它分配 0~1 的坐标；不要边画边想。

第 3 步 · 摆节点、连边
    band(ax, x0, y0, x1, y1, "分组名")          分组容器（虚线框）
    box(ax, x, y, w, h, "文字", bold=False)     节点，x/y 是**中心**坐标
    icon(ax, x, y, "database")                  图标（可用名见 assets/fonts/fa-codepoints.json）
    arrow(ax, (x1, y1), (x2, y2), "标签")       箭头，坐标取节点边缘
    文字要换行就写 "第一行\\n第二行"。

第 4 步 · 自检迭代（关键）
    跑脚本，看 finalize 打印的三项检查：
      文字溢出  → 加宽/加高盒子，或缩短文字、拆成两行
      节点重叠  → 拉开坐标
      超出画布  → 往里收坐标
    反复调到三项全 PASS。**看不到图时，这就是唯一的迭代信号。**

配色默认就是「清爽商务」（白卡片 + 中性灰描边 + 少量强调色），无需手写色值；
要换样式改 scripts/diagram_kit.py 顶部常量，或调用时传 fc=/ec=/color= 单项覆盖。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

from diagram_kit import arrow, band, box, canvas, finalize  # noqa: E402

# 输出文件名必须匹配它在 Markdown 里是第几个 mermaid 块：
#   第 1 个 → diagram_1.png    第 2 个 → diagram_2.png    以此类推
OUT = os.path.join(HERE, "assets", "diagram_N.png")


def build():
    fig, ax = canvas(11, 8, title="图标题")

    # ---- 第 2 步：按选定的布局范式铺坐标 ----
    # band(ax, 0.02, 0.80, 0.98, 0.95, "分组 A")
    # box(ax, 0.25, 0.88, 0.20, 0.06, "节点 1")
    # box(ax, 0.55, 0.88, 0.20, 0.06, "节点 2")

    # ---- 第 3 步：连边 ----
    # arrow(ax, (0.25, 0.85), (0.55, 0.85), "关系")

    return finalize(fig, ax, OUT)


if __name__ == "__main__":
    raise SystemExit(0 if build()["ok"] else 1)
