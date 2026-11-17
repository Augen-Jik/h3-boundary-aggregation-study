from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
font_manager.fontManager.addfont('C:/Windows/Fonts/msyh.ttc')
plt.rcParams['font.family']=font_manager.FontProperties(fname='C:/Windows/Fonts/msyh.ttc').get_name()
fig,ax=plt.subplots(figsize=(10,5));ax.set_xlim(0,10);ax.set_ylim(0,5);ax.axis('off')
def box(x,y,w,h,s,c):
 ax.text(x+w/2,y+h/2,s,ha='center',va='center',fontsize=11,bbox=dict(boxstyle='round,pad=.7',fc=c,ec='#264B62',lw=1.2))
def arrow(a,b):ax.annotate('',xy=b,xytext=a,arrowprops=dict(arrowstyle='->',color='#496477',lw=1.5))
box(.2,3.8,9.5,.6,'共同分类规则   full候选筛选 → 顶点余量探测 → 内部格 / 风险格','#E5EFF7')
box(.1,2,4.4,.8,'M2 逐点展开\n内部点查父格  风险点粗编码','#EDF5F3')
box(5.5,2,4.4,.8,'M3 按细格计数\n内部格整组累加  风险点粗编码','#FFF0DE')
box(.1,.4,4.4,.7,'N个归属标签 + N个内部标记\n再使用Counter汇总','#EDF5F3')
box(5.5,.4,4.4,.7,'直接得到粗格Counter\n避免生成逐点输出列表','#FFF0DE')
arrow((4.5,3.6),(2.3,3));arrow((5.5,3.6),(7.7,3));arrow((2.3,1.9),(2.3,1.2));arrow((7.7,1.9),(7.7,1.2))
ax.text(5,-.05,'固定分类下计数代数等价；M3性能与真实H3一致性仍待运行验证',ha='center',fontsize=10,color='#555')
out=Path(__file__).parent/'supplement_analysis/figures'
fig.savefig(out/'07_kernel.png',dpi=180,bbox_inches='tight')
fig.savefig(out/'07_kernel.svg',bbox_inches='tight')

