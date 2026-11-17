"""Insert completed supplement results, without filling unobserved outcomes."""
from pathlib import Path
import json, statistics as st

ROOT=Path(__file__).parent
BASE=ROOT/'supplement_20261117'
s=json.loads((BASE/'derived/summary.json').read_text(encoding='utf-8'))
groups=s['cost_groups']
seed_rows=list(__import__('csv').DictReader((BASE/'derived/seed_results.csv').open(encoding='utf-8-sig')))
source=(BASE/'report_enhanced_source.md').read_text(encoding='utf-8')
u=next(g for g in groups if g['distribution']=='U' and g['n']==100000)
c=next(g for g in groups if g['distribution']=='C' and g['n']==100000)
source=source.replace('新增按细格计数内核M3已实现，其真实H3实验尚待执行，不作为本文的性能证据。',
    f"随后在SSH服务器完成M3补充实验。每批10万点、20批时，相对每个种子中较快的直接编码参照，M3耗时比的种子均值为U组{u['strong_over_M3']:.3f}、C组{c['strong_over_M3']:.3f}。新增四区域108组、54万点检查记录到{s['new_region_point_mismatches']}次M2逐点差异及{s['new_region_count_l1']}个M3计数L1差。所有负结果和错误均按登记范围报告。")
source=source.replace('研究范围 杭州与南京的合成点归属验证，以及杭州连续新批次成本评估',
    '研究范围 合成点归属与计数执行优化、连续新批次成本及新增四区域压力验证')
source=source.replace('| 面向计数输出的执行优化 | M3内部格按数量直接累加，风险点逐点编码 | 实现与实验协议已形成 | 尚无真实H3运行结果，不作为性能结论 |',
    '| 面向计数输出的执行优化 | M3共享M2分类器，安全细格整组累加，风险点粗编码 | 21条同期成本序列、9条漂移序列和108组新区域检查 | 只改变计数执行，不消除分类器的几何局限 |')
source=source.replace('前四项构成本文已经有证据支持的课程级研究贡献。第五项是新增实现方向，单列为待验证内容。这样的结构将方法贡献、实测收益和后续探索逐一对应，避免把代码完成等同于实验完成。',
    '前四项由已有实验及日志复算支持，第五项由本轮冻结实现与补充实验检验。原创边界限定为课程级实现组合、输出需求驱动的执行修改和适用条件评估，不把已有H3性质、full接口或一般缓存机制列为新发明。')
start=source.index('## 12 新增实现与补充实验方案')
end=source.index('## 13 研究过程与复现说明',start)
parts=['## 12 补充实验 计数执行优化与强基线对照','',
       'M3沿用M2的full筛选与1e-9度余量探测，仅改变聚合执行。安全细格按点数累加，风险点按原坐标编码。其输出为粗格Counter，不生成N长度的逐点标签和内部标记列表。这是计数输出需求下的执行优化，不是新的几何分类规则。','',
       '本轮先固定协议、源码哈希和新种子，再在SSH服务器独立目录串行运行。Python3.12.3，H3 Python/C4.5.0，numpy1.26.4、pyproj3.8.0；线程数设为1。实际CPU及配额见environment.json。所有M2、M3首次对象构造均在计时内，A3每批重建M3对象。数据生成、细编码、正确性检查和内存测量在计时外。旧结果不重写，旧版与本轮M2的绝对时间不用于估计修改的因果效果。','',
       '成本任务为杭州U/C三规模及B压力组，共21条不同新批次序列，种子300至302。每序列20批、重复3次。先取每个种子的重复累计耗时中位数，再对3个种子汇总。B1以列表编码后计数，B1s以流式生成器计数；强参照为每个种子中二者较小的累计中位数。这是事后选出的较强参照，不是声称部署前已知哪个实现更快。','',
       '| 分布 | 每批点数 | B1累计秒 | B1s累计秒 | M2累计秒 | M3累计秒 | 强参照/M3 |','|---|---|---|---|---|---|---|']
for g in groups:parts.append(f"| {g['distribution']} | {g['n']} | {g['B1_s']:.4f} | {g['B1s_s']:.4f} | {g['M2_s']:.4f} | {g['M3_s']:.4f} | {g['strong_over_M3']:.3f} |")
parts+=['','比值大于1表示M3累计耗时较低，小于1表示M3较慢。比值在种子内计算后平均，不必等于表中两列均值之比。所有条件同时报告，B组单列为边界压力测试。原始每批每次计时均随仓库提供。M3在小批次中仍慢于直接编码；在B压力组中，它还慢于共享同一分类器的M2。因此，省略逐点输出列表并不保证净收益。','',
        '![全部条件下M3与同期方法的累计耗时比较](supplement_20261117/derived/figures/01_strong_baselines.png)','',
        '![密集新批次的完整累计成本](supplement_20261117/derived/figures/02_dense_cumulative.png)','',
        'M2/M3比较在相同分类规则和跨批复用条件下测量计数执行改动的整体影响。M3/A3比较反映组合分类状态跨批保留的收益，不能分离三层缓存。两组比较均包含各自数据结构操作，未记录组件分项耗时，不能唯一解释每个内部步骤的贡献。只有3个成本种子，图中曲线和比值不是统计显著性结论。','',
        '### 空间漂移与新单元成本','',
        '在相同U生成规则下，每批10万点、共10批，向东逐批平移0、1、5 km，使用种子400至402，各重复3次。变化同时影响覆盖范围和新增细格数，因此属于复用压力实验，不是只操纵缓存命中率的因果实验。','',
        '| 每批向东平移km | 强参照/M3种子均值 | 种子最小值 | 种子最大值 | 累计新增细格数均值 |','|---|---|---|---|---|']
