"""Current-state corrections applied after the historical report generator."""
import csv
from pathlib import Path

def revise(source):
    root=Path(__file__).parent
    source=source.replace('代码、独立评测数据、图表与本初稿已上传公开仓库。','代码、原始结果、图表和当前报告均已公开。原版与修订版实验已完成，本文保留全部失败与不利结果。')
    source=source.replace('研究范围 两处局部区域的合成点计数与重复新批次成本',
                          '研究范围 杭州与南京的合成点归属验证，以及杭州连续新批次成本评估')
    source=source.replace('开发种子0至4，独立评测种子100至109。',
                          '开发种子0至4。原版随机评测种子为100至109，修订版为200至209，各版本均为180组。两个区域及其生成分布在开发阶段已知。')
    source=source.replace('冷启动和后续出现新单元时的几何处理均应计入运行成本。',
                          '当前计时包含冷缓存填充和后续新增细格处理，但M初始对象构造在计时外，A1每批对象构造在计时内。该差异未单独量化，比较因此包含对象生命周期的影响。')
    source=source.replace('两张曲线均包含首批几何建立和后续新增单元处理。A1每批重建，展示缓存对本实现成本的作用。',
                          '两张曲线均包含首批几何建立和后续新增单元处理。A1每批重建对象及组合分类状态，M跨批保留这些状态，比较涉及三层缓存及对象生命周期。')
    source=source.replace('图中线为3个种子中位数的平均值，阴影为种子范围。首批与新增细格的完整处理均计入。',
                          '图中线为3个种子中位数的平均值，阴影为种子范围。首批几何分类和新增细格处理已计时，M初始对象构造未计时。')
    source=source.replace('累计缓存数直接来自每批新增单元日志，所有新增几何判断已计入计时。',
                          '累计缓存细格数为len(local.parents)的条目数量，由new_cells序列累加得到，不是三层缓存命中次数或full接口调用次数。新增几何判断已计时。')
    source=source.replace('网页GPT技术审查由执行助手代发，实际问题和回复分别归档。',
                          '早期独立网页技术审查由执行助手代发。后续分享会话从原理提问到结果审查，共9轮、18条消息，已从页面首尾逐段导出。讨论中的任务口径、压力数据边界和归因限制按实际消息记录，不据发送身份推定独立首创。')
    source=source.replace('早期会话接口未返回的原图以附件占位说明保留，文字问答按接口返回内容导出。',
                          '主要分享会话保留文字、表格、代码、TeX公式及9幅原始SVG图，逐消息页面原始导出另存压缩文件。其他早期会话中未返回的附件仍保留占位说明。')
    source=source.replace('## 9 修订版结果与适用条件','## 9 修订版结果、消融与适用条件')
    rows=list(csv.DictReader((root/'results/derived_v2/workload_summary.csv').open(encoding='utf-8-sig')))
    additions=['### 跨批状态复用与阶段累计成本','',
               'A1与M采用相同的局部分类与风险点回退规则。A1每批创建新对象，M跨新批次保留parents、full_cells和guarded三层状态。因此，二者比较反映组合状态复用与对象生命周期的总体成本差异，不能分离各缓存组件的独立贡献，也不能解释为M减少了风险点重编码。', '',
               '| 分布 | 每批点数 | 20批A1累计秒 | 20批M累计秒 |','|---|---|---|---|']
    for r in rows:
        if int(r['batches'])==20:additions.append(f"| {r['distribution']} | {r['points_per_batch']} | {float(r['A1_cumulative_seed_mean_s']):.4f} | {float(r['M_cumulative_seed_mean_s']):.4f} |")
    additions+=['','M在六组条件中均快于A1，但只有每批10万点的两组在20批时快于B1。A1与M的差异不能替代与直接编码基线的比较。当前仅有3个成本种子，未作显著性检验。','',
                '| 分布 | 每批点数 | 累计批数 | B1累计秒 | M累计秒 |','|---|---|---|---|---|']
    for r in rows:
        if int(r['points_per_batch'])==100000:additions.append(f"| {r['distribution']} | 100000 | {r['batches']} | {float(r['B1_cumulative_seed_mean_s']):.4f} | {float(r['M_cumulative_seed_mean_s']):.4f} |")
    additions+=['','修订版在首批和5批累计时仍慢于B1，在20批检查点才观察到累计优势。这与几何处理成本逐步摊销的解释一致，但不能确定普适盈亏平衡批次。每批点数、占用格密度和新增格比例未独立操纵，现有结果不识别密度的单独因果效果。', '',
                '成本脚本在计时结束后断言M、A1和B1的Counter相同，只检查该批粗格计数。逐点归属一致性由单独的180组评测提供。现有日志未分别保存几何筛选、顶点探测、风险点编码和计数聚合的分项耗时，不据总耗时分配这些环节的贡献。','']
    source=source.replace('## 10 研究取舍与AI协作说明','\n'.join(additions)+'\n## 10 研究取舍与AI协作说明')
    source=source.replace('## 11 结论','补充技术审查记录 https://github.com/Augen-Jik/h3-boundary-aggregation-study/blob/main/conversations/02_web_gpt_review.md\n\n## 11 结论')
    start=source.index('在本次结果复核中，作者选择')
    end=source.index('\n\n作者提供选题计划',start)
    source=source[:start]+('作者在结果复核中选择将方法限定为已有细格编码、保留原坐标且较密集新批次条件下的条件性优化。'
                          '这一定位依据第9节的收益与负结果，保留首次几何处理的成本，不采用通用加速主张。')+source[end:]
    start=source.index('作者提供选题计划')
    end=source.index('\n\n公开对话',start)
    source=source[:start]+('作者确定选题、执行范围和上述研究定位。AI协助资料核查、方案细化、编程、实验、审计、绘图与写作。'
                          '早期网页技术审查由执行助手代发，后续分享会话保留9轮实际问答。任务口径、数据设计和归因限制按实际讨论归属，'
                          '不据发送身份推定独立首创。分工见decisions.md，discussion_plan.md是AI辅助提纲，不属于已经发生的对话。')+source[end:]
    return source
