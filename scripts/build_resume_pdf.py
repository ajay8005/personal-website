"""Build the downloadable PDF from the website's canonical resume.qmd.

Run: python scripts/build_resume_pdf.py [source.qmd] [output.pdf]
Requires reportlab. Contact details are retained from the original résumé PDF.
"""
from pathlib import Path
import html
import re
import sys
import os

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    KeepTogether, PageBreak, HRFlowable,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'resume.qmd'
OUTPUT = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'resume.pdf'
BASE = 'https://ajay8005.github.io/personal-website/'
BLUE = colors.HexColor('#003262')
INK = colors.HexColor('#172533')
MUTED = colors.HexColor('#536575')
WIDTH = A4[0] - 88  # account for the document frame's 6-point inner padding

# Embed fonts so the PDF looks the same in browsers and downloaded viewers.
FONT_DIR = Path(os.environ.get('RESUME_FONT_DIR', '/usr/share/fonts/truetype/liberation2'))
if not (FONT_DIR / 'LiberationSerif-Regular.ttf').exists():
    FONT_DIR = Path(os.environ.get('CODEX_PRIMARY_RUNTIME_ROOT', '/opt/codex/runtimes/codex-primary-runtime')) / 'dependencies/native/libreoffice-headless/libreoffice/share/fonts/truetype'
for name, filename in [('Resume', 'LiberationSerif-Regular.ttf'),
                       ('Resume-Bold', 'LiberationSerif-Bold.ttf'),
                       ('Resume-Italic', 'LiberationSerif-Italic.ttf'),
                       ('Resume-BoldItalic', 'LiberationSerif-BoldItalic.ttf')]:
    pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
pdfmetrics.registerFontFamily('Resume', normal='Resume', bold='Resume-Bold',
                              italic='Resume-Italic', boldItalic='Resume-BoldItalic')


def markup(text):
    text = html.unescape(text.strip())
    text = re.sub(r'<[^>]+>', '', text)
    text = html.escape(text)
    text = re.sub(r'\[([^]]+)\]\(([^)]+)\)',
                  lambda m: '<link href="' + BASE + m[2].replace('.qmd', '.html') + '">' + m[1] + '</link>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
    return text


body = ParagraphStyle('Body', fontName='Resume', fontSize=10,
                      leading=11.8, textColor=INK, spaceAfter=2)
bullet = ParagraphStyle('Bullet', parent=body, leftIndent=9, bulletIndent=0,
                        spaceAfter=2.3)
role_style = ParagraphStyle('Role', parent=body, fontName='Resume-Italic',
                            fontSize=9.5, leading=10.8, spaceAfter=2)
date_style = ParagraphStyle('Date', parent=role_style, alignment=TA_RIGHT,
                            textColor=MUTED)
heading_style = ParagraphStyle('Heading', parent=body, fontName='Resume-Bold',
                               fontSize=10.8, leading=12.5, textColor=BLUE,
                               spaceAfter=0)
section_style = ParagraphStyle('Section', parent=heading_style, fontSize=12,
                               leading=14, spaceBefore=9, spaceAfter=3,
                               keepWithNext=True)
skill_style = ParagraphStyle('Skill', parent=body, fontSize=10, leading=12.5,
                             spaceAfter=0)


def p(text, style=body):
    return Paragraph(markup(text), style)


def section(title):
    return [p(title.upper(), section_style), HRFlowable(width='100%', thickness=.6,
            color=BLUE, spaceAfter=5)]


def entry(block):
    title = re.search(r'^### (.+)$', block, re.M)[1]
    role = re.search(r'<p class="role">(.*?)</p>', block)[1]
    date = html.unescape(re.search(r'<p class="date">(.*?)</p>', block)[1])
    dates, location = date.split(' · ', 1)
    # Use a full-width title so long degree/project names never collide with dates.
    header = p(title, heading_style)
    metadata = Table([[p(role, role_style), p(dates + ' | ' + location, date_style)]],
                     colWidths=[WIDTH * .54, WIDTH * .46])
    metadata.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'TOP'),
                                 ('LEFTPADDING', (0, 0), (-1, -1), 0),
                                 ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                                 ('TOPPADDING', (0, 0), (-1, -1), 1),
                                 ('BOTTOMPADDING', (0, 0), (-1, -1), 0)]))
    bullets = [Paragraph(markup(t), bullet, bulletText='•')
               for t in re.findall(r'^- (.+)$', block, re.M)]
    return [KeepTogether([header, metadata] + bullets), Spacer(1, 3)]