for shift in [0,1000,5000]:
    rs=[r for r in seed_rows if r['shift']==str(shift)]
    assert len(rs)==3
    values=[float(r['strong_over_M3']) for r in rs]
    parts.append(f"| {shift/1000:g} | {st.mean(values):.3f} | {min(values):.3f} | {max(values):.3f} | {st.mean(float(r['new_cells']) for r in rs):.1f} |")
parts+=['','本轮10批观察窗口内，三种平移条件的M3均未超过强直接编码参照。新增细格数随平移量增大，但这只是既定空间压力设计中的共同变化，不能把耗时差唯一归因为缓存命中变化。','',
        '![空间漂移条件下的耗时比与新增细格](supplement_20261117/derived/figures/03_drift.png)','',
        '### 新区域检查与旧失败回归','',
        '固定M2分类器后，在北京、深圳、悉尼和雷克雅未克四处局部区域，按各自UTM分区生成U/C/B样本。分辨率对为9到8、10到8、10到9，种子500至502，每组5000点，共108组、54万点。检查M2逐点归属及M3粗格计数。地理位置虽未参与旧分类器开发，但仍是人为合成分布，只能称新增区域压力验证。','',
        '| 区域 | 组合数 | 检查点数 | M2逐点差异数 | M3计数L1差之和 |','|---|---|---|---|---|']
regions=json.loads((BASE/'supplement_v3/new_regions.json').read_text())
for city in ['beijing','shenzhen','sydney','reykjavik']:
    rs=[r for r in regions if r['city']==city]
    parts.append(f"| {city} | {len(rs)} | {sum(r['n'] for r in rs)} | {sum(r['point_mismatches'] for r in rs)} | {sum(r['count_l1'] for r in rs)} |")
parts+=['',f"对保留的4条旧失败坐标分别检查3个分辨率对，共12条回归记录，其中失败{len(s['regression_failures'])}条。它们是已知失败回归，不是12个独立位置。成本与漂移序列还在计时外检查M2隐含逐点归属及各方法Counter，记录到{len(s['workload_point_errors'])}个逐点异常批次、{len(s['workload_count_errors'])}个计数异常方法批次。发生失败时保留坐标、方法和配置，不删除样本。",'',
        '![新区域的逐点差异与风险比例](supplement_20261117/derived/figures/04_new_regions.png)','',
        '风险比例图为U/C/B合并后的描述性汇总，不能代表真实城市点分布。计数一致本身不能替代逐点一致；M3不输出逐点标签，逐点检查由相同分类规则的M2提供。有限顶点探测在新增样本中通过，也仍不能提供全球零误差保证。','',
        '### 内存与输出结构','',
        '使用种子600、U组每批10万点、5个不同新批次，独立测量Python分配峰值与保留量。输入数据在追踪前生成，每批结果用后释放，各方法保持相同结果寿命。该测量仅有一条登记序列，不覆盖C库全部RSS，也不作为稳定总体内存估计。','',
        '| 方法 | Python峰值MiB | Python保留量MiB |','|---|---|---|']
for method,m in s['memory'].items():parts.append(f"| {method} | {m['peak_bytes']/1024**2:.3f} | {m['retained_bytes']/1024**2:.3f} |")
parts+=['','M3的Python分配峰值低于M2，符合减少逐点中间列表的预期，但流式直接计数B1s的峰值仍远低于M3。不能据此宣称M3在全部方法中最节省内存。','',
        '![不同输出结构下的Python内存分配](supplement_20261117/derived/figures/05_memory.png)','',
        '本轮所有新区域与成本结果已经查看并参与本报告讨论。若后续据此调整实现或阈值，应登记其已参与开发。当前未根据结果搜索阈值或重新选择种子。补充实验证据与旧版结果分别保存，不能混用分母或计时版本。','']
source=source[:start]+'\n'.join(parts)+'\n'+source[end:]
source=source.replace('本轮新增的实证内容是对既有原始轨迹的完整复算，包括累计交叉点、后段边际成本和留一种子敏感性；没有新增H3点样本。M3及空间漂移、新区域实验仍待真实执行。',
    '本轮先复算既有原始轨迹，再在SSH服务器执行M3同期成本、空间漂移、新区域、回归与内存实验。两类证据分开归档，不将旧数据复算记作新增独立实验。')
source=source.replace('后续M3将计数输出需求落实到执行内核，需通过同期强基线、新区域与漂移验证后再判断效果。',
    f"M3已完成同期验证，密集U/C条件下相对强参照的平均耗时比分别为{u['strong_over_M3']:.3f}和{c['strong_over_M3']:.3f}。该结果须与全部规模、压力数据及漂移条件共同解释，不能替代严格几何证明或普遍优势主张。")
assert not any(t in source for t in ['代码已备，待运行','真实H3实验尚待执行','尚无真实H3运行结果','M3及空间漂移、新区域实验仍待真实执行'])
(ROOT/'report.md').write_text(source,encoding='utf-8',newline='\n')
print('Updated report from complete frozen supplement results')
