from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
from reportlab.lib.pagesizes import A4
from common import ROOT

OUT=ROOT/'output/pdf';OUT.mkdir(parents=True,exist_ok=True)
FIG=ROOT/'results/figures';FIG.mkdir(parents=True,exist_ok=True)
NAVY=colors.HexColor('#132D46');TEAL=colors.HexColor('#087E8B');GREY=colors.HexColor('#526579')
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleX',fontName='Helvetica-Bold',fontSize=28,leading=32,textColor=NAVY,spaceAfter=18))
styles.add(ParagraphStyle(name='SubX',fontName='Helvetica',fontSize=12,leading=17,textColor=GREY,spaceAfter=14))
styles.add(ParagraphStyle(name='H1X',fontName='Helvetica-Bold',fontSize=18,leading=23,textColor=NAVY,spaceAfter=12))
styles.add(ParagraphStyle(name='H2X',fontName='Helvetica-Bold',fontSize=11.5,leading=16,textColor=TEAL,spaceBefore=12,spaceAfter=7))
styles.add(ParagraphStyle(name='BodyX',fontName='Helvetica',fontSize=10,leading=14.5,textColor=NAVY,spaceAfter=9))
styles.add(ParagraphStyle(name='SmallX',fontName='Helvetica',fontSize=8.2,leading=11,textColor=GREY,spaceAfter=7))
styles.add(ParagraphStyle(name='CellX',fontName='Helvetica',fontSize=8.4,leading=11,textColor=NAVY))
styles.add(ParagraphStyle(name='HeadX',fontName='Helvetica-Bold',fontSize=8.4,leading=11,textColor=colors.white))

def p(text,style='BodyX'):return Paragraph(text,styles[style])
def h(text):return p(text,'H1X')
def sub(text):return p(text,'H2X')
def table(rows,widths=None):
    cells=[[p(escape(str(cell)),'HeadX' if i==0 else 'CellX') for cell in row] for i,row in enumerate(rows)]
    t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.spaceAfter=8
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),NAVY),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F0F5F8'),colors.white]),('LINEBELOW',(0,-1),(-1,-1),.5,colors.HexColor('#CBD6DE'))]))
    return t
def fig(name,width=491):
    im=Image(str(FIG/name));ratio=im.imageHeight/im.imageWidth;im.drawWidth=width;im.drawHeight=width*ratio;return im
def build(name,story,short_title):
    def page(canvas,doc):
        canvas.setStrokeColor(TEAL);canvas.setLineWidth(1);canvas.line(52,805,543,805)
        canvas.setFillColor(GREY);canvas.setFont('Helvetica',8)
        canvas.drawString(52,817,'XAUUSD RESEARCH  /  STUDY III-B')
        canvas.drawString(52,29,short_title+'  |  05 October 2026')
        canvas.drawRightString(543,29,str(doc.page))
    doc=SimpleDocTemplate(str(OUT/name),pagesize=A4,rightMargin=52,leftMargin=52,topMargin=54,bottomMargin=48,title=short_title,author='XAUUSD Research',pageCompression=1)
    doc.build(story,onFirstPage=page,onLaterPages=page)
