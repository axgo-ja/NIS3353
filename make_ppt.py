# -*- coding: utf-8 -*-
import os
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# Morandi palette
BG   = RGBColor(0xFA,0xF8,0xF5)
CARD = RGBColor(0xFF,0xFF,0xFF)
TXT  = RGBColor(0x3D,0x3D,0x3D)
MUTED= RGBColor(0x8C,0x8C,0x8C)
ROSE = RGBColor(0xC2,0xA4,0x97)
SAGE = RGBColor(0x8B,0x9D,0x83)
PERI = RGBColor(0x9B,0x9E,0xC0)
RED  = RGBColor(0xD4,0x84,0x7A)
GRN  = RGBColor(0x7A,0xA8,0x84)
LINE = RGBColor(0xE8,0xE3,0xDD)
WHITE= RGBColor(0xFF,0xFF,0xFF)

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)

def bg(s): s.background.fill.solid(); s.background.fill.fore_color.rgb = BG

def tb(s,l,t,w,h,txt,sz=18,c=TXT,b=False,a=PP_ALIGN.LEFT,fn='Microsoft YaHei'):
    bx=s.shapes.add_textbox(l,t,w,h); p=bx.text_frame.paragraphs[0]
    p.text=txt; p.font.size=Pt(sz); p.font.color.rgb=c; p.font.bold=b; p.font.name=fn; p.alignment=a
    return bx.text_frame

def mtb(s,l,t,w,h,lines,sz=16,c=TXT):
    bx=s.shapes.add_textbox(l,t,w,h); tf=bx.text_frame; tf.word_wrap=True
    for i,(txt,bold,clr) in enumerate(lines):
        p=tf.paragraphs[0] if i==0 else tf.add_paragraph()
        p.text=txt; p.font.size=Pt(sz); p.font.color.rgb=clr; p.font.bold=bold
        p.font.name='Microsoft YaHei'; p.space_after=Pt(sz*0.35)
    return tf

def line(s,l,t,w): s.shapes.add_shape(MSO_SHAPE.RECTANGLE,l,t,w,Pt(1)).fill.solid(); s.shapes[-1].fill.fore_color.rgb=ROSE; s.shapes[-1].line.fill.background()

def card(s,l,t,w,h,title,val,sub="",ac=ROSE):
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,l,t,w,h); sh.fill.solid(); sh.fill.fore_color.rgb=CARD
    sh.line.color.rgb=LINE; sh.line.width=Pt(1)
    tb(s,l+Pt(14),t+Pt(10),w-Pt(28),Pt(20),title,11,MUTED,a=PP_ALIGN.CENTER)
    tb(s,l+Pt(14),t+Pt(32),w-Pt(28),Pt(36),val,26,ac,True,PP_ALIGN.CENTER)
    if sub: tb(s,l+Pt(14),t+h-Pt(20),w-Pt(28),Pt(16),sub,9,MUTED,a=PP_ALIGN.CENTER)

def title_slide(title, subtitle, authors):
    s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
    line(s,Inches(3),Inches(2.4),Inches(7.333))
    tb(s,Inches(3),Inches(2.7),Inches(7.333),Inches(1.2),title,42,TXT,True,PP_ALIGN.CENTER)
    tb(s,Inches(3),Inches(3.8),Inches(7.333),Inches(0.5),subtitle,20,MUTED,a=PP_ALIGN.CENTER)
    tb(s,Inches(3),Inches(4.5),Inches(7.333),Inches(0.5),authors,16,ROSE,a=PP_ALIGN.CENTER)
    line(s,Inches(3),Inches(5.4),Inches(7.333))

OUT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'WaNet答辩_v2.pptx')

# === SLIDE 1: Cover ===
title_slide("Warping后门攻击的频域弱点",
            "WaNet 复现与分析  ·  AI安全课程设计",
            "周争妍  ·  蒋竺君")

