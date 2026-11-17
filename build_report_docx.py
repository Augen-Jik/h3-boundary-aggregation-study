"""Create an editable Word report from the current, evidence-checked Markdown."""
import re
from pathlib import Path
from docx import Document
from docx.shared import Cm, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from PIL import Image

root=Path(__file__).parent
doc=Document()
doc.core_properties.author='jinchenying'
doc.core_properties.title='H3 跨分辨率聚合中的边界归属偏差与局部重编码方法'
doc.core_properties.subject='数据挖掘与技术课程报告'
sec=doc.sections[0]
sec.page_width=Cm(21);sec.page_height=Cm(29.7)
sec.top_margin=Cm(2);sec.bottom_margin=Cm(2)
sec.left_margin=Cm(2.2);sec.right_margin=Cm(2.2)
sec.header_distance=Cm(.8);sec.footer_distance=Cm(.8)
for name in ['Normal','Title','Heading 1','Heading 2','Heading 3','Caption']:
    style=doc.styles[name];style.font.name='Times New Roman';style.font.color.rgb=RGBColor(0,0,0)
    style.element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'宋体' if name in ['Normal','Caption'] else '黑体')
    style.paragraph_format.widow_control=True
normal=doc.styles['Normal'];normal.font.size=Pt(11)
normal.paragraph_format.line_spacing=1.3;normal.paragraph_format.space_after=Pt(5)
for name,size in [('Title',20),('Heading 1',15),('Heading 2',12.5),('Heading 3',11.5)]:
    style=doc.styles[name];style.font.size=Pt(size);style.font.bold=name!='Title'
    style.paragraph_format.space_before=Pt(10);style.paragraph_format.space_after=Pt(6)
    style.paragraph_format.keep_with_next=True
