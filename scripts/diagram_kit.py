# -*- coding: utf-8 -*-
"""diagram_kit —— 手绘流程图 / 时序图工具包。

设计立场：**不做自动布局**。自动布局（dagre 那一类）拿不到语义信息，产出的结构
经常是错的（该并排的被拆开、该分组的被拆散、主链路被拉成对角线）。
正确的做法是：由 agent 读懂图的语义后，**显式指定每个节点的坐标**，用本工具包绘制。

坐标统一用 0~1 的 figure 坐标（左下为原点，y 向上），便于排版与阅读。

两类图的画法::

    # ① 流程图 / 架构图
    from diagram_kit import canvas, band, box, arrow, caption, finalize
    fig, ax = canvas(11.8, 8.6, title="系统总体架构")
    caption(ax, 0.008, 0.919, "邮件源", ha="left", va="center")   # 层名放带外
    band(ax, 0.160, 0.878, 0.790, 0.960)
    box(ax, 0.360, 0.919, 0.200, 0.058, "IMAP / POP3 邮箱")
    arrow(ax, (0.360, 0.878), (0.360, 0.816))                      # 层间箭头落在间隙里

    # ② 时序图（列 = 参与者，行 = 时间，自上而下）
    from diagram_kit import canvas, lifeline, msg, finalize
    fig, ax = canvas(11, 7, title="一次收信时序")
    a = lifeline(ax, 0.15, 0.90, 0.06, "调度器")
    b = lifeline(ax, 0.45, 0.90, 0.06, "Worker")
    msg(ax, a, b, 0.78, "投递 mail.fetch")

**声明尺寸 = 可见尺寸**：`box(w, h)` 画出来的盒子就是 w×h，不会因为圆角样式偷偷外扩。
所以两个节点相邻时，中心距必须 **> (w1+w2)/2** 才不重叠——留一点额外间隙更好看。

`finalize` 会做自检并打印结果，这是**看不到图片时的核心迭代信号**：

1. **文字溢出**：节点内文字超出节点宽/高
2. **节点重叠**：两个 box 的**实际渲染包围盒**相交
3. **越界**：box / 容器 超出 0~1 画布范围
4. **容器标题溢出**：`band()` 的标题文字超出它所属容器
5. **消息过密**：时序图里相邻两条消息的 y 间距过小

只要有一项 FAIL，就调整坐标或尺寸后重跑，直到全 PASS。
"""
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "SimSun", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

# 默认配色：清爽商务（白卡片 + 中性灰 + 少量强调色）
# 与 diagrams/architecture.py 的总体架构图同源——固定调色板标注技术域、
# 深色描边 + 白/浅色填充（Tailwind v3.4 官方色阶；配色原则参考 IBM 架构可视化规范）。
# 边线/箭头按 WCAG 非文本对比度 ≥3.0 选取，别为了"清淡"调到看不清。
BOX_FC, BOX_EC = "#FFFFFF", "#64748B"          # white / slate-500
BAND_FC, BAND_EC = "#F8FAFC", "#CBD5E1"        # slate-50 / slate-300
ACCENT_FC, ACCENT_EC = "#EFF6FF", "#3B82F6"    # blue-50 / blue-500
ACTOR_FC, ACTOR_EC = "#FFFFFF", "#64748B"      # white / slate-500
LIFELINE_C = "#CBD5E1"                         # slate-300
ARROW_C = "#64748B"                            # slate-500
MUTED = "#64748B"                              # slate-500
TITLE_C, GROUP_C, CAPTION_C = "#1E293B", "#334155", "#475569"  # slate-800/700/600

_PAD = 0.010       # 圆角样式的内边距；box() 会把它算进去，保证「声明尺寸 = 可见尺寸」

_BOXES = []        # (text_artist, (x, y, w, h), label, patch)
_CONTAINERS = []   # (x0, y0, x1, y1, label, title_artist|None)
_MSGS = []         # (y, label)


def canvas(w=11.0, h=8.0, title=None):
    """新建画布。返回 (fig, ax)。每次调用会清空上一次的登记项。"""
    _BOXES.clear()
    _CONTAINERS.clear()
    _MSGS.clear()
    fig, ax = plt.subplots(figsize=(w, h))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    if title:
        fig.suptitle(title, fontsize=12.5, fontweight="bold", y=0.975, color=TITLE_C)
    return fig, ax