# === SLIDE 2: Background ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(5),Inches(0.5),"什么是后门攻击",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
mtb(s,Inches(0.8),Inches(1.5),Inches(5.5),Inches(2.5),[
    ("深度学习模型在训练阶段可被植入后门",True,TXT),
    ("攻击者在训练数据中混入带触发器的样本",False,MUTED),
    ("正常图 -> 正常分类  |  带触发器的图 -> 攻击者指定标签",False,RED),
    ("",False,MUTED),
    ("传统触发器: 白色方块 / 水印 / 正弦波纹 (人眼可见)",False,MUTED),
    ("-> 防御方法 (STRIP / Neural Cleanse) 可以检测",False,RED),
],16)
card(s,Inches(7.5),Inches(1.3),Inches(2.5),Inches(1.3),"BadNets","白色Patch","可见触发器",RED)
card(s,Inches(10.3),Inches(1.3),Inches(2.5),Inches(1.3),"Blend/SIG","叠加图案","可见触发器",RED)
card(s,Inches(7.5),Inches(3.0),Inches(5.3),Inches(1.3),"共同问题","人眼可见 + 防御可检测","需要更隐蔽的触发器",ROSE)
tb(s,Inches(7.5),Inches(4.8),Inches(5.3),Inches(0.5),"WaNet的答案: 用图像形变替代可见Patch",15,ROSE,True)

# === SLIDE 3: WaNet ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"WaNet: 基于图像形变的后门攻击",30,TXT,True)
tb(s,Inches(0.8),Inches(1.0),Inches(5),Inches(0.3),"Nguyen & Tran, ICLR 2021",14,MUTED)
line(s,Inches(0.8),Inches(1.4),Inches(1.5))
mtb(s,Inches(0.8),Inches(1.8),Inches(5.8),Inches(3.0),[
    ("核心思想:",True,ROSE),
    ("用图像空间形变(Warping)替代可见Patch作为后门触发器",False,TXT),
    ("",False,MUTED),
    ("怎么做:",True,ROSE),
    ("1. 生成 k*k 随机控制网格, 定义平滑的像素位移场",False,MUTED),
    ("2. 对图像做微小形变 (亚像素级) -> 后门样本",False,MUTED),
    ("3. 模型学到该形变模式与目标标签的关联",False,MUTED),
    ("4. 人眼完全无法察觉形变",False,TXT),
    ("",False,MUTED),
    ("关键设计: Noise Mode",True,ROSE),
    ("训练时加入随机形变的噪声样本, 迫使模型学习真正的warping而非像素捷径",False,TXT),
],16)
card(s,Inches(7.5),Inches(1.5),Inches(5.0),Inches(1.5),"WaNet 攻击效果","ASR = 99.15%","人眼完全不可见",GRN)
card(s,Inches(7.5),Inches(3.5),Inches(5.0),Inches(1.5),"绕过防御","STRIP / NC / FP 全部失效","现有防御无法检测",RED)

# === SLIDE 4: Our Work ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(5),Inches(0.5),"我们的工作",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
card(s,Inches(0.8),Inches(1.8),Inches(3.5),Inches(2.5),"阶段一: 复现 (周争妍)","3数据集x2模式","STRIP/NC/FP防御验证",MUTED)
tb(s,Inches(1.0),Inches(3.1),Inches(3.1),Inches(0.8),"主实验复现, 确认WaNet\n确实绕过所有现有防御",12,MUTED,a=PP_ALIGN.CENTER)
card(s,Inches(4.9),Inches(1.8),Inches(3.5),Inches(2.5),"阶段二: 消融 (蒋竺君)","Noise/s/k参数扫描","发现参数高度敏感规律",PERI)
tb(s,Inches(5.1),Inches(3.1),Inches(3.1),Inches(0.8),"深入拆解warping机制\ns<0.5或k<4时攻击大幅下降",12,MUTED,a=PP_ALIGN.CENTER)
card(s,Inches(9.0),Inches(1.8),Inches(3.5),Inches(2.5),"阶段三: 创新 (蒋竺君)","频域检测器","AUC 0.735 vs STRIP 0.50",ROSE)
tb(s,Inches(9.2),Inches(3.1),Inches(3.1),Inches(0.8),"Warping=插值->频域留痕\n首次从图像信号检测warping后门",12,MUTED,a=PP_ALIGN.CENTER)
tb(s,Inches(0.8),Inches(5.5),Inches(11.7),Inches(0.6),
   "核心贡献: 现有防御看模型行为->检测不到; 我们看图像信号->能检测到",16,TXT,True,PP_ALIGN.CENTER)

