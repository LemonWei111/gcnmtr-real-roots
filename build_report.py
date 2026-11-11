# -*- coding: utf-8 -*-
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

OUT = 'poly_roots_算法报告.docx'
BODY_FONT_CN = '宋体'
BODY_FONT_EN = 'Times New Roman'
HEAD_FONT_CN = '黑体'
HEAD_FONT_EN = 'Arial'
MATH_FONT = 'Cambria Math'
MONO_FONT = 'Consolas'
DARK = RGBColor(0x1F, 0x3B, 0x57)
GRAY = RGBColor(0x55, 0x55, 0x55)
BLACK = RGBColor(0, 0, 0)


def set_run_font(run, size=10.5, bold=False, color=BLACK,
                 en=BODY_FONT_EN, cn=BODY_FONT_CN, italic=False,
                 subscript=False, superscript=False):
    run.font.name = en
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color
    run.font.subscript = subscript
    run.font.superscript = superscript
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), en)
    rFonts.set(qn('w:hAnsi'), en)
    rFonts.set(qn('w:eastAsia'), cn)


def set_style_font(style, size, bold=False, color=BLACK,
                   en=BODY_FONT_EN, cn=BODY_FONT_CN):
    style.font.name = en
    style.font.size = Pt(size)
    style.font.bold = bold
    style.font.color.rgb = color
    rPr = style.element.get_or_add_rPr()
    rFonts = rPr.find(qn('w:rFonts'))
    if rFonts is None:
        rFonts = OxmlElement('w:rFonts')
        rPr.append(rFonts)
    rFonts.set(qn('w:ascii'), en)
    rFonts.set(qn('w:hAnsi'), en)
    rFonts.set(qn('w:eastAsia'), cn)


def shade_cell(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:color'), 'auto')
    shd.set(qn('w:fill'), fill)
    tcPr.append(shd)


def set_cell_margins(cell, top=0.05, bottom=0.05, left=0.12, right=0.12):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for tag, value in (('top', top), ('bottom', bottom), ('left', left), ('right', right)):
        node = OxmlElement('w:' + tag)
        node.set(qn('w:w'), str(int(value * 567)))
        node.set(qn('w:type'), 'cm')
        tcMar.append(node)
    tcPr.append(tcMar)


def set_table_borders(table, color='B7C7D8', size='4'):
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        el = OxmlElement('w:' + edge)
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), size)
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), color)
        borders.append(el)
    tblPr.append(borders)


def set_row_cant_split(row):
    trPr = row._tr.get_or_add_trPr()
    cantSplit = OxmlElement('w:cantSplit')
    trPr.append(cantSplit)


def add_page_number_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('第 ')
    set_run_font(r, 9, color=GRAY)
    fld_begin = OxmlElement('w:fldChar')
    fld_begin.set(qn('w:fldCharType'), 'begin')
    instr = OxmlElement('w:instrText')
    instr.set(qn('xml:space'), 'preserve')
    instr.text = ' PAGE '
    fld_sep = OxmlElement('w:fldChar')
    fld_sep.set(qn('w:fldCharType'), 'separate')
    fld_text = OxmlElement('w:t')
    fld_text.text = '1'
    fld_end = OxmlElement('w:fldChar')
    fld_end.set(qn('w:fldCharType'), 'end')
    r2 = p.add_run()
    set_run_font(r2, 9, color=GRAY)
    r2._r.append(fld_begin)
    r2._r.append(instr)
    r2._r.append(fld_sep)
    r2._r.append(fld_text)
    r2._r.append(fld_end)
    r3 = p.add_run(' 页')
    set_run_font(r3, 9, color=GRAY)


def add_header(section):
    header = section.header
    p = header.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p.paragraph_format.tab_stops.add_tab_stop(Cm(15.6), WD_TAB_ALIGNMENT.RIGHT)
    r = p.add_run('工程计算方法 · 算法报告')
    set_run_font(r, 8.5, color=GRAY)
    r = p.add_run('\t北京邮电大学')
    set_run_font(r, 8.5, color=GRAY)
    pPr = p._p.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '4')
    bottom.set(qn('w:color'), 'B7C7D8')
    pBdr.append(bottom)
    pPr.append(pBdr)


def para(text='', size=10.5, bold=False, color=BLACK, align=WD_ALIGN_PARAGRAPH.JUSTIFY,
         first_indent=True, space_before=0, space_after=4, line=1.5,
         keep_with_next=False, en=BODY_FONT_EN, cn=BODY_FONT_CN):
    p = doc.add_paragraph()
    p.alignment = align
    pf = p.paragraph_format
    pf.space_before = Pt(space_before)
    pf.space_after = Pt(space_after)
    pf.line_spacing = line
    if first_indent:
        pf.first_line_indent = Pt(size * 2)
    pf.keep_with_next = keep_with_next
    pf.widow_control = True
    if text:
        r = p.add_run(text)
        set_run_font(r, size, bold, color, en=en, cn=cn)
    return p