def box(ax, x, y, w, h, text, fc=BOX_FC, ec=BOX_EC, fs=9.5, bold=False, track=True):
    """在 (x, y) 中心画一个**可见尺寸就是 w×h** 的节点。

    内部把圆角样式所需的内边距从 w/h 里预留出来（而不是往外扩），
    这样「声明多大 = 画出来多大」，不会出现两个节点看着重叠的情况。
    """
    iw, ih = max(w - 2 * _PAD, w * 0.4), max(h - 2 * _PAD, h * 0.4)
    patch = FancyBboxPatch(
        (x - iw / 2, y - ih / 2), iw, ih,
        boxstyle=f"round,pad={_PAD},rounding_size=0.018",
        linewidth=1.1, edgecolor=ec, facecolor=fc, zorder=3)
    ax.add_patch(patch)
    t = ax.text(x, y, text, ha="center", va="center", fontsize=fs, zorder=4,
                fontweight="bold" if bold else "normal", linespacing=1.45)
    if track:
        _BOXES.append((t, (x, y, w, h), text, patch))
    return t


def band(ax, x0, y0, x1, y1, title=None, fc=BAND_FC, ec=BAND_EC,
         title_rotate=False, title_ha="left"):
    """画一个分组容器（虚线框）。作为容器不参与「节点重叠」判定，但它的**标题会参与溢出检查**。

    title_rotate=True 是竖排——竖排文字的高度等于文字长度，矮带里极易溢出，
    所以默认横排；要用竖排请先确认带足够高（自检会拦下溢出的情况）。
    """
    ax.add_patch(FancyBboxPatch(
        (x0, y0), x1 - x0, y1 - y0,
        boxstyle="round,pad=0.008,rounding_size=0.02",
        linewidth=1.0, edgecolor=ec, facecolor=fc,
        linestyle=(0, (5, 3)), zorder=1))
    artist = None
    if title:
        if title_rotate:
            artist = ax.text(x0 + 0.012, (y0 + y1) / 2, title, ha="left", va="center",
                             fontsize=9, color=GROUP_C, fontweight="bold",
                             rotation=90, zorder=2)
        else:
            artist = ax.text(x0 + 0.012, y1 - 0.014, title, ha=title_ha, va="top",
                             fontsize=9, color=GROUP_C, fontweight="bold", zorder=2)
    _CONTAINERS.append((x0, y0, x1, y1, title or "", artist))


def arrow(ax, p1, p2, label=None, color=ARROW_C, rad=0.0, dashed=False,
          double=False, fs=7.6, lw=1.0, head=12):
    """从 p1 指向 p2 的箭头。label 会自动加白底避免压线。

    `lw` 是线宽、`head` 是箭头头部大小——**细线配略大的头部**比粗线小头部精致；
    线太粗会显得笨重。端点用圆角，避免生硬的方角。
    注意：层间箭头很短时（间隙小），label 会盖住整条箭头——那种情况请把文字
    用 `caption()` 放在箭头旁边，而不是用这个 label。
    """
    patch = FancyArrowPatch(
        p1, p2, arrowstyle="<|-|>" if double else "-|>", mutation_scale=head,
        linewidth=lw, color=color, zorder=5,
        linestyle=(0, (4, 2.5)) if dashed else "-",
        shrinkA=3, shrinkB=3, connectionstyle=f"arc3,rad={rad}")
    patch.set_capstyle("round")
    patch.set_joinstyle("round")
    ax.add_patch(patch)
    if label:
        ax.text((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2, label,
                fontsize=fs, color=MUTED, ha="center", va="center", zorder=6,
                bbox=dict(fc="white", ec="none", pad=0.8))


def route_arrow(ax, p1, p2, lane_x, label=None, label_side="right", color=ARROW_C,
                dashed=False, fs=7.6):
    """直角绕行箭头：p1 --水平--> lane_x --竖直--> 再水平进入 p2。

    用于**跨层**连线：直接画斜线会压在中间那些层上，绕到侧边通道（lane_x）走就干净了。
    """
    x1, y1 = p1
    x2, y2 = p2
    ls = (0, (4, 2.5)) if dashed else "-"
    ax.plot([x1, lane_x], [y1, y1], color=color, linewidth=1.15, zorder=5, linestyle=ls)
    ax.plot([lane_x, lane_x], [y1, y2], color=color, linewidth=1.15, zorder=5, linestyle=ls)
    ax.add_patch(FancyArrowPatch((lane_x, y2), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=11, linewidth=1.15, color=color,
                                 zorder=5, linestyle=ls))
    if label:
        dx = 0.010 if label_side == "right" else -0.010
        ax.text(lane_x + dx, (y1 + y2) / 2, label, fontsize=fs, color=MUTED,
                ha="left" if label_side == "right" else "right", va="center",
                zorder=6, bbox=dict(fc="white", ec="none", pad=0.8))


def caption(ax, x, y, text, fs=9, color=CAPTION_C, **kw):
    """纯文字标注（不参与盒内溢出判定）。用于层的名称、箭头旁的说明等。"""
    return ax.text(x, y, text, fontsize=fs, color=color, **kw)


# ------------------------------------------------------- 图标（Font Awesome Free）
_FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                         "assets", "fonts")
_ICON_FP = None
_ICON_MAP = None


