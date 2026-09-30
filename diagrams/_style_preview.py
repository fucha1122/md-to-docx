# -*- coding: utf-8 -*-
"""生成总体架构图的**样式候选**，供人工挑选（历史存档）。

**样式已定稿**：采用 `style_2_clean`（清爽商务），并已下沉到
`scripts/diagram_kit.py` 的默认配色常量——`architecture.draw()` 传 `None`
拿到的就是它，其余示例（pipeline / sequence / _template）也共用同一套默认。
换样式只需改 `diagram_kit.py` 一处；本文件保留作对照 / 回归。

坐标逻辑复用 `architecture.draw()`，只换调色板。产出：

    assets/preview/style_1_original.png   改动前的原样式（蓝底蓝边）
    assets/preview/style_2_clean.png      清爽商务（= 当前默认）
    assets/preview/style_3_bands.png      分区色相（每层一个低饱和色相）

色值取自 Tailwind v3.4 官方色阶；配色原则参考 IBM 架构可视化规范
（固定调色板标注技术域、深色描边 + 白/浅色填充）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))

import architecture  # noqa: E402
from diagram_kit import canvas, finalize  # noqa: E402

PREVIEW_DIR = os.path.join(HERE, "assets", "preview")

# 改动前的原样式：一片蓝、无层次、无图标、粗箭头
PALETTE_1_ORIGINAL = {
    "band_fc": "#f4f7fb", "band_ec": "#afbdd1",
    "node_fc": "#e8f1fb", "node_ec": "#4177b8",
    "arrow": "#3d5a80", "label": "#4a5a75", "note": "#5a5a5a",
    "band_node": {"data": ("#fdf0e3", "#d99857")},   # amber 强调
    "icons": False, "arrow_lw": 1.15, "arrow_head": 11,
}

# 分区色相：每层一个 Tailwind 低饱和色族（50 底 / 500 边，保证边线可辨）
PALETTE_3_BANDS = {
    "band_fc": "#f8fafc", "band_ec": "#cbd5e1",
    "node_fc": "#ffffff", "node_ec": "#64748b",
    "arrow": "#64748b", "label": "#334155", "note": "#64748b",
    "band_node": {
        "mail":   ("#f0f9ff", "#0284c7"),   # sky-50 / sky-600
        "ingest": ("#ecfeff", "#0891b2"),   # cyan-50 / cyan-600
        "engine": ("#eff6ff", "#2563eb"),   # blue-50 / blue-600
        "data":   ("#f5f3ff", "#7c3aed"),   # violet-50 / violet-600
        "web":    ("#ecfdf5", "#059669"),   # emerald-50 / emerald-600
        "ext":    ("#fffbeb", "#d97706"),   # amber-50 / amber-600
    },
}


def render(name, palette):
    fig, ax = canvas(12.6, 8.6, title="系统总体架构")
    architecture.draw(ax, palette)
    return finalize(fig, ax, os.path.join(PREVIEW_DIR, name))


if __name__ == "__main__":
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    results = {
        "style_1_original.png": render("style_1_original.png", PALETTE_1_ORIGINAL),
        "style_2_clean.png": render("style_2_clean.png", None),          # 默认调色板
        "style_3_bands.png": render("style_3_bands.png", PALETTE_3_BANDS),
    }
    print()
    for name, rep in results.items():
        print(f"  {name}: {'PASS' if rep['ok'] else 'FAIL'}  (节点 {rep['boxes']})")
    raise SystemExit(0 if all(r["ok"] for r in results.values()) else 1)