# === SLIDE 5: Main Results ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"主实验复现结果 (CIFAR-10)",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
card(s,Inches(0.8),Inches(1.8),Inches(2.8),Inches(1.4),"Clean Acc","92.84%","论文 94.15%",GRN)
card(s,Inches(3.9),Inches(1.8),Inches(2.8),Inches(1.4),"ASR","99.15%","论文 99.55%",RED)
card(s,Inches(7.0),Inches(1.8),Inches(2.8),Inches(1.4),"Cross Acc","89.71%","论文 93.55%",PERI)
card(s,Inches(10.1),Inches(1.8),Inches(2.8),Inches(1.4),"Cross(无Noise)","0.00%","关键发现",RED)
mtb(s,Inches(0.8),Inches(3.8),Inches(5.5),Inches(2.5),[
    ("防御验证:",True,TXT),
    ("STRIP: Entropy分布无法区分 -> 检测失败",False,RED),
    ("Fine-Pruning: 剪枝后ASR仍>90% -> 无法消除",False,RED),
    ("Neural Cleanse: Anomaly Index<2 -> 检测不到",False,RED),
    ("结论: WaNet确实能绕过所有三种现有防御",True,PERI),
],15)

# === SLIDE 6: Noise Mode ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"消融实验: Noise Mode的关键作用",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
card(s,Inches(0.8),Inches(2.0),Inches(5.5),Inches(2.2),"With Noise Mode","Cross Acc = 89.71%","Neural Cleanse 检测不到",GRN)
card(s,Inches(6.8),Inches(2.0),Inches(5.5),Inches(2.2),"Without Noise Mode","Cross Acc = 0.00%","Neural Cleanse 能检测到",RED)
tb(s,Inches(0.8),Inches(5.0),Inches(11.7),Inches(1.2),
   "Noise Mode是WaNet绕过防御的决定性因素。\n无Noise: 模型学到像素捷径->被NC发现。有Noise: 模型被迫学习真正的warping->防御失效。",
   16,TXT,a=PP_ALIGN.CENTER)

# === SLIDE 7: s & k ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"消融实验: Warping参数敏感性",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
tb(s,Inches(0.8),Inches(1.6),Inches(5),Inches(0.4),"Warping强度 s",20,ROSE,True)
card(s,Inches(0.8),Inches(2.2),Inches(2.6),Inches(1.4),"s = 0.25","ASR 74%","太弱->失效",RED)
card(s,Inches(3.7),Inches(2.2),Inches(2.6),Inches(1.4),"s = 0.50","ASR 99.59%","最优",GRN)
card(s,Inches(6.6),Inches(2.2),Inches(2.6),Inches(1.4),"s = 1.00","ASR 98.29%","饱和",MUTED)
tb(s,Inches(0.8),Inches(4.0),Inches(5),Inches(0.4),"网格大小 k",20,ROSE,True)
card(s,Inches(0.8),Inches(4.6),Inches(2.6),Inches(1.4),"k = 2","ASR 92.82%","太粗->被当噪声",RED)
card(s,Inches(3.7),Inches(4.6),Inches(2.6),Inches(1.4),"k = 4","ASR 99.15%","最优",GRN)
card(s,Inches(6.6),Inches(4.6),Inches(2.6),Inches(1.4),"k = 8","ASR 97.55%","饱和",MUTED)
tb(s,Inches(10),Inches(1.8),Inches(2.8),Inches(4.2),
   "关键发现\n\nWaNet对参数\n高度敏感\n\ns<0.5或k<4时\n攻击大幅下降\n\n存在狭窄的\n有效参数区间",14,ROSE,a=PP_ALIGN.CENTER)

# === SLIDE 8: Insight ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"核心洞察: Warping在频域留下痕迹",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
mtb(s,Inches(0.8),Inches(1.6),Inches(5.5),Inches(3.0),[
    ("消融实验揭示了一个重要线索:",False,MUTED),
    ("WaNet 的 warping 到底是怎么实现的？",False,TXT),
    ("它调用的是 PyTorch 的 grid_sample 函数 + 双线性插值 (bilinear interpolation)",True,ROSE),
    ("",False,MUTED),
    ("而插值运算本质上是一种信号处理操作 ——",False,MUTED),
    ("每个新像素 = 周围像素的加权平均 -> 必然在频域留下痕迹!",True,TXT),
    ("",False,MUTED),
    ("全新检测思路:",False,MUTED),
    ("现有防御: 看模型输出 -> 检测不到WaNet",False,RED),
    ("我们的方法: 看图像频域(FFT) -> 能检测到!",True,GRN),
],17)
tb(s,Inches(7.5),Inches(2.0),Inches(5),Inches(3.0),
   "Warping的本质\n\ngrid_sample对图像\n做双线性插值\n\n每个插值点=周围像素\n的加权平均\n\n-> 频域高频分量异常",
   16,ROSE,a=PP_ALIGN.CENTER)
