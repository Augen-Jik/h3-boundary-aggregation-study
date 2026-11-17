# H3 跨分辨率聚合中的边界归属偏差与局部重编码方法

作者 jinchenying。数据挖掘与技术课程报告。AI参与的任务与实际讨论记录见conversations目录。

本仓库研究已具备细分辨率H3编码、且保留原始坐标的点数据如何汇总到直接粗编码口径。实验实现按已占用细格筛选的局部重编码与几何缓存，比较逐点归属、聚合计数、热点集合及运行成本。

## 结果概要

原版与修订版各完成90组开发验证、180组随机评测及18条成本工作负载。原版在46080次极近边界检查中出现4条误判。修订版通过已登记边界回归，并在新种子评测中得到逐点一致结果。每批10万点、累计20个新批次时，修订版相对同期直接编码的耗时比B1/M2为U组1.108、C组1.124；每批1000与10000点时仍较慢。因此，方法定位为已有细格编码、较密集新批次任务下的条件性优化。

在指定SSH服务器完成M3补充实验，包含21条成本序列、9条空间漂移序列、108组新区域检查及旧失败回归。M3沿用M2分类器，以格内点数直接汇总安全细格。每批10万点、累计20批时，相对每个种子中较快的直接编码参照，平均耗时比为U组1.071、C组1.089。小批次与边界压力组仍较慢，三种漂移条件在10批内均未获得累计优势。新增四个区域共54万点的M2逐点差异与M3计数差异均为0，但这不构成全球正确性证明。完整条件、种子范围与内存负结果见报告第12节。

- [主要对话：与ai对话过程](conversations/)
- [补充实验结果复核对话（完整10轮）](conversations/05补充实验结果复核对话.md)
- [最终报告 Markdown](report.md)
- [课程报告 Word 可编辑版](output/docx/H3_course_report.docx)
- [课程报告 PDF](output/pdf/H3_course_report.pdf)
- [补充实验协议、代码与说明](supplement_20261117/)
- [补充实验审计与全部结果汇总](supplement_20261117/derived/summary.json)
- [补充实验逐种子成本表](supplement_20261117/derived/seed_results.csv)
- [既有日志的补充分析](supplement_analysis/analysis.json)
- [修订版实验分层汇总](results/derived_v2/independent_summary.csv)
- [原版实验分层汇总](results/derived/independent_summary.csv)
- [原始记录重新计算审计](results/derived/current_results_audit.json)
- [提交核查清单](delivery_checklist.md)
- [实验覆盖与源码绑定审计](results/derived/experiment_coverage_audit.json)

## 复现

Python3.12，H3 Python/C4.5.0，numpy1.26.4，pyproj3.8.0，matplotlib3.9.4。创建独立环境后按requirements.txt安装。数据全部为合成观测点，输入规则见datasets.py。

```bash
python reproduce.py --version v1 --output /absolute/path/h3_v1_rerun
python reproduce.py --version v2 --output /absolute/path/h3_v2_rerun
```

每次复现串行运行边界检查、开发验证、随机评测与成本实验。修订版若边界检查失败会停止并保留记录。只检查入口而不运行实验时可添加--prepare-only。不要同时启动两个计时任务。

绘图由summarize.py、summarize_workloads.py、extra_figures.py与boundary_figure.py生成。添加--revision-v2可汇总修订版，原版读取snapshot/results/evaluation与workload_snapshot，修订版读取revision_v2/results。配置和代码冻结于评测结果目录。resume_fix.json记录JSON配置比较修复，旧计时和修改前源码保留在recovery_evidence。verify_experiments.py在全量结果齐全后核对两个版本。

补充实验的独立复现步骤见[supplement_20261117/README.md](supplement_20261117/README.md)。从现有结果重新生成分析与报告时依次运行以下程序，无需再次运行计时任务。

```bash
python analyze_supplement.py
python summarize_supplement_v3.py
python kernel_figure.py
python update_supplement_report.py
python build_report_pdf.py
python build_report_docx.py
python verify_report.py
python verify_final_delivery.py --visual-reviewed 25 23
```


## 资料与局限

- [H3官方层级说明](https://h3geo.org/docs/highlights/indexing/)
- [h3-py接口](https://uber.github.io/h3-py/api_verbose.html)
- [full模式已知问题报告](https://github.com/uber/h3/pull/1271)

full接口是实验功能，局部样本一致性不构成全域安全证明。B为边界压力分布，不能并入常规数据声称真实城市平均差异。已有细格编码为上游输入，计时与从原坐标开始的端到端成本应分别解释。相同不变数据重复查询时，预存粗计数是必要强基线。
