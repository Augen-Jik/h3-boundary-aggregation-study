"""Finalize only after complete v2 data exist. All cost values come from CSV."""
import csv
import json
from pathlib import Path

root = Path(__file__).parent
audit = json.loads((root / "results/derived/experiment_coverage_audit.json").read_text())
assert {r["version"] for r in audit["reports"]} == {"v1", "v2"}
assert all(r["coverage_pass"] for r in audit["reports"])
with (root / "results/derived_v2/workload_summary.csv").open(encoding="utf-8-sig") as f:
    costs = list(csv.DictReader(f))
assert len(costs) == 18
twenty = [r for r in costs if int(r["batches"]) == 20]
assert len(twenty) == 6
ratios = {r["distribution"]: float(r["direct_over_local_ratio_mean"])
          for r in twenty if int(r["points_per_batch"]) == 100000}
source = (root / "report_draft.md").read_text(encoding="utf-8")
source = source.replace("状态 实验结果部分已核验，成本实验与提交核查进行中", "研究范围 两处局部区域的合成点计数与重复新批次成本")
source = source.replace("代码、独立评测数据、图表与本初稿已上传公开仓库。对话文件是截至导出时的快照，最终提交前需补齐之后新增内容。", "代码、原始结果、图表与报告已公开。对话记录保留实际提问、公开回答、失败与修订，服务器凭据脱敏。")
start = source.index("本项目研究一种具体的空间统计口径差异。")
end = source.index("\n\n## 1 ", start)
abstract = ("本项目研究已有细分辨率H3编码的点数据如何汇总到直接粗编码口径。原版局部重编码在180组随机评测中逐点一致，"
            "但后续46080次极近边界检查发现4条内部筛选误判。针对该机制，修订版增加顶点余量探测，重新通过边界回归与90组开发验证，"
            "并使用新种子200至209完成180组评测，180万次点归属检查均与直接粗编码一致。效率以18条不同新批次工作负载测量，"
            f"每批10万点、累计20批时，修订版的直接编码耗时与局部方法耗时之比为U组{ratios['U']:.3f}、C组{ratios['C']:.3f}。"
            "比值大于1表示局部方法更快，小于1表示更慢。每批1000与10000点时，20批内修订版仍更慢。结果支持对正确性边界、缓存成本与适用条件进行具体分析，不能提供全球零误差保证。")
source = source[:start] + abstract + source[end:]
source = source.replace("## 6 独立评测结果", "## 6 修订前的随机评测结果")
source = source.replace("实际 AI 对话 Markdown", "完整协作记录索引 https://github.com/Augen-Jik/h3-boundary-aggregation-study/blob/main/conversations/README.md  \n实际 AI 对话 Markdown", 1)
source = source.replace("## 5 最小反例", "实验运行于Intel Xeon Platinum 8352V 2.10GHz的Linux容器，CPU配额12核。计时进程将OMP、MKL与OPENBLAS线程数设为1，四种方法串行交错执行。Python3.12，H3 Python/C均为4.5.0，numpy1.26.4、pyproj3.8.0。GPU未被项目代码调用。数据生成、绘图和正确性审计位于计时之外；各方法必需的编码、几何检查、查询和计数聚合均在相应计时范围内。\n\n## 5 最小反例")
source = source.replace("## 7 成本与适用条件", "## 7 修订前的成本与适用条件")
source = source.replace("### 数值边界修订与新的评测", "### 数值边界修订与新的评测")
source = source.replace("修订版成本另用种子200至202运行，原版速度结果不作为修订版速度证据。", "修订版成本另用种子200至202完成18条工作负载，原版速度结果不作为修订版速度证据。")
source = source.replace("当前方法仍需保守修复和新的验证，原成本收益也仅针对原实现。", "该发现触发了单独登记的修订与新种子验证。原成本收益仅针对原实现。")
source = source.replace("## 9 AI协作与个人贡献记录", "## 10 AI协作与个人贡献记录")
old_collaboration = "用户提供选题计划和老师要求，指定研究执行范围与作者署名。AI实现数据生成、方法、实验审计和图表，并另向网页GPT提交真实技术审查请求。该请求已注明由执行助手代发。尚未由作者表达的反驳与感想不写成实际发生的互动。Codex实际记录及网页GPT问答已分别导出Markdown，导出后新增内容需在最终提交前补齐。"
new_collaboration = "我提供选题计划和老师要求，确定研究执行与提交范围，并委托AI协助编程、远程实验、审计、绘图与报告制作。网页GPT技术审查由执行助手代发，记录明确标注这一事实。设计与技术执行中AI参与较深，decisions.md登记了具体分工。Codex实际记录与网页GPT问答分别导出Markdown，保留错误、修订和真实工具结果。随机样本一致之后又发现数值边界失败，这一过程表明，协作评价需要检查证据覆盖范围，不能仅凭AI的初步结论判断方法可靠性。"
assert old_collaboration in source
source = source.replace(old_collaboration, new_collaboration)
source = source.replace("我提供选题计划和老师要求", "早期原理讨论提出了核查官方知识、区分已有常识与探索空间的要求，实际问答也已归档。我提供选题计划和老师要求", 1)
source = source.replace("保留错误、修订和真实工具结果。", "保留错误、修订和真实工具结果。早期会话接口未返回的图片以占位说明保留，没有重建原图；文字问答按接口返回内容完整导出。", 1)
section = ["## 9 修订版的完整结果与成本", "",
           "修订版180组新种子评测的逐点差异和归一化计数差异均为0。下面的成本与原版分别计量，每条工作负载含20个不同新批次，每个种子重复7次。先取种子内累计耗时中位数，再汇总3个种子。", "",
           "| 分布 | 每批点数 | B1累计秒 | M2累计秒 | B1/M2 |", "|---|---|---|---|---|"]
