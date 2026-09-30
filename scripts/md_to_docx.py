# -*- coding: utf-8 -*-
"""Markdown -> Word (.docx) 转换器（CLI）。

用法:
    python md_to_docx.py 输入.md
    python md_to_docx.py 输入.md -o 输出.docx
    python md_to_docx.py 输入.md --diagrams ./diagrams/assets

关于 mermaid 图（重要）:
    本工具**不做自动布局**。md 里第 N 个 ```mermaid 代码块，会被替换为
    <diagrams 目录>/diagram_N.png。该 PNG 需要由 agent 按 SKILL.md 的「四步法」
    手写绘图脚本产出（见 diagrams/architecture.py、diagrams/pipeline.py 两个范例）。
    找不到图时，该块会保留为代码文本并打印警告——不会插入一张结构不可靠的自动图。

支持的 Markdown 语法同 SKILL.md；退出码 0 成功 / 1 输入问题 / 2 参数问题。
"""
import argparse
import os
import re
import sys

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

CN, EN, MONO = "宋体", "Times New Roman", "Consolas"
BODY_SIZE = 12
IMG_WIDTH_CM = 15.5

INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*\s][^*]*?\*|`[^`]+?`|!\[[^\]]*\]\([^)]+?\)|\[[^\]]+?\]\([^)]+?\))")
IMG_ONLY = re.compile(r"^!\[([^\]]*)\]\(([^)]+?)\)$")


def set_font(run, cn=CN, en=EN, size=BODY_SIZE, bold=False, italic=False, color=None):
    run.font.name = en
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    if color is not None:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    rf.set(qn("w:eastAsia"), cn)
    rf.set(qn("w:ascii"), en)
    rf.set(qn("w:hAnsi"), en)


def body_format(p, indent=True, space_after=6):
    pf = p.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_before = Pt(0)
    pf.space_after = Pt(space_after)
    if indent:
        pf.first_line_indent = Cm(0.74)


def add_hr(doc):
    p = doc.add_paragraph()
    ppr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), "C8C8C8")
    pbdr.append(bottom)
    ppr.append(pbdr)
    p.paragraph_format.space_after = Pt(8)


def shade(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


def add_image(doc, path, width_cm=IMG_WIDTH_CM):
    doc.add_picture(path, width=Cm(width_cm))
    p = doc.paragraphs[-1]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)


def code_block(doc, lines):
    for ln in lines:
        p = doc.add_paragraph()
        body_format(p, indent=False, space_after=0)
        set_font(p.add_run(ln), cn=MONO, en=MONO, size=9)


def add_inline(p, text, size=BODY_SIZE, bold=False, color=None):
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            set_font(p.add_run(part[2:-2]), size=size, bold=True, color=color)
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            set_font(p.add_run(part[1:-1]), cn=MONO, en=MONO, size=size - 0.5,
                     color=RGBColor(0x9A, 0x3A, 0x3A))
        elif part.startswith("!["):
            continue
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            set_font(p.add_run(part[1:-1]), size=size, italic=True, color=color)
        elif part.startswith("[") and "](" in part:
            set_font(p.add_run(part[1:part.index("]")]), size=size,
                     color=RGBColor(0x1F, 0x4E, 0x79))
        else:
            set_font(p.add_run(part), size=size, bold=bold, color=color)


def smart_join(a, b):
    if a and b and a[-1].isascii() and b[0].isascii() and a[-1].isalnum() and b[0].isalnum():
        return a + " " + b
    return a + b


def is_special(s):
    return (s.startswith("#") or s.startswith("|") or s.startswith(">")
            or s.startswith("```") or IMG_ONLY.match(s)
            or re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s)
            or re.match(r"^(-{3,}|\*{3,}|_{3,})$", s))