def skills(block):
    cards = re.findall(r'<div class="skill-card">(.*?)</div>', block, re.S)
    assert len(cards) == 8, 'Expected exactly eight skill categories'
    cells = []
    for card in cards:
        title = re.search(r'<strong>(.*?)</strong>', card, re.S)[1]
        content = re.sub(r'<strong>.*?</strong>', '', card, count=1, flags=re.S)
        items = re.findall(r'<li>(.*?)</li>', content, re.S)
        plain = re.sub(r'<ul>.*?</ul>', '', content, flags=re.S).strip()
        text = '<font color="#003262"><b>' + markup(title) + '</b></font>'
        if plain:
            text += '<br/>' + markup(plain)
        for item in items:
            text += '<br/>• ' + markup(item)
        cells.append(Paragraph(text, skill_style))
    table = Table([cells[i:i+2] for i in range(0, 8, 2)], colWidths=[WIDTH/2]*2)
    table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#F5F8FB')),
        ('BOX', (0, 0), (-1, -1), .4, colors.HexColor('#D7E1EB')),
        ('INNERGRID', (0, 0), (-1, -1), .4, colors.HexColor('#D7E1EB')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    return table


def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor('#D7E1EB'))
    canvas.line(38, 31, A4[0]-38, 31)
    canvas.setFont('Resume', 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(38, 20, 'Ajay Sharma | Resume')
    canvas.drawRightString(A4[0]-38, 20, str(doc.page))
    canvas.restoreState()


source = SOURCE.read_text(encoding='utf-8')
assert not re.search(r'\bTeX\b', source), 'Use LaTeX in the canonical website source'
parts = re.split(r'^## (.+)$', source, flags=re.M)
sections = dict(zip(parts[1::2], parts[2::2]))
story = [Paragraph('AJAY SHARMA', ParagraphStyle('Name', fontName='Resume-Bold',
          fontSize=23, leading=26, alignment=TA_CENTER, textColor=BLUE)),
    Paragraph('(510) 575-8812 | <link href="mailto:ajay.sharma@berkeley.edu">ajay.sharma@berkeley.edu</link>',
              ParagraphStyle('Contact', parent=body, fontSize=9.5, leading=12, alignment=TA_CENTER)),
    Paragraph('<link href="https://www.linkedin.com/in/asharma2718">linkedin.com/in/asharma2718</link> | '
              '<link href="'+BASE+'">ajay8005.github.io/personal-website</link>',
              ParagraphStyle('Links', parent=body, fontSize=9.5, leading=12, alignment=TA_CENTER))]

for title, block in sections.items():
    if title == 'Additional Teaching Experience':
        if isinstance(story[-1], Spacer):
            story.pop()
        story += [PageBreak(), p('AJAY SHARMA', heading_style), Spacer(1, 2)]
    story += section(title)
    if title == 'Professional Summary':
        story.append(p(re.search(r'<p class="summary-copy">(.*?)</p>', block)[1]))
    elif title == 'Skills & Additional Information':
        story.append(skills(block))
    else:
        for item in re.split(r'(?=^### )', block, flags=re.M)[1:]:
            story += entry(item)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=38, leftMargin=38,
        topMargin=32, bottomMargin=40, title='Ajay Sharma - Resume', author='Ajay Sharma')
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUTPUT)
