"""Build the one-page PDF from resume.qmd, using the supplied sample's layout.
Run: python scripts/build_resume_pdf.py [source.qmd] [output.pdf]
Requires reportlab, pypdf, and Liberation Serif (or RESUME_FONT_DIR).
The website retains full history; the PDF selects its four principal roles.
"""
from pathlib import Path
import html, os, re, sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether, HRFlowable
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'resume.qmd'
OUTPUT = Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'resume.pdf'
BASE = 'https://ajay8005.github.io/personal-website/'
WIDTH = A4[0]-76
FONT_DIR = Path(os.environ.get('RESUME_FONT_DIR','/usr/share/fonts/truetype/liberation2'))
if not (FONT_DIR/'LiberationSerif-Regular.ttf').exists():
    FONT_DIR = Path(os.environ.get('CODEX_PRIMARY_RUNTIME_ROOT','/opt/codex/runtimes/codex-primary-runtime'))/'dependencies/native/libreoffice-headless/libreoffice/share/fonts/truetype'
for name, file in [('Resume','LiberationSerif-Regular.ttf'),('Resume-Bold','LiberationSerif-Bold.ttf'),('Resume-Italic','LiberationSerif-Italic.ttf'),('Resume-BoldItalic','LiberationSerif-BoldItalic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT_DIR/file)))
pdfmetrics.registerFontFamily('Resume',normal='Resume',bold='Resume-Bold',italic='Resume-Italic',boldItalic='Resume-BoldItalic')
body = ParagraphStyle('Body',fontName='Resume',fontSize=9.7,leading=10.8,spaceAfter=0)
bullet = ParagraphStyle('Bullet',parent=body,leftIndent=9,bulletIndent=0,spaceAfter=1.7)
heading = ParagraphStyle('Heading',parent=body,fontName='Resume-Bold',fontSize=10.1,leading=11.5)
right_bold = ParagraphStyle('RightBold',parent=heading,alignment=TA_RIGHT)
right = ParagraphStyle('Right',parent=body,alignment=TA_RIGHT)
section_style = ParagraphStyle('Section',parent=body,fontSize=13.2,leading=14.4,spaceBefore=9,spaceAfter=1,keepWithNext=True)

def markup(text):
    text = html.escape(re.sub(r'<[^>]+>','',html.unescape(text.strip())))
    text = re.sub(r'\[([^]]+)\]\(([^)]+)\)',lambda m:'<link href="'+BASE+m[2].replace('.qmd','.html')+'">'+m[1]+'</link>',text)
    return re.sub(r'\*\*(.*?)\*\*',r'<b>\1</b>',text)

def para(text,style=body):
    return Paragraph(markup(text),style)

def section(title):
    return [para(title,section_style),HRFlowable(width='100%',thickness=.45,color=colors.black,spaceAfter=2)]

def row(left,right_text,left_style=body,right_style=right,split=.78):
    t=Table([[Paragraph(left,left_style),para(right_text,right_style)]],colWidths=[WIDTH*split,WIDTH*(1-split)])
    t.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),0),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
    return t

def entry(block):
    title=re.search(r'^### (.+)$',block,re.M)[1]
    role=re.search(r'<p class="role">(.*?)</p>',block)[1]
    dates,location=html.unescape(re.search(r'<p class="date">(.*?)</p>',block)[1]).split(' · ',1)
    for month,short in [('January','Jan'),('February','Feb'),('March','Mar'),('April','Apr'),('June','Jun'),('July','Jul'),('August','Aug'),('September','Sep'),('October','Oct'),('November','Nov'),('December','Dec')]:
        dates=dates.replace(month,short)
    role=markup(role)
    if title.startswith('Crestline'):
        role+=' (<link href="'+BASE+'finance.html"><i>Interactive Dashboard</i></link>)'
    lines=[row(markup(title),dates,heading,right_bold,.70),row(role,location,split=.86),Spacer(1,3)]
    for b in re.findall(r'^- (.+)$',block,re.M):
        if 'Explore the interactive' not in b:
            lines.append(Paragraph(markup(b),bullet,bulletText='•'))
    return [KeepTogether(lines),Spacer(1,4)]

def footer(canvas,doc):
    canvas.setFont('Resume',8)
    canvas.drawCentredString(A4[0]/2,15,str(doc.page))

source=SOURCE.read_text(encoding='utf-8')
assert not re.search(r'\bTeX\b',source)
parts=re.split(r'^## (.+)$',source,flags=re.M)
sections=dict(zip(parts[1::2],parts[2::2]))
story=[Paragraph('AJAY SHARMA',ParagraphStyle('Name',parent=body,fontSize=24,leading=25,alignment=TA_CENTER)),
    Paragraph('Phone: (510) 575-8812 &nbsp; | &nbsp; Email: <link href="mailto:ajay.sharma@berkeley.edu">ajay.sharma@berkeley.edu</link> &nbsp; | &nbsp; LinkedIn: <link href="https://www.linkedin.com/in/asharma2718">linkedin.com/in/asharma2718</link>',ParagraphStyle('Contact',parent=body,fontSize=9.2,leading=10.3,alignment=TA_CENTER)),
    Paragraph('Website: <link href="'+BASE+'">ajay8005.github.io/personal-website</link>',ParagraphStyle('Website',parent=body,fontSize=9.2,leading=10.3,alignment=TA_CENTER))]
story+=section('SUMMARY')
story.append(Paragraph(markup(re.search(r'<p class="summary-copy">(.*?)</p>',sections['Professional Summary'])[1]),bullet,bulletText='•'))
story+=section('EDUCATION')
for item in re.split(r'(?=^### )',sections['Education'],flags=re.M)[1:]:
    story+=entry(item)
story+=section('EXPERIENCE')
for item in re.split(r'(?=^### )',sections['Professional Experience'],flags=re.M)[1:]:
    story+=entry(item)
story+=section('SKILLS')
# Concise phrasing of the website's eight categories, without its card layout.
skills=[
    '<b>Finance &amp; Business Tools:</b> Microsoft Office, Google Workspace, Power BI; Excel formulas, PivotTables, lookups, conditional formatting.',
    '<b>Financial Analysis:</b> Budget vs. Actual Analysis, KPI Reporting, Forecasting, Financial Modeling, Sensitivity Analysis.',
    '<b>Programming:</b> Intermediate: Python, SQL, R, LaTeX; Basic: Java, C++, MATLAB.',
    '<b>AI &amp; Data Tools:</b> LLMs &amp; Prompt Engineering (ChatGPT, Claude, Gemini), Git, CSV-based data workflows.',
    '<b>Statistical Methods:</b> Hypothesis Testing, Linear &amp; Generalized Linear Models, ANOVA/ANCOVA, Maximum Likelihood Estimation, Bootstrap Methods, Model Selection &amp; Diagnostics, Quality Improvement.',
    '<b>Additional:</b> U.S. Citizen; Project Management, Quality Control, Detail-Oriented, Written &amp; Oral Communication, Quick Learner, Adaptable.',
]
story.extend(Paragraph(s,bullet,bulletText='•') for s in skills)
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
doc=SimpleDocTemplate(str(OUTPUT),pagesize=A4,leftMargin=32,rightMargin=32,topMargin=24,bottomMargin=27,title='Ajay Sharma - Resume',author='Ajay Sharma')
doc.build(story,onFirstPage=footer,onLaterPages=footer)
pages=len(PdfReader(OUTPUT).pages)
print(f'{OUTPUT}: {pages} page(s)')
assert pages==1,'Resume must remain one page; revise spacing before publishing.'