for r in twenty:
    section.append(f"| {r['distribution']} | {r['points_per_batch']} | {float(r['B1_cumulative_seed_mean_s']):.4f} | "
                   f"{float(r['M_cumulative_seed_mean_s']):.4f} | {float(r['direct_over_local_ratio_mean']):.3f} |")
section += ["", "![修订版均匀分布累计成本](figures_v2/cumulative_U_100000.png)", "",
            "![修订版聚集分布累计成本](figures_v2/cumulative_C_100000.png)", "",
            "图中线为3个种子中位数的平均值，阴影为种子范围。首批与新增细格的完整处理均计入。原版和修订版采用不同独立种子，版本间耗时差异仅作描述；修订版与同期B1、A1的对照用于判断其实际成本。", "",
            "| 分布 | 每批点数 | 20批后Python缓存相关保留内存 MiB |", "|---|---|---|"]
for r in twenty:
    section.append(f"| {r['distribution']} | {r['points_per_batch']} | {float(r['retained_python_bytes_mean_at_20']) / 1024 ** 2:.3f} |")
section += ["", "内存单独使用tracemalloc测量，覆盖Python分配而非C库全部驻留内存。已有细格编码是各方法共同的输入前提；从原始坐标开始还需考虑细编码、数据组织和存储成本，不能将这里的增量耗时比直接称作端到端加速。", ""]
section += ["| 分布 | 每批点数 | 首批每个已占用细格的平均点数 N/U | 20批累计缓存细格数 |", "|---|---|---|---|"]
for r in twenty:
    section.append(f"| {r['distribution']} | {r['points_per_batch']} | {float(r['first_batch_points_per_occupied_fine_mean']):.3f} | {float(r['geometry_entries_mean']):.1f} |")
section += ["", "N/U先在每个种子的首个批次计算，再对3个种子平均。它描述占用密度，不能与后续批次的新单元数量混为一项。累计缓存数直接来自每批新增单元日志，所有新增几何判断已计入计时。", ""]
section += ["数值余量使用角度单位，约束的是探测坐标的变化。它不是全球统一的米制缓冲距离，不同纬度的物理尺度不同。当前实验只覆盖指定中纬度区域，不推断极区或跨日期变更线的可靠性。", ""]
source = source.replace("## 10 AI协作与个人贡献记录", "\n".join(section) + "\n## 10 AI协作与个人贡献记录")
conclusion = ("## 11 结论\n\n本作业将H3层级与几何口径差异转化为可复现的点计数实验，并通过极近边界检查发现了常规随机评测遗漏的失败。"
              "保守修订在新随机样本和已登记边界回归中得到逐点一致，但有限数值探测仍不构成全域证明。"
              "几何缓存是否值得采用，应同时检查批次规模、格内密度、首次建立成本、新单元增量与原始坐标是否可用。"
              "同一份不变数据的重复查询可优先保存粗计数。所有不利结果与失败证据均随报告公开。\n\n")
source = source.replace("## 参考资料", conclusion + "## 参考资料")
assert "成本实验进行中" not in source
(root / "report.md").write_text(source, encoding="utf-8")
print(root / "report.md")