line(s,Inches(0.8),Inches(5.5),Inches(11.7))
tb(s,Inches(0.8),Inches(5.8),Inches(11.7),Inches(0.5),"不可感知 != 不可检测",18,ROSE,True,PP_ALIGN.CENTER)

# === SLIDE 9: Detector Design ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"频域Warping检测器",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
steps=[("STEP1: 图像对","Clean+Warped\n各500张",MUTED),("STEP2: FFT","傅里叶变换\n频谱图",MUTED),("STEP3: 特征","高频能量比\n频谱熵等6维",MUTED),("STEP4: SVM","RBF核SVM\n30%测试",MUTED),("STEP5: 评估","ROC vs STRIP\nAUC 0.735",ROSE)]
for i,(t,d,ac) in enumerate(steps):
    card(s,Inches(0.8+i*2.5),Inches(2.0),Inches(2.2),Inches(2.0),t,d,"",ac)
    if i<4: tb(s,Inches(0.8+i*2.5+2.3),Inches(2.8),Inches(0.3),Inches(0.3),"->",18,ROSE,a=PP_ALIGN.CENTER)
card(s,Inches(0.8),Inches(4.5),Inches(5.5),Inches(1.5),"6维频域特征","高频能量比 / 频谱熵 / 均值频率 / 方差频率 / 低频能量比 / 中频能量比","",PERI)
card(s,Inches(6.8),Inches(4.5),Inches(5.5),Inches(1.5),"检测结果","Acc=67.33%  |  AUC=0.735  |  STRIP AUC=0.50","",GRN)

