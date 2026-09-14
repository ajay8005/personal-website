"""Build the one-page resume with pdfLaTeX and genuine Computer Modern.
Run: python scripts/build_resume_pdf.py [source.qmd] [output.pdf]
Requires pdflatex, geometry, enumitem, microtype, hyperref, pypdf.
An editable .tex is written alongside the PDF. The website keeps full history.
"""
from pathlib import Path
import html, re, subprocess, sys, tempfile, shutil
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'resume.qmd'
OUTPUT=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'resume.pdf'
BASE='https://ajay8005.github.io/personal-website/'

def tex(text):
    text=re.sub(r'<[^>]+>','',html.unescape(text.strip()))
    text=re.sub(r'\[([^]]+)\]\([^)]+\)',r'\1',text).replace('**','')
    chars={'\\':r'\textbackslash{}','&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}'}
    result=''.join(chars.get(c,c) for c in text)
    words=result.split(' ')
    # Avoid stranding a single last word on its own line.
    return ' '.join(words[:-3])+' '+'~'.join(words[-3:]) if len(words)>5 else result

def entry(block):
    title=re.search(r'^### (.+)$',block,re.M)[1]
    role=re.search(r'<p class="role">(.*?)</p>',block)[1]
    dates,location=html.unescape(re.search(r'<p class="date">(.*?)</p>',block)[1]).split(' · ',1)
    for month,short in [('January','Jan'),('February','Feb'),('March','Mar'),('April','Apr'),('June','Jun'),('July','Jul'),('August','Aug'),('September','Sep'),('October','Oct'),('November','Nov'),('December','Dec')]:
        dates=dates.replace(month,short)
    role=tex(role)
    if title.startswith('Crestline'):
        role+=r' (\href{'+BASE+r'finance.html}{\textit{Interactive Dashboard}})'
    lines=[r'\noindent\textbf{'+tex(title)+r'}\hfill\textbf{'+tex(dates)+r'}\\',role+r'\hfill '+tex(location),r'\begin{itemize}']
    for b in re.findall(r'^- (.+)$',block,re.M):
        if 'Explore the interactive' in b:
            continue
        if b.startswith('**[Relevant Coursework]'):
            lines.append(r'\item \textbf{Relevant Coursework:} '+tex(b.split(':** ',1)[1]))
        else:
            lines.append(r'\item '+tex(b))
    lines += [r'\end{itemize}',r'\vspace{3pt}']
    return '\n'.join(lines)

source=SOURCE.read_text(encoding='utf-8')
assert not re.search(r'\bTeX\b',source)
parts=re.split(r'^## (.+)$',source,flags=re.M)
sections=dict(zip(parts[1::2],parts[2::2]))
preamble=r"""
\RequirePackage{fix-cm}
\documentclass[10pt,a4paper]{article}
\usepackage[left=0.5in,right=0.5in,top=0.34in,bottom=0.34in]{geometry}
\usepackage{enumitem}
\usepackage{microtype}
\usepackage[hidelinks]{hyperref}
\input{glyphtounicode}
\pdfgentounicode=1
\renewcommand{\$}{{\fontencoding{OT1}\selectfont\char36}}
% OT1 Computer Modern: intentionally no font-substitution packages.
\setlength{\parindent}{0pt}
\setlength{\parskip}{0pt}
\setlength{\footskip}{14pt}
\setlist[itemize]{leftmargin=10pt,label=$\bullet$,itemsep=1.1pt,parsep=0pt,topsep=3pt,partopsep=0pt}
\hyphenpenalty=10000
\exhyphenpenalty=10000
\emergencystretch=1em
\widowpenalty=10000
\clubpenalty=10000
\newcommand{\ressection}[1]{\vspace{6pt}{\fontsize{12.5}{13}\selectfont #1}\par\vspace{1pt}\hrule\vspace{3pt}}
\begin{document}
\fontsize{9.5}{10.9}\selectfont
\begin{center}
{\fontsize{24}{25}\selectfont AJAY SHARMA}\\[-1pt]
{\fontsize{9}{10}\selectfont Phone: (510) 575-8812 \enspace|\enspace Email: \href{mailto:ajay.sharma@berkeley.edu}{ajay.sharma@berkeley.edu} \enspace|\enspace LinkedIn: \href{https://www.linkedin.com/in/asharma2718}{linkedin.com/in/asharma2718}}\\[-1pt]
{\fontsize{9}{10}\selectfont Website: \href{https://ajay8005.github.io/personal-website/}{ajay8005.github.io/personal-website}}
\end{center}
\vspace{-8pt}
"""
out=[preamble,r'\ressection{SUMMARY}',r'\begin{itemize}\item '+tex(re.search(r'<p class="summary-copy">(.*?)</p>',sections['Professional Summary'])[1])+r'\end{itemize}',r'\ressection{EDUCATION}']
for block in re.split(r'(?=^### )',sections['Education'],flags=re.M)[1:]:
    out.append(entry(block))
out.append(r'\ressection{EXPERIENCE}')
for block in re.split(r'(?=^### )',sections['Professional Experience'],flags=re.M)[1:]:
    out.append(entry(block))
out += [r'\ressection{SKILLS}',r'\begin{itemize}']
skills=[
 ('Finance & Business Tools','MS Office (Excel, PowerPoint, Word), Google Workspace, Power BI.'),
 ('Excel','Formulas, PivotTables, lookup functions, conditional formatting.'),
 ('Financial Analysis','Budget vs. Actual Analysis, KPI Reporting, Forecasting, Financial Modeling, Sensitivity Analysis.'),
 ('Programming','Intermediate: Python, SQL, R, LaTeX; Basic: Java, C++, MATLAB.'),
 ('AI & Data Tools','LLMs & Prompt Engineering (ChatGPT, Claude, Gemini), Git, CSV-based data workflows.'),
 ('Statistical Methods','Hypothesis Testing, Linear & Generalized Linear Models, ANOVA/ANCOVA, Maximum Likelihood Estimation, Bootstrap Methods, Model Selection & Diagnostics, Quality Improvement.'),
 ('Additional','U.S. Citizen; Project Management, Quality Control, Written & Oral Communication, Detail-Oriented, Quick Learner, Adaptable.'),
]
for name,desc in skills:
    out.append(r'\item \textbf{'+tex(name)+':} '+tex(desc))
out += [r'\end{itemize}',r'\end{document}']
OUTPUT.parent.mkdir(parents=True,exist_ok=True)
TEX=OUTPUT.with_suffix('.tex')
TEX.write_text('\n'.join(out),encoding='utf-8')
with tempfile.TemporaryDirectory(prefix='resume-latex-') as tmp:
    result=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',tmp,str(TEX.resolve())],capture_output=True,text=True)
    print(result.stdout[-3500:])
    if result.returncode:
        raise RuntimeError('pdfLaTeX failed')
    shutil.copyfile(Path(tmp)/(TEX.stem+'.pdf'),OUTPUT)
    LOG=ROOT/'tmp/pdfs/computer-modern.log'
    LOG.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(Path(tmp)/(TEX.stem+'.log'),LOG)
pages=len(PdfReader(OUTPUT).pages)
print(f'{OUTPUT}: {pages} page(s)')
assert pages==1,'Resume must remain one page; adjust layout before publishing.'