def body_with_lead(lead, text, size=10.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(4)
    pf.line_spacing = 1.5
    pf.first_line_indent = Pt(size * 2)
    pf.widow_control = True
    r = p.add_run(lead)
    set_run_font(r, size, bold=True)
    r = p.add_run(text)
    set_run_font(r, size)
    return p


def bullet(text, size=10.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    pf = p.paragraph_format
    pf.left_indent = Cm(0.74)
    pf.first_line_indent = Cm(-0.37)
    pf.space_before = Pt(0)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.4
    pf.widow_control = True
    r = p.add_run('• ')
    set_run_font(r, size)
    r = p.add_run(text)
    set_run_font(r, size)
    return p


def heading(text, level=1):
    p = doc.add_paragraph(style='Heading %d' % level)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    r = p.add_run(text)
    set_run_font(r, {1: 16, 2: 13, 3: 11.5}[level], True,
                 en=HEAD_FONT_EN, cn=HEAD_FONT_CN)
    return p


def caption(text, keep=True):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pf = p.paragraph_format
    pf.space_before = Pt(4)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.2
    pf.keep_with_next = keep
    r = p.add_run(text)
    set_run_font(r, 9, bold=False, color=GRAY)
    return p


def add_table(headers, rows, widths, caption_text, font_size=8.8,
              header_fill='1F4E79', first_col_left=True):
    caption(caption_text)
    table = doc.add_table(rows=1, cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)
    hdr = table.rows[0]
    set_row_cant_split(hdr)
    for j, h in enumerate(headers):
        cell = hdr.cells[j]
        cell.width = Cm(widths[j])
        shade_cell(cell, header_fill)
        set_cell_margins(cell)
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(1)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.0
        r = p.add_run(h)
        set_run_font(r, font_size, True, RGBColor(255, 255, 255))
    for i, row in enumerate(rows):
        tr = table.add_row()
        set_row_cant_split(tr)
        for j, val in enumerate(row):
            cell = tr.cells[j]
            cell.width = Cm(widths[j])
            set_cell_margins(cell)
            if i % 2 == 0:
                shade_cell(cell, 'F2F6FA')
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT if (j == 0 and first_col_left) else WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.paragraph_format.line_spacing = 1.0
            r = p.add_run(str(val))
            set_run_font(r, font_size)
    # small spacing after table
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0
    return table


def add_figure(path, width_cm, caption_text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run()
    run.add_picture(path, width=Cm(width_cm))
    caption(caption_text, keep=False)


def add_code(lines, caption_text, size=8.3):
    caption(caption_text)
    table = doc.add_table(rows=1, cols=1)
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    table.columns[0].width = Cm(15.6)
    cell = table.rows[0].cells[0]
    cell.width = Cm(15.6)
    shade_cell(cell, 'F5F7F9')
    set_cell_margins(cell, top=0.12, bottom=0.12, left=0.18, right=0.18)
    set_table_borders(table, color='D0D8E2', size='4')
    set_row_cant_split(table.rows[0])
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.0
    first = True
    for line in lines:
        if not first:
            p = cell.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = 1.0
        first = False
        r = p.add_run(line)
        set_run_font(r, size, en=MONO_FONT, cn=MONO_FONT)
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.0


def add_formula(segments, number=None, size=10.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    pf = p.paragraph_format
    pf.space_before = Pt(2)
    pf.space_after = Pt(2)
    pf.line_spacing = 1.2
    pf.keep_together = True
    pf.tab_stops.add_tab_stop(Cm(7.9), WD_TAB_ALIGNMENT.CENTER)
    pf.tab_stops.add_tab_stop(Cm(15.6), WD_TAB_ALIGNMENT.RIGHT)
    p.add_run('\t')
    for text, mode in segments:
        r = p.add_run(text)
        set_run_font(r, size, en=MATH_FONT, cn=MATH_FONT,
                     italic=(mode == 'i'), subscript=(mode == 'sub'),
                     superscript=(mode == 'sup'))
    if number is not None:
        r = p.add_run('\t（%d）' % number)
        set_run_font(r, 9.5)


doc = Document()

# Document defaults
normal = doc.styles['Normal']
set_style_font(normal, 10.5, False, BLACK, BODY_FONT_EN, BODY_FONT_CN)
normal.paragraph_format.line_spacing = 1.5
normal.paragraph_format.space_after = Pt(4)
normal.paragraph_format.widow_control = True

for level, size in ((1, 16), (2, 13), (3, 11.5)):
    st = doc.styles['Heading %d' % level]
    set_style_font(st, size, True, BLACK, HEAD_FONT_EN, HEAD_FONT_CN)
    st.font.underline = False
    st.paragraph_format.keep_with_next = True
    st.paragraph_format.space_before = Pt({1: 16, 2: 10, 3: 8}[level])
    st.paragraph_format.space_after = Pt({1: 8, 2: 5, 3: 4}[level])

title_style = doc.styles['Title']
set_style_font(title_style, 23, True, BLACK, 'Times New Roman', HEAD_FONT_CN)
title_style.font.underline = False
title_style.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
title_style.paragraph_format.space_before = Pt(0)
title_style.paragraph_format.space_after = Pt(8)

section = doc.sections[0]
section.page_width = Cm(21.0)
section.page_height = Cm(29.7)
section.top_margin = Cm(2.5)
section.bottom_margin = Cm(2.4)
section.left_margin = Cm(2.6)
section.right_margin = Cm(2.6)
section.different_first_page_header_footer = True
add_header(section)
add_page_number_footer(section)

core = doc.core_properties
core.title = '一元 n 次实系数多项式实根通用求解器算法报告'
core.subject = '工程计算方法平时算法大作业'
core.author = '工程计算方法课程作业'
core.keywords = '多项式求根；连续牛顿流；综合除法；重数认证；Descartes 符号法则'

# ---------------- Title page ----------------
p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(42)
r = p.add_run('北京邮电大学')
set_run_font(r, 16, True, DARK, en='Times New Roman', cn=HEAD_FONT_CN)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(66)
r = p.add_run('2026 年秋季研究生课程')
set_run_font(r, 12, False, GRAY)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(10)
r = p.add_run('工程计算方法平时算法大作业')
set_run_font(r, 14, False, BLACK, cn='楷体')

p = doc.add_paragraph(style='Title')
r = p.add_run('一元 n 次实系数多项式\n实根通用求解器算法报告')
set_run_font(r, 23, True, BLACK, en='Times New Roman', cn=HEAD_FONT_CN)
p.paragraph_format.line_spacing = 1.25

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(12)
p.paragraph_format.space_after = Pt(84)
r = p.add_run('基于连续牛顿流、降次与重数认证的 poly_roots 求解器')
set_run_font(r, 13, False, DARK, cn='楷体')

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_after = Pt(4)
r = p.add_run('2026 年 11 月')
set_run_font(r, 12, False, GRAY)

# Cover information block
for line in ('求解对象：p₅(x)=x⁵−6x³−x²−5x+5',
             '求解器：poly_roots.poly_real_roots',
             '运行环境：Python 3.10 / NumPy 2.1'):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(72 if line.startswith('求解对象') else 2)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.35
    r = p.add_run(line)
    set_run_font(r, 10.5, False, GRAY)

doc.add_page_break()

# ---------------- Abstract ----------------
heading('摘要', 1)
para('针对一元 n 次实系数多项式可能同时存在单根、重根、零根和无实根的情况，本文设计并实现了一个通用实根求解器 poly_real_roots。求解器以连续牛顿流完成单根定位，以综合除法降次，以高精度 Decimal 算术认证重数，并用 Descartes 符号变化、采样变号与聚类规范化提供完整性证据和明确的状态标记。', first_indent=True)
para('对题目多项式 p₅(x)=x⁵−6x³−x²−5x+5，求得三个单重实根 −2.579714343403、0.634113250651、2.614244150443，残差均不超过 7.2×10⁻¹⁵，与 numpy.roots 的差异小于 10⁻¹²；剩余二次因子的判别式为负，说明另外两个根为一对共轭复根。结果通过了残差、Vieta 关系、因式分解和导数单调性四类校验。', first_indent=True)
p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(8)
p.paragraph_format.space_after = Pt(0)
p.paragraph_format.line_spacing = 1.5
r = p.add_run('关键词：')
set_run_font(r, 10.5, True)
r = p.add_run('多项式求根；连续牛顿流；综合除法；重数认证；Descartes 符号法则')
set_run_font(r, 10.5)

p = doc.add_paragraph()
p.paragraph_format.space_before = Pt(16)
p.paragraph_format.space_after = Pt(0)
p.paragraph_format.line_spacing = 1.5
p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
r = p.add_run('报告结构：')
set_run_font(r, 10.5, True)
r = p.add_run('第 1 节给出问题与总体路线；第 2 节说明算法设计；第 3 节给出数值结果与交叉验证；第 4 节解释结果的数学含义和算法边界；第 5 节讨论工程意义与应用场景；第 6 节总结，附录给出接口与复现方式。')
set_run_font(r, 10.5)

doc.add_page_break()

# ---------------- 1 ----------------
heading('1  问题描述与总体思路', 1)
heading('1.1  问题与设计目标', 2)
para('给定实系数多项式')
add_formula([('p(x) = a', ''), ('0', 'sub'), (' + a', ''), ('1', 'sub'), ('x + ⋯ + a', ''), ('n', 'sub'), ('x', ''), ('n', 'sup')], 1)
para('其中 aₙ≠0，要求在不提供任何初始猜测的前提下，求出 p(x)=0 的全部实根及其重数。系数按升幂排列，即 coeffs[i] 对应 xⁱ。题目中的五次多项式为', first_indent=True)
add_formula([('p', 'i'), ('5', 'sub'), ('(x) = x', 'i'), ('5', 'sup'), (' − 6x', 'i'), ('3', 'sup'), (' − x', 'i'), ('2', 'sup'), (' − 5x + 5', 'i')], 2)
para('该问题的主要困难不在单个牛顿迭代，而在全局性：牛顿法只保证局部收敛；重根附近导数趋于零，普通牛顿法退化为线性收敛；逐次降次会累积舍入误差；无实根时算法容易把“找不到”误当成“不存在”；高次展开还会带来 O(n²) 以上的计算量和系数溢出风险。因此，求解器需要同时满足以下目标：', first_indent=True)
bullet('通用性：任意次数、任意实系数，系数允许前导零、常数项为零或有重根。')
bullet('全局性：不依赖人工初值，能够定位所有实根；对无实根情形给出可验证的判断或明确的状态。')
bullet('准确性：单根达到双精度极限，重根尽可能恢复重数；降次后仍在原多项式上精修。')
bullet('可解释性：每个根都有残差和重数，重要判断有数学依据，而不是只输出一串数字。')
bullet('效率：主路径保持 O(n²) 时间、O(n) 空间，适合中低次多项式的反复调用。')

para('求解器采用“预处理—单根搜索—精修—降次与重数认证—完整性门控—规范化输出”的流水线。表 1 给出各模块的分工。', first_indent=True)
add_table(
    ['模块', '主要技术', '解决的问题'],
    [
        ['预处理', '去高次零、提取 xᵏ、首一化', '降低实际次数，精确记录零根，改善尺度'],
        ['单根搜索', '连续牛顿流、自适应步长、Levenberg 正则、多起点', '从任意初值全局定位一个实根，绕过驻点'],
        ['精修', '阻尼牛顿、重数修正步', '消除降次累积误差，恢复重根二次收敛'],
        ['降次与重数', '综合除法、Decimal 认证、聚类合并', '确定重数，处理数值上被拆开的重根'],
        ['完整性门控', 'Descartes 符号变化、采样变号、状态字段', '证明无根，或在证据不足时如实标记'],
        ['输出', '排序、去重、重数相加', '得到稳定、可直接使用的根表'],
    ],
    [2.8, 7.2, 5.8],
    '表 1  求解器模块划分'
)

heading('1.2  题目多项式的结论概览', 2)
para('对 p₅(x)=x⁵−6x³−x²−5x+5，求解器返回 3 个互不相同的单重实根：', first_indent=True)
add_formula([('x', 'i'), ('1', 'sub'), (' ≈ −2.579714343403，  x', 'i'), ('2', 'sub'), (' ≈ 0.634113250651，  x', 'i'), ('3', 'sub'), (' ≈ 2.614244150443', 'i')], 3)
para('剩余二次因子为 x²+0.668643057691x+1.169190862468，其判别式约为 −4.22968<0，因此另外两个根是一对共轭复根 −0.334321528846±1.028309281208i。所以 p₅ 恰有 3 个实根，且全部为单重根。详细数值、交叉验证和结果解释分别见第 3、4 节。', first_indent=True)

# ---------------- 2 ----------------
heading('2  程序设计思路', 1)
heading('2.1  数据约定与预处理', 2)
para('求解器统一采用升幂系数数组 a=[a₀,a₁,…,aₙ]。预处理完成三件事：去掉最高位的零系数以确定真实次数；统计低阶零系数的个数 k，把 xᵏ 整体提出，从而把 x=0 记录为 k 重根；用首项系数通除，使工作多项式成为首一多项式。这样既降低了后续次数，又避免了零根和尺度差异对迭代的干扰。', first_indent=True)
para('例如 p(x)=3x³+2x²=x²(3x+2)，预处理后记录 0 为二重根，剩余工作多项式为 x+2/3，次数从 3 降为 1。首一化不改变根，只改变多项式的整体尺度，有利于残差阈值的统一。', first_indent=True)

heading('2.2  单根定位：连续牛顿流', 2)
para('对当前工作多项式 q(x)，定义连续牛顿流（课程中广义连续牛顿法 GCNMTr 的标量形式）', first_indent=True)
add_formula([('dx/dt = −q(x) / q′(x)', 'i')], 4)
para('沿该流有 d q(x(t))/dt = q′(x)x′(t) = −q(x)，因此只要 q′≠0，就有 q(x(t))=q(x(0))e⁻ᵗ。这说明残差沿轨道理论上单调指数衰减，流最终会到达某个根；而经典的牛顿迭代 x←x−q/q′ 只是该流在 h=1 时的显式 Euler 离散。把牛顿法看作连续流的离散化，是本算法能够统一处理“快速收敛”和“驻点停滞”的关键。', first_indent=True)
para('实际离散采用带步长限制的 Euler 步', first_indent=True)
add_formula([('x', 'i'), ('k+1', 'sub'), (' = x', 'i'), ('k', 'sub'), (' − [h', 'i'), ('k', 'sub'), ('/(1+h', 'i'), ('k', 'sub'), (')] · q(x', 'i'), ('k', 'sub'), (')q′(x', 'i'), ('k', 'sub'), (') / [q′(x', 'i'), ('k', 'sub'), (')', ''), ('2', 'sup'), (' + λ', 'i'), ('k', 'sub'), (']', '')], 5)
para('其中 hₖ>0 是信赖域步长，λₖ 是 Levenberg 型正则项。分母使用 q′²+λ 而不是 q′，使 q′=0 的驻点附近步长自然趋于零，避免除零爆炸；当 q′=0 且 q≠0 时流会停在驻点，这是连续牛顿流在“没有可到达的实根”时的正确行为，而不是数值失败。', first_indent=True)
para('步长 hₖ 由残差的实际下降量与线性模型预测下降量之比控制：', first_indent=True)
add_formula([('ρ', 'i'), ('k', 'sub'), (' = (|q', 'i'), ('k', 'sub'), ('| − |q', 'i'), ('k+1', 'sub'), ('|) / (|q', 'i'), ('k', 'sub'), ('| − |q', 'i'), ('k', 'sub'), (' + q′', 'i'), ('k', 'sub'), ('s', 'i'), ('k', 'sub'), ('|)', 'i')], 6)
para('若 |1−ρₖ|<0.25，说明模型与真实下降高度一致，令 h←2h；若 |1−ρₖ|<0.75，保持 h；否则令 h←h/2。只有 ρₖ≥10⁻⁶ 的步才被接受；被拒绝时回退并增大 λ。这个规则使算法在远离根时敢于走大步，在接近根或遇到强非线性时自动收缩。', first_indent=True)
para('为了覆盖所有可能的实根，起点不能围绕 0 盲目选取。算法使用 Fujiwara 根界', first_indent=True)
add_formula([('B = 2 max', 'i'), ('1≤i≤n', 'sub'), (' |a', 'i'), ('n−i', 'sub'), ('/a', 'i'), ('n', 'sub'), ('|', ''), ('1/i', 'sup')], 7)
para('保证所有实根都落在 [−B,B] 内，并把流的越界保护设为 10B。起点由固定点 0、±1、±0.5 与 [−B,B] 上的均匀点组成；均匀点数量按 Descartes 符号变化数自适应，最多 32 个。若某个起点收敛，就得到一个根；若所有起点都停在驻点，则说明当前多项式可能已无实根，交由完整性门控处理。', first_indent=True)

heading('2.3  原多项式精修与重数修正', 2)
para('降次会把舍入误差逐步放大，因此每得到一个近似根，都要回到原始首一多项式 p 上精修。精修第一阶段是带回溯的阻尼牛顿法：只接受使 |p| 下降的步，步长连续折半直到残差下降或达到回溯上限。这样即使当前点离根较远，也不会一步跳到另一个根而污染后续降次。', first_indent=True)
para('对重根，普通牛顿法只有线性收敛。利用 p、p′、p″ 可以估计重数', first_indent=True)
add_formula([('m̂ = p′', 'i'), ('2', 'sup'), (' / (p′', 'i'), ('2', 'sup'), (' − p p″)', 'i')], 8)
para('在 m 重根附近 m̂→m。当 m̂ 接近整数 m₀≥2 且残差仍高于舍入下限时，改用修正步 x←x−m₀p/p′，可恢复二次收敛。若 m̂ 不接近整数，则保持普通牛顿步，避免在单根附近误用重数修正。', first_indent=True)

heading('2.4  降次、重数与高精度认证', 2)
para('确定一个根 r 后，用综合除法 q←q/(x−r) 降次。对升幂系数，Horner 形式的综合除法只需 O(n) 次运算；连续做 m 次即可除以 (x−r)ᵐ。代码先做一次降次，再检查 r 是否仍是商多项式的近似根：若 |q(r)|<10⁻⁶·scale(q)，则继续降次并累加重数。这里的 scale(q)=max(1,max|qᵢ|) 用于把残差归一化，避免系数整体缩放导致阈值失效。', first_indent=True)
para('降次循环给出的重数在临界情形下可能模棱两可。为此，当次数不超过 300 且精度参数允许时，算法把系数转成 Decimal，在 60、120、240 位精度下逐级认证：先用带回溯的牛顿法把根精修到高精度，再用局部对数斜率估计重数。若 r 是 m 重根，则对充分小的 η 有', first_indent=True)
add_formula([('m ≈ log', 'i'), ('2', 'sub'), (' |p(r+2η) / p(r+η)|，  η→0', 'i')], 9)
para('算法在 η=|r|·10⁻⁹ 到 |r|·10⁻² 的 8 个尺度上取样，要求连续两个尺度给出相同的整数估计才接受。这样重数成为系数本身的性质，而不是降次循环的偶然结果。对于数值上被拆成多个条目的重根，输出阶段再按位置聚类；合并容差为', first_indent=True)
add_formula([('δ', 'i'), ('m', 'sub'), (' = min(50 ε', ''), ('1/m', 'sup'), (', 10', ''), ('−3', 'sup'), (') · max(1, |r|)', 'i')], 10)
para('其中 ε≈2.22×10⁻¹⁶ 是双精度机器精度。只有当合并后的中心能被 Decimal 认证为某个整数重数时，才真正合并；否则保留原条目并给出警告，避免把两个靠得很近但不同的单根误并成一个重根。', first_indent=True)

heading('2.5  完整性门控与状态约定', 2)
para('求根算法最容易犯的错误，是在“没有找到根”时宣称“没有实根”。本求解器用两层证据避免这种误判。第一层是 Descartes 符号法则：对当前工作多项式 q，统计系数序列（忽略零）的符号变化数 V(q)，则 q 的正实根个数（计重数）不超过 V(q)，且与 V(q) 同奇偶。因此 V(q)=0 是“没有正实根”的严格证明；对 q(−x) 做同样统计，V(q(−x))=0 则证明没有负实根。若两者都为 0 且 q(0)≠0，就可以严格终止主循环。', first_indent=True)
para('第二层是采样兜底。若 Descartes 门控不能证明无根，而所有流起点都停滞，算法在 [−B,B] 上均匀取 16 个点。相邻两点若变号，由介值定理立刻得到存在实根的构造性证据，再用二分法求出该根；若找不到变号，算法不会宣称无根，而是把剩余部分标记为 unverified，并在警告中说明“流停滞、采样未发现变号”。', first_indent=True)
para('因此求解器返回三种主要状态：ok 表示所有根均已定位并通过认证；partial 表示根已找到但某些重数未完全认证；unverified 表示仍有剩余次数无法证明没有实根。另有 input_error、overflow_risk、degree_too_high 等输入保护状态。这样的“三态完整性契约”让调用者明确知道结果可信到什么程度。', first_indent=True)

heading('2.6  主流程', 2)
para('把上述模块串起来，得到如下伪代码。', first_indent=True)
add_code([
    'PolyRealRoots(a[0..n], tol):',
    '    a ← TrimHighZeros(a);  k ← CountLowZeros(a);  a ← a[k:]',
    '    a ← a / a[n]                       # 首一化',
    '    roots ← [(0, k)] if k > 0 else []',
    '    q ← a',
    '    while deg(q) ≥ 2:',
    '        V+ ← Descartes(q);  V− ← Descartes(q(−x))',
    '        if V+ = 0 and V− = 0 and q(0) ≠ 0: break',
    '        B ← FujiwaraBound(q);  starts ← BuildStarts(B, V+ + V−)',
    '        found ← None',
    '        for s in starts:',
    '            r, reason ← NewtonFlow(q, s, tol)',
    '            if reason = converged: found ← r; break',
    '        if found = None:',
    '            found ← SampleProbeAndBisect(q, B)',
    '            if found = None: mark unverified; break',
    '        r ← Polish(original_p, found)',
    '        r, m ← DeflateAndEstimate(q, r)',
    '        r, m ← DecimalCertify(original_p, r, m) if enabled',
    '        roots.append((r, m));  q ← q / (x − r)^m',
    '    if deg(q) = 1: roots.append((−q[0]/q[1], 1))',
    '    roots ← MergeClusters(roots);  Sort(roots)',
    '    return roots, status',
], '代码 1  求解器主流程伪代码', size=8.0)

heading('2.7  复杂度分析', 2)
para('设当前工作多项式次数为 m。一次 Horner 求值或求导为 O(m)，一次综合除法为 O(m)。单根搜索通常需要 k 步流迭代，k 是与 tol 有关的常数；找到该根后降次一次为 O(m)。对 n 个根求和，总时间为 O(n²k)，空间只需保存当前系数数组，为 O(n)。Decimal 认证只在次数不超过 300 且重数模棱两可时触发，不改变主路径的渐近复杂度。', first_indent=True)
add_table(
    ['操作', '单次成本', '次数', '总计'],
    [
        ['Horner 求 q、q′', 'O(m)', '每步迭代 1 次', 'O(mk)'],
        ['综合除法降次', 'O(m)', '每个根 1 次', 'O(n²)'],
        ['原多项式精修', 'O(n)', '每个根 ≤50 步', 'O(n²)'],
        ['聚类与排序', 'O(r log r)', 'r≤n 个输出根', 'O(n log n)'],
        ['Decimal 认证', 'O(n·m)', '仅小次数触发', '不进入主复杂度'],
    ],
    [5.6, 4.2, 3.2, 2.8],
    '表 2  主要操作的时间复杂度'
)

# ---------------- 3 ----------------
heading('3  数值计算结果', 1)
heading('3.1  计算环境与调用方式', 2)
para('计算在 Windows 11、Python 3.10.16（conda 环境 test_env）、NumPy 2.1.2 下完成。求解器只依赖 Python 标准库；NumPy 仅用于独立的 numpy.roots 交叉验证。题目多项式的调用方式如下。', first_indent=True)
add_code([
    'from poly_roots import poly_real_roots',
    '',
    '# 升幂系数：5 − 5x − x² − 6x³ + 0·x⁴ + x⁵',
    'coeffs = [5.0, -5.0, -1.0, -6.0, 0.0, 1.0]',
    'roots = poly_real_roots(coeffs, tol=1e-12)',
], '代码 2  题目多项式的调用', size=8.5)
para('运行 solve_p5.py 的主要输出如下（节选）：', first_indent=True)
add_code([
    'real roots found: 3 (degree 5)',
    '   1     -2.579714343403    mult=1    residual=7.105e-15',
    '   2      0.634113250651    mult=1    residual=8.882e-16',
    '   3      2.614244150443    mult=1    residual=3.553e-15',
    'Vieta check: sum of real roots = 0.668643057691388',
    'numpy.roots cross-check: agreement with our solver: True',
    'remaining complex pair:',
    '   -0.334321528846 + 1.028309281208i',
    '   -0.334321528846 - 1.028309281208i',
], '代码 3  solve_p5.py 运行输出（节选）', size=8.2)

heading('3.2  实根与残差', 2)
para('三个实根按升序排列，重数均为 1。表 3 给出更高精度的根、残差、归一化残差和该点的一阶导数。归一化残差用 |p₅(r)|/max(1,max|aᵢ|)=|p₅(r)|/6 计算，便于与系数尺度无关地判断精度。', first_indent=True)
add_table(
    ['序号', '根 rᵢ', '重数', 'p₅(rᵢ)', '|p₅(rᵢ)|/6', 'p₅′(rᵢ)'],
    [
        ['1', '−2.579714343402782', '1', '−7.105×10⁻¹⁵', '1.184×10⁻¹⁵', '101.810965556'],
        ['2', '0.634113250650736', '1', '8.882×10⁻¹⁶', '1.480×10⁻¹⁶', '−12.697599065'],
        ['3', '2.614244150443434', '1', '−3.553×10⁻¹⁵', '5.921×10⁻¹⁶', '100.291008619'],
    ],
    [1.2, 4.4, 1.5, 3.4, 3.0, 2.3],
    '表 3  p₅(x) 的三个实根及其残差'
)
para('三个根的绝对残差都在 10⁻¹⁵ 量级，归一化残差在 10⁻¹⁶ 到 10⁻¹⁵ 之间，已经接近双精度浮点的舍入极限。若用一阶误差估计 |δr|≈|p(r)|/|p′(r)|，三个根的位置误差分别约为 7.0×10⁻¹⁷、7.0×10⁻¹⁷ 和 3.5×10⁻¹⁷，均小于一个机器 epsilon 对应的量级。', first_indent=True)

heading('3.3  复根与 NumPy 交叉验证', 2)
para('numpy.roots 通过求伴随矩阵的特征值得到全部 5 个根。表 4 将它与本文求解器的实根结果并列比较。两者在 12 位小数上完全一致，最大差异约 2.7×10⁻¹⁵。', first_indent=True)
add_table(
    ['根', '本文求解器', 'numpy.roots', '绝对差'],
    [
        ['r₁', '−2.579714343403', '−2.579714343403', '2.66×10⁻¹⁵'],
        ['r₂', '0.634113250651', '0.634113250651', '1.11×10⁻¹⁶'],
        ['r₃', '2.614244150443', '2.614244150443', '2.66×10⁻¹⁵'],
        ['复根对', '—（不返回）', '−0.334321528846±1.028309281208i', '—'],
    ],
    [3.0, 4.8, 5.2, 2.8],
    '表 4  实根与 numpy.roots 的交叉验证'
)
para('numpy.roots 还给出剩余的一对共轭复根 −0.334321528846±1.028309281208i。本文求解器的接口只返回实根，因此复根不出现在 roots 列表中；它们的位置用于后续 Vieta 校验和结果解释。', first_indent=True)

heading('3.4  因式分解与 Vieta 关系', 2)
para('依次除以 (x−r₂)、(x−r₁)、(x−r₃) 后，剩余二次因子为', first_indent=True)
add_formula([('q', 'i'), ('2', 'sub'), ('(x) = x', 'i'), ('2', 'sup'), (' + 0.668643057691388x + 1.169190862467746', 'i')], 11)
para('其判别式为 Δ=0.668643057691388²−4×1.169190862467746≈−4.229679911272<0，因此该二次因子没有实根，两个根为 −0.334321528846±1.028309281208i。这与 numpy.roots 的结果一致。于是 p₅ 的完整因式分解为', first_indent=True)
add_formula([('p', 'i'), ('5', 'sub'), ('(x) = (x−r', 'i'), ('1', 'sub'), (')(x−r', 'i'), ('2', 'sub'), (')(x−r', 'i'), ('3', 'sub'), (')(x', 'i'), ('2', 'sup'), (' + 0.668643057691x + 1.169190862468)', 'i')], 12)
para('把 5 个根（3 个实根加一对复根）代入 Vieta 关系，结果如表 5。所有初等对称和都与首一多项式的系数一致，最大误差约 2.7×10⁻¹⁵。', first_indent=True)
add_table(
    ['Vieta 关系', '计算值（双精度）', '理论值'],
    [
        ['Σ rᵢ', '−1.11×10⁻¹⁶', '0'],
        ['Σᵢ<ⱼ rᵢrⱼ', '−6.000000000000001', '−6'],
        ['Σᵢ<ⱼ<ₖ rᵢrⱼrₖ', '1.000000000000000', '1'],
        ['Σᵢ<ⱼ<ₖ<ₗ rᵢrⱼrₖrₗ', '−4.999999999999998', '−5'],
        ['Π rᵢ', '−4.999999999999997', '−5'],
    ],
    [6.0, 5.2, 4.6],
    '表 5  p₅ 的 Vieta 关系校验'
)
para('其中实根之和为 0.668643057691388，而复根对的实部之和为 2×(−0.334321528846)=−0.668643057691388，两者相加为 0，正好满足一次项系数为 0 的条件。这从整体上验证了实根和复根的位置没有互相错配。', first_indent=True)

heading('3.5  迭代过程与收敛曲线', 2)
para('求解器按降次阶段依次工作。表 6 记录每个阶段的工作多项式次数、Descartes 计数、首次收敛的起点、流迭代步数和输出根。图 2 给出前三个阶段的残差下降曲线。', first_indent=True)
add_table(
    ['阶段', '次数', 'V+', 'V−', '收敛起点', '流步数', '输出根', '最终 |p₅|'],
    [
        ['1', '5', '2', '3', '0.000000', '10', '0.634113250650736', '8.88×10⁻¹⁶'],
        ['2', '4', '1', '3', '−4.731976', '11', '−2.579714343402782', '7.11×10⁻¹⁵'],
        ['3', '3', '1', '2', '−1.297067', '12', '2.614244150443434', '3.55×10⁻¹⁵'],
        ['4', '2', '0', '2', '全部停滞于 −0.334322', '—', '无实根', 'Δ<0'],
    ],
    [1.2, 2.2, 1.1, 1.1, 3.0, 2.0, 3.2, 2.0],
    '表 6  降次各阶段的求解过程'
)
para('第一阶段从 x=0 出发，10 步后到达 0.634113，残差从 5 降到 3.8×10⁻¹²；第二阶段前五个起点都停在 −0.402132 附近，第六个起点 −4.731976 在 11 步后到达 −2.579714；第三阶段前七个起点停在 −0.134749 附近，第八个起点 −1.297067 在 12 步后到达 2.614244。第四阶段只剩二次因子，11 个起点全部停在 −0.334322，恰好是该二次因子复根对的实部；采样也没有发现变号，因此求解器把剩余部分标记为 unverified，随后用判别式完成严格判定。', first_indent=True)
add_figure('report_assets/fig2_convergence.png', 14.2, '图 2  三个降次阶段的连续牛顿流残差下降曲线')
p = para('图 2 的纵轴是当前阶段工作多项式的残差 |qₖ(xₖ)|（对数坐标）。三条曲线都在 10 到 12 个接受步内从 10⁰ 到 10² 量级降到 10⁻¹² 到 10⁻¹⁴，且越接近根下降越快，呈现典型的超线性收敛特征。图中只记录被接受的步，因此曲线单调下降；迭代过程中被拒绝的试探步可能使残差暂时上升，但不会出现在图中。', first_indent=True)
p.paragraph_format.keep_together = True

heading('3.6  正确性测试与性能', 2)
para('除题目多项式外，还用两组测试检查通用性。第一组是 10 个已知根的小规模单元测试，覆盖单根、重根、零根、无实根、Wilkinson 型病态多项式和系数整体缩放；第二组是表驱动的 35 个用例，其中 28 个可运行用例全部通过，0 个错误，7 个因零多项式或系数超出 double 表示范围而按特殊情形跳过。表 7 列出部分代表性结果。', first_indent=True)
add_table(
    ['测试用例', '期望根（重数）', '结果', '最大相对残差'],
    [
        ['题目 p₅', '3 个单根', '通过', '1.18×10⁻¹⁵'],
        ['(x−1)⋯(x−5)', '1,2,3,4,5', '通过', '1.50×10⁻¹⁵'],
        ['(x−2)³(x+1)²', '−1(2), 2(3)', '通过', '0'],
        ['x²+1', '无实根', '通过', '—'],
        ['(x−1)⋯(x−10)', '1,2,…,10', '通过', '1.56×10⁻¹³'],
        ['x²(3x+2)', '0(2), −2/3', '通过', '0'],
    ],
    [5.2, 5.2, 1.8, 3.6],
    '表 7  代表性测试结果'
)
para('性能方面，在本机上对 p₅ 连续调用 200 次，平均耗时约 2.1 ms（含预处理、三次降次、重数认证和输出排序）。这个量级远低于课程作业的交互需求；主路径的 O(n²) 复杂度也保证了次数增加到几十时仍然可用。', first_indent=True)

# ---------------- 4 ----------------
heading('4  计算结果的说明', 1)
heading('4.1  为什么恰好是 3 个实根', 2)
para('仅凭“求出了 3 个根”还不足以说明没有第 4、第 5 个实根。p₅ 的导数为 p₅′(x)=5x⁴−18x²−2x−5。该四次方程恰有两个实根 −1.9141469335 和 2.0114711357，另外两个根为共轭复根；因此 p₅ 在实轴上只有两个驻点，被分成三个单调区间。表 8 给出每个区间的单调性和端点趋势。', first_indent=True)
add_table(
    ['区间', 'p₅′ 符号', 'p₅ 单调性', '端点趋势', '实根数'],
    [
        ['(−∞, −1.9141)', '+', '单调递增', '−∞ → 27.2903', '1'],
        ['(−1.9141, 2.0115)', '−', '单调递减', '27.2903 → −25.0058', '1'],
        ['(2.0115, +∞)', '+', '单调递增', '−25.0058 → +∞', '1'],
    ],
    [3.8, 2.0, 2.4, 5.4, 2.2],
    '表 8  p₅ 的单调区间与实根计数'
)
para('在每个区间内函数严格单调，且两端函数值异号，由介值定理各有一个实根；三个区间之外没有别的驻点，因此不可能再有实根。两个驻点值 27.2903 和 −25.0058 的符号决定了三次穿越：从左到右依次是“上升穿过 0”“下降穿过 0”“上升穿过 0”。这与图 1 的图形完全一致。', first_indent=True)
add_figure('report_assets/fig1_p5_function.png', 14.6, '图 1  p₅(x) 与 p₅′(x) 的图形及实根位置')

heading('4.2  精度、条件数与误差来源', 2)
para('三个根都是单根，且 p₅′(r) 分别为 101.81、−12.70、100.29，远离零。对单根，残差与位置误差的一阶关系是 δr≈−p(r)/p′(r)，因此即使残差在 10⁻¹⁵ 量级，位置误差也只有 10⁻¹⁷ 量级。表 3 的归一化残差和表 4 的 NumPy 差异都说明结果已经达到双精度的有效极限。', first_indent=True)
para('误差主要来自三处：系数以 double 存储时的初始舍入；Horner 求值在根附近的消去误差；逐次降次把前一个根的误差传给商多项式。算法用“原多项式精修”消除第三项，用“首一化 + 归一化残差”减轻第一项，用“高精度重数认证”处理重根情形。对于本题的单根，这三项都不构成实质影响。', first_indent=True)

heading('4.3  复根的来源与流的停滞', 2)
para('第四阶段的工作多项式是 q₂(x)=x²+0.668643057691x+1.169190862468。它的顶点在 x=−0.334321528846，恰好是复根对的实部；在该点 q₂′=0 而 q₂>0，所以连续牛顿流的分母趋近于零、步长不断下溢，所有起点都停在这个驻点。这不是求根失败，而是“该二次因子没有实根”的几何表现：流只能到达 |q₂| 的极小值点，无法到达零点。', first_indent=True)
para('由于 V(q₂)=0 只证明没有正实根，而 V(q₂(−x))=2 不能证明没有负实根，Descartes 门控不能单独结束循环；采样 16 个点也没有发现变号。求解器因此返回 unverified 状态，而不是错误地宣称“无实根”。报告进一步计算判别式 Δ=−4.22968<0，才给出“该因子无实根”的严格结论。这个例子说明：状态字段不是装饰，它精确记录了算法在哪一步有证明、哪一步只有经验证据。', first_indent=True)

heading('4.4  重数、局限与适用边界', 2)
para('本题的 3 个根都是单根，求解器返回的重数均为 1。为确认没有漏掉重根，可计算 gcd(p₅,p₅′)=1，说明 p₅ 与导数没有公共根，故不存在重根。重数判定逻辑本身已在 (x−2)³(x+1)²、x²(3x+2) 等用例上验证：前者返回 −1(2)、2(3)，后者返回 0(2)、−2/3。', first_indent=True)
para('需要明确算法的边界。第一，fast 完整性模式不是 Sturm 序列或 VCA 那样的绝对完备算法：Descartes 门控能给出严格的无根证明，采样只能给出“有根”的构造性证据，不能给出“无根”的证明；因此证据不足时会返回 unverified，而不是假装确定。第二，m 重根在 double 系数下的位置精度本质上受 ε 的 1/m 次方限制，例如三重根只能达到约 6×10⁻⁶；Decimal 认证可以恢复重数，但无法凭空恢复系数中已经丢失的信息。第三，主路径是 O(n²)，适合中低次多项式；次数达到数千时，稠密系数和逐次降次都不再经济。第四，展开后的高重根可能产生超过 1.8×10³⁰⁸ 的系数，这在 double 输入阶段就会溢出，属于接口表示问题，而不是迭代算法本身能解决的范围。', first_indent=True)
para('在工程使用中，建议把本求解器定位为“中低次、重根多、需要重数和可信状态”的通用工具；若需要处理任意高次或极端病态的多项式，可在现有框架上增加 Sturm 序列、二次因子的闭式判定或任意精度系数入口，而无需改变主求解流程。', first_indent=True)

heading('4.5  结果可靠性小结', 2)
para('本题结果通过了四类相互独立的检查：逐根残差达到 10⁻¹⁵ 量级；与 numpy.roots 的实根差异小于 10⁻¹²；Vieta 关系与因式分解一致；导数单调性分析证明实根恰好为 3 个。四条证据链相互吻合，说明输出不是数值巧合。复根对的位置也由二次因子和 Vieta 关系双重确认。', first_indent=True)

# ---------------- 5 ----------------
heading('5  工程意义与应用思考', 1)
para('多项式方程是工程建模中最常见的一类标量方程。虽然一元四次以下存在根式解，但实际工程系数很少适合直接套公式，五次及以上更不存在一般闭式解，必须依赖数值方法。一个不需要初值、能枚举全部实根并给出重数的通用求解器，其价值不在于替代某个局部迭代，而在于把“求实根”变成可靠的基础算子，嵌入更大的仿真、设计与控制流程。', first_indent=True)
para('本求解器特别适合那些只关心实根、且往往不能遗漏任一实根的工程问题。典型场景如表 9 所示。', first_indent=True)
add_table(
    ['领域', '出现的多项式', '实根含义'],
    [
        ['自动控制与系统稳定性', '特征方程 det(sI−A)=0', '正实根对应非周期发散模态；重根对应临界稳定'],
        ['化学反应与平衡', '质量作用与物料衡算多项式', '正实根是物理解；多个正根对应多稳态'],
        ['结构力学与振动', '频率方程、屈曲载荷方程', '实根给出临界转速、屈曲荷载等设计边界'],
        ['电气与电子工程', '含二极管或非线性电阻的直流稳态方程', '实根是直流工作点；多根对应多个工作状态'],
        ['工程优化与极值', '目标函数导数为零的多项式', '实根是驻点候选，可结合符号判别求出全部极值'],
        ['几何建模与图形仿真', '曲面或曲线交线的多项式方程', '实根为交点参数，决定是否相交及交点个数'],
        ['实时与嵌入式仿真', '参数扫描中反复出现的小次数多项式', '作为无初值的底层算子，批量且快速地完成大量求根'],
    ],
    [3.2, 6.2, 6.4],
    '表 9  多项式实根求解的典型工程应用'
)
para('这些场景有两个共同点。其一，只有实根具有物理或设计意义——浓度、荷载、工作点必须为实数，负数或复数值往往被直接剔除；其二，漏掉一个实根，就可能漏掉一个稳态、一个临界点或一个可行解。因此“求全部实根”比“只求一个根”有质的区别，而重数信息在判断临界稳定、多重平衡等退化情形时不可替代。', first_indent=True)
para('从软件与算法工程的角度看，本求解器的意义还体现在四个方面。第一，接口是无初值的通用子函数，可以被优化、参数扫描、蒙特卡洛等上层流程反复调用。第二，返回值带残差、重数和 status（ok/partial/unverified），把“能找到”与“不能证明没有”明确区分开，便于工程审计与决策，而不会把“找不到”误当成“不存在”。第三，时间复杂度 O(n²k)、空间复杂度 O(n)，实测求解题目五次多项式约 2.1 ms，适合实时控制、嵌入式或大规模仿真中对成千上万个多项式求根。第四，它可以与 numpy.roots 等伴随矩阵法互补：本算子负责实根的全枚举、重数与状态诊断，伴随矩阵法则负责给出全部复根。', first_indent=True)
para('当然，它也有明确的工程边界：接口只返回实根，不能直接给出复根；采用双精度实现，不适合高于数百次的稠密多项式或系数超出 double 表示范围的问题；fast 模式的完整性不是 Sturm 级的绝对证明，而是“有证据时严格、无证据时如实标注”。因此在工程上应把它定位为“中低次、实根敏感、需要重数与可信状态”的基础求解算子，需要复根或绝对完备性时再与伴随矩阵法、Sturm 序列或区间算术配和使用。', first_indent=True)
para('综合来看，这个求解器最有意义的并不是“比某个迭代法更快更准”，而是把求全部实根这件容易被当作平凡小事的基础工作，做成了一个可调用、可验证、可诊断的稳定部件——这正是工程软件愿意长期依赖它的原因。', first_indent=True)

# ---------------- 6 ----------------
heading('6  结论', 1)
para('本文设计并实现了一个求解一元 n 次实系数多项式全部实根的通用求解器 poly_real_roots。算法以连续牛顿流完成单根定位，以自适应步长和 Levenberg 正则处理驻点，以原多项式精修和修正牛顿步处理重根，以综合除法降次，以 Decimal 局部斜率认证重数，并用 Descartes 符号变化、采样变号和聚类规范化给出完整性证据与状态标记。主路径时间为 O(n²k)、空间为 O(n)，适合中低次多项式的工程计算。', first_indent=True)
para('对题目多项式 p₅(x)=x⁵−6x³−x²−5x+5，求得三个单重实根 −2.579714343403、0.634113250651、2.614244150443；剩余二次因子的判别式为负，另外两个根为 −0.334321528846±1.028309281208i。三个实根的残差均不超过 7.2×10⁻¹⁵，与 NumPy 的差异小于 10⁻¹²，Vieta 关系和导数单调性分析均验证了“恰有 3 个实根”的结论。', first_indent=True)

# ---------------- Appendix ----------------
heading('附录 A  接口与返回值', 1)
para('求解器对外暴露的主函数签名如下。系数必须按升幂排列；tol 是残差归一化阈值；canonical=True 时返回按位置排序、同一根只出现一次的列表；raw=True 可保留未合并的调试条目；diagnostics=True 时返回 RootResult，其中包含 status、warnings 和 certified 字段。', first_indent=True)
add_code([
    'poly_real_roots(coeffs, tol=1e-12, *,',
    '                canonical=True, cluster_tol=None,',
    '                precision="auto", raw=False,',
    '                diagnostics=False, max_degree=None,',
    '                completeness="fast", strict=False)',
], '代码 4  主函数签名', size=8.4)
para('默认返回值为 [(r₀,m₀),(r₁,m₁),…]，其中 rᵢ 是实根，mᵢ 是重数，按 rᵢ 升序排列。需要诊断信息时，返回 RootResult(roots, status, warnings, certified)：status 说明整体可信度，warnings 记录流停滞、重数未认证、聚类失败等信息，certified 表示返回的根是否全部经过认证。', first_indent=True)

heading('附录 B  文件与复现方式', 1)
para('复现题目结果所需文件如下：poly_roots.py 是通用求解器；solve_p5.py 是题目驱动脚本；test_poly_roots.py 是 10 个已知根单元测试；test_report_table.py 与测试报告_用例表.txt 是表驱动测试及结果。激活环境后执行 python solve_p5.py 即可得到第 3 节的输出。', first_indent=True)
add_code([
    'conda activate test_env',
    'python solve_p5.py',
    'python test_poly_roots.py',
], '代码 5  复现命令', size=8.4)

# Save
doc.save(OUT)
print('written', os.path.abspath(OUT))