def _load_icons():
    """惰性加载图标字体与码点表。资源缺失时返回空表（静默降级为纯文字）。"""
    global _ICON_FP, _ICON_MAP
    if _ICON_MAP is None:
        import json

        from matplotlib import font_manager
        ttf = os.path.join(_FONT_DIR, "fa-solid-900.ttf")
        codes = os.path.join(_FONT_DIR, "fa-codepoints.json")
        if os.path.exists(ttf) and os.path.exists(codes):
            _ICON_FP = font_manager.FontProperties(fname=ttf)
            with open(codes, encoding="utf-8") as f:
                _ICON_MAP = json.load(f)
        else:
            _ICON_MAP = {}
    return _ICON_MAP


def icon(ax, x, y, name, size=12, color=BOX_EC, ha="center", va="center", zorder=6):
    """在 (x, y) 画一个图标（名字见 assets/fonts/fa-codepoints.json）。

    字体资源不在时**静默跳过**——图仍能出，只是少了图标，不会中断生成。
    可用名字：envelope / tower-broadcast / microchip / database / window-restore /
    cloud / share-nodes / gears / server / hard-drive / globe / comments / brain 等。
    """
    cp = _load_icons().get(name)
    if not cp:
        return None
    return ax.text(x, y, chr(int(cp, 16)), fontproperties=_ICON_FP, fontsize=size,
                   color=color, ha=ha, va=va, zorder=zorder)


# ------------------------------------------------------- 时序图原语
def lifeline(ax, x, y_top, y_bot, name, w=0.17, h=0.058,
             fc=ACTOR_FC, ec=ACTOR_EC, fs=9.5):
    """画一条参与者生命线：顶部名称框 + 向下的虚线。返回该列的 x 坐标（供 msg 用）。"""
    box(ax, x, y_top, w, h, name, fc=fc, ec=ec, fs=fs, bold=True)
    ax.plot([x, x], [y_top - h / 2, y_bot], color=LIFELINE_C, linewidth=1.0,
            linestyle=(0, (4, 3)), zorder=2)
    return x


def msg(ax, x1, x2, y, text=None, dashed=False, color=ARROW_C, fs=8.0):
    """一条消息箭头（同一个 y）。x1 == x2 时画自消息回环；dashed 表示返回/异步。"""
    if abs(x1 - x2) < 0.01:                      # 自消息
        ax.add_patch(FancyArrowPatch(
            (x1, y), (x1 + 0.055, y), arrowstyle="-|>", mutation_scale=10,
            linewidth=1.15, color=color, zorder=4,
            connectionstyle="arc3,rad=-1.6"))
        if text:
            ax.text(x1 + 0.075, y, text, fontsize=fs, color=MUTED,
                    ha="left", va="center", zorder=6)
    else:
        ax.add_patch(FancyArrowPatch(
            (x1, y), (x2, y), arrowstyle="-|>", mutation_scale=10,
            linewidth=1.15, color=color, zorder=4,
            linestyle=(0, (4, 2.5)) if dashed else "-"))
        if text:
            ax.text((x1 + x2) / 2, y + 0.016, text, fontsize=fs, color=MUTED,
                    ha="center", va="bottom", zorder=6,
                    bbox=dict(fc="white", ec="none", pad=0.6))
    _MSGS.append((y, text or ""))
    return y


# ------------------------------------------------------------------ 自检
def _bbox_ratio(fig, ax, artist, box):
    """artist 的包围盒相对 box=(x0,y0,x1,y1) 的宽/高占比。"""
    te = artist.get_window_extent(renderer=fig.canvas.get_renderer())
    p0 = ax.transData.transform((box[0], box[1]))
    p1 = ax.transData.transform((box[2], box[3]))
    bw, bh = abs(p1[0] - p0[0]), abs(p1[1] - p0[1])
    return te.width / bw, te.height / bh