# === SLIDE 10: FFT ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"频域可视化: Clean vs Warped",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
for i,lbl in enumerate(["Clean Image","Clean FFT Spectrum","Clean Radial Profile","Warped Image","Warped FFT Spectrum","FFT Difference Map"]):
    x=Inches(0.8+(i%3)*4.0); y=Inches(1.6+(i//3)*2.6)
    sh=s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,x,y,Inches(3.7),Inches(2.3))
    sh.fill.solid();sh.fill.fore_color.rgb=CARD;sh.line.color.rgb=ROSE if i==5 else LINE;sh.line.width=Pt(1)
    tb(s,x+Pt(8),y+Pt(6),Inches(3.5),Inches(0.3),lbl,12,ROSE if i==5 else MUTED,a=PP_ALIGN.CENTER)
tb(s,Inches(0.8),Inches(6.9),Inches(11.7),Inches(0.3),"插入 results/freq_detector/fft_spectrum_comparison.png",12,MUTED,a=PP_ALIGN.CENTER)

# === SLIDE 11: ROC ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"检测性能: 频域检测器 vs STRIP",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
card(s,Inches(0.8),Inches(2.0),Inches(3.8),Inches(2.0),"频域检测器 (Ours)","AUC = 0.735","准确率 67.33%",GRN)
card(s,Inches(5.0),Inches(2.0),Inches(3.8),Inches(2.0),"STRIP","AUC = 0.50","等同随机猜测",RED)
card(s,Inches(9.2),Inches(2.0),Inches(3.5),Inches(2.0),"提升幅度","+23.5% AUC","远超随机基线",ROSE)
tb(s,Inches(0.8),Inches(4.5),Inches(11.7),Inches(0.3),"插入 results/freq_detector/roc_curve.png",12,MUTED,a=PP_ALIGN.CENTER)
tb(s,Inches(0.8),Inches(5.8),Inches(11.7),Inches(0.6),"STRIP看模型输出熵->无法区分(AUC=0.50)  |  频域检测器看图像信号->能有效检测(AUC=0.735)",15,TXT,a=PP_ALIGN.CENTER)

# === SLIDE 12: Full Results ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(0.8),Inches(0.5),Inches(7),Inches(0.5),"全部实验结果汇总",30,TXT,True)
line(s,Inches(0.8),Inches(1.1),Inches(1.5))
data=[
    ["Epochs","Experiment","Clean Acc","ASR","Cross Acc","Key Finding"],
    ["400","Noise WITH","92.84","99.15","89.71","Baseline"],
    ["400","Noise WITHOUT","92.74","98.21","0.00","Noise is KEY"],
    ["400","s=0.25","92.39","74.12","89.38","s too small"],
    ["400","s=0.50","92.81","99.59","89.69","Optimal"],
    ["400","s=1.00","92.82","98.29","89.30","Saturated"],
    ["80","k=2","92.14","92.82","88.95","k too small"],
    ["400","k=4","92.84","99.15","89.71","Optimal"],
    ["80","k=8","91.94","97.55","88.04","Saturated"],
    ["400","Seed=0","92.81","99.59","89.69","Stable"],
    ["80","Seed=1","92.10","98.70","88.72","Stable"],
]
r,c=len(data),len(data[0])
tbl=s.shapes.add_table(r,c,Inches(0.5),Inches(1.7),Inches(12.3),Inches(5.0)).table
for ri in range(r):
    for ci in range(c):
        cell=tbl.cell(ri,ci);cell.text=data[ri][ci]
        for p in cell.text_frame.paragraphs:
            p.font.size=Pt(11);p.font.name='Microsoft YaHei';p.alignment=PP_ALIGN.CENTER
            if ri==0:p.font.bold=True;p.font.color.rgb=WHITE
            elif ri in[2,6]:p.font.color.rgb=TXT
            else:p.font.color.rgb=MUTED
        if ri==0:cell.fill.solid();cell.fill.fore_color.rgb=ROSE
        elif ri in[2,6]:cell.fill.solid();cell.fill.fore_color.rgb=RGBColor(0xF5,0xF0,0xEB)

# === SLIDE 13: Conclusion ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(2),Inches(1.2),Inches(9.333),Inches(0.8),"结论",38,TXT,True,PP_ALIGN.CENTER)
line(s,Inches(5),Inches(2.0),Inches(3.333))
conclusions=[
    ("1","WaNet攻击高度有效","CIFAR-10上ASR达99.15%, Clean保持92.84%",GRN),
    ("2","Noise Mode是绕过防御的关键","无Noise时Cross=0%, 后门可被Neural Cleanse检测",ROSE),
    ("3","Warping参数高度敏感","s<0.5或k<4时攻击大幅下降 — 存在狭窄有效区间",RED),
    ("4","频域检测: 我们的创新","首次从图像信号层面检测warping后门, AUC 0.735远超市面上最强的STRIP(0.50)",GRN),
]
for i,(num,title,desc,color) in enumerate(conclusions):
    y=Inches(2.6+i*1.1)
    tb(s,Inches(2.0),y,Inches(0.5),Inches(0.5),num,24,color,True)
    tb(s,Inches(2.7),y,Inches(4),Inches(0.35),title,20,TXT,True)
    tb(s,Inches(2.7),y+Inches(0.4),Inches(8.5),Inches(0.35),desc,14,MUTED)

# === SLIDE 14: Members ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
tb(s,Inches(2),Inches(1.5),Inches(9.333),Inches(0.8),"成员分工",38,TXT,True,PP_ALIGN.CENTER)
line(s,Inches(5),Inches(2.3),Inches(3.333))
card(s,Inches(2.0),Inches(3.0),Inches(4.2),Inches(2.5),"周争妍","主实验复现+防御验证","3数据集 x 2模式\nSTRIP / Fine-Pruning / Neural Cleanse\n环境配置 + tmux并行脚本",ROSE)
card(s,Inches(7.1),Inches(3.0),Inches(4.2),Inches(2.5),"蒋竺君","消融实验+频域检测器+可视化","Noise/s/k参数扫描 (10组)\n频域检测器 (AUC 0.735)\nDashboard + PPT制作",PERI)

# === SLIDE 15: Thank you ===
s=prs.slides.add_slide(prs.slide_layouts[6]); bg(s)
line(s,Inches(3),Inches(2.8),Inches(7.333))
tb(s,Inches(3),Inches(3.1),Inches(7.333),Inches(1.0),"感谢聆听",48,TXT,True,PP_ALIGN.CENTER)
tb(s,Inches(3),Inches(4.3),Inches(7.333),Inches(0.5),"WaNet复现与分析  ·  AI安全课程设计",18,MUTED,a=PP_ALIGN.CENTER)
tb(s,Inches(3),Inches(5.0),Inches(7.333),Inches(0.5),"github.com/axgo-ja/NIS3353",15,ROSE,a=PP_ALIGN.CENTER)
line(s,Inches(3),Inches(5.8),Inches(7.333))

prs.save(OUT)
print(f'OK: {OUT} ({len(prs.slides)} slides)')