doc.styles['Caption'].font.size=Pt(9)
doc.styles['Caption'].font.bold=False
doc.styles['Caption'].paragraph_format.space_after=Pt(7)
for style in doc.styles:
    for border in list(style.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
footer=sec.footer.paragraphs[0];footer.alignment=WD_ALIGN_PARAGRAPH.CENTER
footer.add_run('jinchenying  |  H3跨分辨率聚合研究  |  ').font.size=Pt(8)
field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');footer._p.append(field)

def hyperlink(p,label,url):
    h=OxmlElement('w:hyperlink');h.set(qn('r:id'),p.part.relate_to(url,RT.HYPERLINK,is_external=True))
    r=OxmlElement('w:r');props=OxmlElement('w:rPr');c=OxmlElement('w:color');c.set(qn('w:val'),'145B86');props.append(c);r.append(props)
    t=OxmlElement('w:t');t.text=label;r.append(t);h.append(r);p._p.append(h)

def add_text(p,text):
    pattern=r'\[([^\]]+)\]\((https?://[^)]+)\)|(https?://[^\s]+)'
    pos=0
    for m in re.finditer(pattern,text):
        p.add_run(text[pos:m.start()].replace('**','').replace('`',''))
        hyperlink(p,m[1] or m[3],m[2] or m[3]);pos=m.end()
    p.add_run(text[pos:].replace('**','').replace('`',''))

def math_equation():
    p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    om=OxmlElement('m:oMathPara');eq=OxmlElement('m:oMath')
    def run(text):
        r=OxmlElement('m:r');t=OxmlElement('m:t');t.text=text;r.append(t);return r
    def sub(base,index):
        s=OxmlElement('m:sSub');e=OxmlElement('m:e');e.append(run(base));x=OxmlElement('m:sub');x.append(run(index));s.append(e);s.append(x);return s
    for part in [run('D(p) = H3(p, '),sub('r','c'),run('),   P(p) = Parent(H3(p, '),sub('r','f'),run('), '),sub('r','c'),run(')')]:eq.append(part)
    om.append(eq);p._p.append(om)

lines=(root/'report.md').read_text(encoding='utf-8-sig').splitlines()
i=0;figure_count=0;table_count=0
while i<len(lines):
    line=lines[i].strip();i+=1
    if not line:continue
    if line==r'\[':
        while i<len(lines) and lines[i].strip()!=r'\]':i+=1
        i+=1;math_equation();continue
    if line.startswith('# '):
        p=doc.add_paragraph(line[2:].replace('与局部重编码方法','\n与局部重编码方法'),style='Title');continue
    if line.startswith('## '):
        doc.add_paragraph(line[3:],style='Heading 1');continue
    if line.startswith('### '):
        doc.add_paragraph(line[4:],style='Heading 2');continue
    if line.startswith('!['):
        m=re.fullmatch(r'!\[([^]]*)\]\(([^)]+)\)',line);path=root/m[2]
        with Image.open(path) as im:w,h=im.size
        width=min(15.5,8.8*w/h)
        p=doc.add_paragraph();p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.keep_with_next=True;p.paragraph_format.space_before=Pt(5)
        p.add_run().add_picture(str(path),width=Cm(width))
        p=doc.add_paragraph(m[1],style='Caption');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        figure_count+=1;continue
    if line.startswith('|'):
        block=[line]
        while i<len(lines) and lines[i].strip().startswith('|'):block.append(lines[i].strip());i+=1
        data=[[x.strip() for x in row.strip('|').split('|')] for row in block if not re.fullmatch(r'[| :\-]+',row)]
        table=doc.add_table(rows=1,cols=len(data[0]));table.alignment=WD_TABLE_ALIGNMENT.CENTER;table.autofit=False
        widths=([2.1,3.7,6.3,4.5] if len(data[0])==4 and data[0][0]=='环节' else [16.6/len(data[0])]*len(data[0]))
        for c,w in zip(table.columns,widths):c.width=Cm(w)
        for ri,row in enumerate(data):
            cells=table.rows[0].cells if ri==0 else table.add_row().cells
            for ci,value in enumerate(row):
                cell=cells[ci];cell.width=Cm(widths[ci]);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
                tcPr=cell._tc.get_or_add_tcPr();margins=OxmlElement('w:tcMar')
                for side in ['top','left','bottom','right']:
                    e=OxmlElement('w:'+side);e.set(qn('w:w'),'85');e.set(qn('w:type'),'dxa');margins.append(e)
                tcPr.append(margins)
                p=cell.paragraphs[0];p.paragraph_format.line_spacing=1.12;p.paragraph_format.space_after=Pt(0)
                p.paragraph_format.keep_with_next=False
                p.alignment=WD_ALIGN_PARAGRAPH.LEFT if data[0][0]=='环节' else WD_ALIGN_PARAGRAPH.CENTER
                run=p.add_run(value);run.font.size=Pt(9.2);run.bold=ri==0
                if ri==0:
                    shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'E8EEF2');tcPr.append(shade)
            trPr=table.rows[ri]._tr.get_or_add_trPr();no_split=OxmlElement('w:cantSplit');trPr.append(no_split)
            if ri==0:trPr.append(OxmlElement('w:tblHeader'))
        borders=OxmlElement('w:tblBorders')
        for side in ['top','left','bottom','right','insideH','insideV']:
            e=OxmlElement('w:'+side);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
        table._tbl.tblPr.append(borders)
        doc.add_paragraph().paragraph_format.space_after=Pt(2)
        table_count+=1;continue
    p=doc.add_paragraph();add_text(p,line)
    if line.startswith(('作者 ','课程 ','研究范围 ','公开仓库 ','完整协作记录索引 ','实际 AI 对话 ')):
        p.paragraph_format.space_after=Pt(5)
        for run in p.runs:run.font.size=Pt(10)
    if re.match(r'^\d+\. ',line):
        p.paragraph_format.space_after=Pt(3)

out=root/'output/docx/H3_course_report.docx';out.parent.mkdir(parents=True,exist_ok=True)
doc.save(out)
assert figure_count==len(re.findall(r"^!\[", (root/"report.md").read_text(encoding="utf-8"), re.M)) and table_count>=7
print(out,'figures',figure_count,'tables',table_count)