def _check_overflow(fig, ax, tol=0.98):
    fig.canvas.draw()
    bad = []
    for t, (x, y, w, h), label, _ in _BOXES:
        rw, rh = _bbox_ratio(fig, ax, t, (x - w / 2, y - h / 2, x + w / 2, y + h / 2))
        if rw > tol or rh > tol:
            bad.append((label.replace("\n", " / "), round(rw, 2), round(rh, 2)))
    return bad


def _check_container_title(fig, ax, tol=0.98):
    """容器标题是否超出容器（竖排标题在矮带里最容易中招）。"""
    fig.canvas.draw()
    bad = []
    for x0, y0, x1, y1, label, artist in _CONTAINERS:
        if artist is None:
            continue
        rw, rh = _bbox_ratio(fig, ax, artist, (x0, y0, x1, y1))
        if rw > tol or rh > tol:
            bad.append((label.replace("\n", " / "), round(rw, 2), round(rh, 2)))
    return bad


def _check_overlap(fig, ax):
    """按**实际渲染包围盒**判定重叠。

    （不要按声明尺寸算：`boxstyle` 的内边距会让盒子比声明的大，
    曾因此让三个相邻节点看着重叠而自检却报 PASS。）
    """
    fig.canvas.draw()
    r = fig.canvas.get_renderer()
    bad = []
    for i in range(len(_BOXES)):
        for j in range(i + 1, len(_BOXES)):
            b1 = _BOXES[i][3].get_window_extent(renderer=r)
            b2 = _BOXES[j][3].get_window_extent(renderer=r)
            ox = min(b1.x1, b2.x1) - max(b1.x0, b2.x0)
            oy = min(b1.y1, b2.y1) - max(b1.y0, b2.y0)
            if ox > 0 and oy > 0:
                l1 = _BOXES[i][2].replace("\n", "/")
                l2 = _BOXES[j][2].replace("\n", "/")
                bad.append((l1, l2, f"重叠 {ox:.0f}x{oy:.0f}px"))
    return bad


def _check_out_of_bounds():
    bad = []
    for _, (x, y, w, h), label, _ in _BOXES:
        if x - w / 2 < -0.001 or x + w / 2 > 1.001 or y - h / 2 < -0.001 or y + h / 2 > 1.001:
            bad.append(label.replace("\n", " / "))
    for x0, y0, x1, y1, lbl, _ in _CONTAINERS:
        if x0 < -0.001 or y0 < -0.001 or x1 > 1.001 or y1 > 1.001:
            bad.append(f"[容器] {lbl}")
    return bad


def _check_msg_spacing(min_gap=0.042):
    """时序图：相邻两条消息的 y 间距过小 -> 文字会挤在一起。"""
    ys = sorted(y for y, _ in _MSGS)
    return [round(b - a, 3) for a, b in zip(ys, ys[1:]) if b - a < min_gap]


def finalize(fig, ax, out_path, dpi=200, verbose=True):
    """自检 -> 保存 PNG -> 打印报告。"""
    rep = {
        "boxes": len(_BOXES),
        "overflow": _check_overflow(fig, ax),
        "container_title": _check_container_title(fig, ax),
        "overlap": _check_overlap(fig, ax),
        "out_of_bounds": _check_out_of_bounds(),
        "msg_too_close": _check_msg_spacing(),
    }
    rep["ok"] = not (rep["overflow"] or rep["container_title"] or rep["overlap"]
                     or rep["out_of_bounds"] or rep["msg_too_close"])
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    if verbose:
        print(f"[自检 {'PASS' if rep['ok'] else 'FAIL'}] {out_path}  "
              f"(节点 {rep['boxes']} / 消息 {len(_MSGS)})")
        for key, head in (("overflow", "文字溢出(文字/盒宽比, 文字/盒高比)"),
                          ("container_title", "容器标题溢出(文字/容器宽比, 文字/容器高比)"),
                          ("overlap", "节点重叠(实际包围盒)"),
                          ("out_of_bounds", "超出画布"),
                          ("msg_too_close", "消息过密(相邻间距)")):
            if rep[key]:
                print(f"  {head}:")
                for it in rep[key]:
                    print("   -", it)
    return rep