def convert(src_path, out_path, diagrams_dir=None, title=None):
    src = open(src_path, encoding="utf-8").read()
    base_dir = os.path.dirname(os.path.abspath(src_path))
    if diagrams_dir is None:
        diagrams_dir = os.path.join(base_dir, "diagrams")
    os.makedirs(diagrams_dir, exist_ok=True)

    doc = Document()
    for sec in doc.sections:
        sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
        sec.left_margin = sec.right_margin = Cm(2.54)
        sec.top_margin = sec.bottom_margin = Cm(2.54)
    normal = doc.styles["Normal"]
    normal.font.name = EN
    normal.font.size = Pt(BODY_SIZE)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), CN)

    lines = src.split("\n")
    i, n = 0, len(lines)
    first_h1 = True
    mmd_i = 0
    stat = {"heading": 0, "para": 0, "list": 0, "table": 0, "image": 0, "quote": 0, "code": 0}
    warnings = []

    while i < n:
        raw = lines[i]
        s = raw.strip()
        if not s:
            i += 1
            continue

        # 代码围栏
        if s.startswith("```"):
            lang = s[3:].strip().lower()
            body, i = [], i + 1
            while i < n and not lines[i].strip().startswith("```"):
                body.append(lines[i])
                i += 1
            i += 1
            if lang in ("mermaid", "mmd"):
                mmd_i += 1
                png = os.path.join(diagrams_dir, f"diagram_{mmd_i}.png")
                if os.path.exists(png):
                    add_image(doc, png)
                    stat["image"] += 1
                else:
                    warnings.append(
                        f"第 {mmd_i} 个 mermaid 块没有对应图片：{png} —— 请按 SKILL.md『四步法』"
                        f"在 diagrams/ 下写绘图脚本产出它（本工具不做自动布局）")
                    code_block(doc, body)
                    stat["code"] += 1
            else:
                code_block(doc, body)
                stat["code"] += 1
            continue

        # 标题
        m = re.match(r"^(#{1,6})\s+(.*)$", s)
        if m:
            level, text = len(m.group(1)), m.group(2).strip()
            p = doc.add_paragraph()
            pf = p.paragraph_format
            pf.line_spacing_rule = WD_LINE_SPACING.SINGLE
            pf.space_before = Pt(14 if level <= 2 else 10)
            pf.space_after = Pt(8)
            if level == 1:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                pf.space_before, pf.space_after = Pt(60), Pt(18)
                set_font(p.add_run(title or text), size=22, bold=True)
            elif level == 2:
                if first_h1:
                    pf.page_break_before = True
                    first_h1 = False
                set_font(p.add_run(text), size=22, bold=True)
            elif level == 3:
                set_font(p.add_run(text), size=16, bold=True)
            elif level == 4:
                set_font(p.add_run(text), size=15, bold=True)
            else:
                set_font(p.add_run(text), size=14, bold=True)
            stat["heading"] += 1
            i += 1
            continue

        # 分隔线
        if re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            add_hr(doc)
            i += 1
            continue

        # 引用块
        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            text = ""
            for ln in buf:
                text = smart_join(text, ln) if ln else text + "\n"
            p = doc.add_paragraph()
            body_format(p, indent=False)
            p.paragraph_format.left_indent = Cm(0.75)
            p.paragraph_format.space_after = Pt(4)
            add_inline(p, text, size=11.5, color=RGBColor(0x44, 0x44, 0x44))
            stat["quote"] += 1
            continue

        # 独立图片
        mi = IMG_ONLY.match(s)
        if mi:
            rel = mi.group(2).strip()
            path = rel if os.path.isabs(rel) else os.path.join(base_dir, rel)
            if os.path.exists(path):
                add_image(doc, path)
                stat["image"] += 1
            else:
                warnings.append(f"图片不存在: {rel}")
            i += 1
            continue

        # 表格
        if s.startswith("|"):
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                t = lines[i].strip()
                if not re.match(r"^[-:\s|]+$", t):
                    rows.append([c.strip() for c in t.strip("|").split("|")])
                i += 1
            if rows:
                cols = max(len(r) for r in rows)
                tb = doc.add_table(rows=0, cols=cols)
                tb.style = "Table Grid"
                for ri, row in enumerate(rows):
                    cells = tb.add_row().cells
                    for ci in range(cols):
                        cp = cells[ci].paragraphs[0]
                        cp.paragraph_format.space_after = Pt(2)
                        cp.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                        add_inline(cp, row[ci] if ci < len(row) else "",
                                   size=10.5, bold=(ri == 0))
                        if ri == 0:
                            cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            shade(cells[ci], "D9E2F3")
                doc.add_paragraph().paragraph_format.space_after = Pt(2)
                stat["table"] += 1
            continue

        # 列表
        if re.match(r"^[-*]\s+", s) or re.match(r"^\d+\.\s+", s):
            indent = (len(raw) - len(raw.lstrip())) // 2
            ordered = bool(re.match(r"^\d+\.\s+", s))
            text = s if ordered else re.sub(r"^[-*]\s+", "", s)
            p = doc.add_paragraph()
            body_format(p, indent=False, space_after=3)
            p.paragraph_format.left_indent = Cm(0.74 + 0.6 * indent)
            p.paragraph_format.first_line_indent = Cm(-0.42 if not ordered else -0.6)
            set_font(p.add_run("" if ordered else "•  "), size=BODY_SIZE)
            add_inline(p, text)
            stat["list"] += 1
            i += 1
            continue

        # 普通段落
        buf = [s]
        i += 1
        while i < n and lines[i].strip() and not is_special(lines[i].strip()):
            buf.append(lines[i].strip())
            i += 1
        text = ""
        for ln in buf:
            text = smart_join(text, ln)
        p = doc.add_paragraph()
        body_format(p)
        add_inline(p, text)
        stat["para"] += 1

    doc.save(out_path)
    return {"out": out_path, "diagrams": diagrams_dir, "stat": stat, "warnings": warnings}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Markdown -> Word (.docx) 转换器")
    ap.add_argument("input", help="输入 .md 文件")
    ap.add_argument("-o", "--output", help="输出 .docx（默认与输入同目录同名）")
    ap.add_argument("--diagrams", help="手绘图目录，按序查找 diagram_1.png / diagram_2.png …"
                                       "（默认 <输入目录>/diagrams）")
    ap.add_argument("--title", help="覆盖文档标题")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.input):
        print(f"错误: 找不到输入文件 {args.input}", file=sys.stderr)
        return 1
    out = args.output or os.path.splitext(args.input)[0] + ".docx"
    res = convert(args.input, out, args.diagrams, args.title)
    print(f"已生成: {res['out']}")
    print(f"图目录: {res['diagrams']}")
    print(f"元素统计: {res['stat']}")
    if res["warnings"]:
        print("警告:")
        for w in res["warnings"]:
            print("  -", w)
        return 1 if res["stat"]["code"] and res["stat"]["image"] == 0 else 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
