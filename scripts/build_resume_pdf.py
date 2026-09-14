"""Compile the user-supplied resume.tex reference in Computer Modern.
Run: python scripts/build_resume_pdf.py [source.tex] [output.pdf]
Requires pdfLaTeX, pdftotext, pypdf. Does not rewrite the supplied resume text.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
import shutil
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'resume.tex'
OUTPUT=Path(sys.argv[2]) if len(sys.argv)>2 else ROOT/'resume.pdf'
with tempfile.TemporaryDirectory(prefix='resume-latex-') as tmp:
    result=subprocess.run(['pdflatex','-interaction=nonstopmode','-halt-on-error','-output-directory',tmp,str(SOURCE.resolve())],capture_output=True,text=True)
    if result.returncode:
        print(result.stdout)
        raise RuntimeError('pdfLaTeX failed')
    OUTPUT.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(Path(tmp)/(SOURCE.stem+'.pdf'),OUTPUT)
    log=ROOT/'tmp/pdfs/reference-build.log'
    log.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(Path(tmp)/(SOURCE.stem+'.log'),log)
pdf=PdfReader(OUTPUT)
assert len(pdf.pages)==1,'Resume must remain one page.'
rendered=subprocess.run(['pdftotext','-layout',str(OUTPUT),'-'],capture_output=True,text=True,check=True).stdout
lines=[' '.join(line.split()) for line in rendered.splitlines() if line.strip()]
summary=lines[lines.index('SUMMARY')+1:lines.index('EDUCATION')]
assert len(summary)<=3,f'Summary exceeds three lines: {len(summary)}'
assert all(term in ' '.join(summary) for term in ['strategic finance','FP&A','business analytics'])
assert 'Overfull' not in log.read_text(),'Text overflows the layout.'
print(f'PASS: one page; {len(summary)} summary lines; no overflow.')
print(OUTPUT)
