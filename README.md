# H3 跨分辨率聚合中的边界归属偏差与局部重编码方法

作者 jinchenying。数据挖掘与技术课程项目，AI辅助过程与贡献如实记录。

本仓库研究已知细格编码的点数据如何汇总到指定粗格口径。H3的逻辑父子索引与严格几何包含不同，这是已有知识。本项目实现局部重编码与几何缓存，并测量逐点、计数、热点与运行成本。

## 当前状态

最终报告、代码、原始结果、图表及实际AI协作记录已整理。原版与修订版各有90组开发、180组随机评测与18条成本工作负载。原版46080次极近边界检查发现4条误判，证据完整保留；修订版边界回归及新种子评测均逐点一致。修订版在每批10万点、20个新批次时的B1/M2耗时比为U组1.108、C组1.124；每批1000与10000点时仍更慢。结论限定测试区域、库版本与输入条件。

- [最终图文报告 PDF](output/pdf/H3_course_report.pdf)
- [最终报告 Markdown](report.md)
- [报告初稿与演进](report_draft.md)
- [题目计划与提示脚本](proposal.md)
- [老师要求](teacher_requirements.md)
- [实际设计决定与证据范围](decisions.md)
- [实验分层汇总](results/derived/independent_summary.csv)
- [全部实际协作记录索引](conversations/README.md)
- [实际Codex协作记录](conversations/01_codex_actual.md)
- [网页GPT技术审查](conversations/02_web_gpt_review.md)
- [提交核查清单](delivery_checklist.md)
- [实验覆盖与源码绑定审计](results/derived/experiment_coverage_audit.json)
- [PDF结构核查](results/derived/report_structural_audit.json)

## 复现

Python3.12，H3 Python/C4.5.0，numpy1.26.4，pyproj3.8.0，matplotlib3.9.4。创建独立环境后按requirements.txt安装。数据全部为合成观测点，输入规则见datasets.py。

建议在Linux与Python3.12下创建独立环境后执行以下命令，输出目录必须不存在。

```bash
python reproduce.py --version v1 --output /absolute/path/h3_v1_rerun
python reproduce.py --version v2 --output /absolute/path/h3_v2_rerun
```

每次复现串行运行边界检查、开发验证、随机评测与成本实验。修订版若边界检查失败会停止并保留记录。只检查入口而不运行实验时可添加--prepare-only。不要同时启动两个计时任务。

绘图由summarize.py、summarize_workloads.py、extra_figures.py与boundary_figure.py生成。添加--revision-v2可汇总修订版，原版读取snapshot/results/evaluation与workload_snapshot，修订版读取revision_v2/results。配置和代码哈希冻结于评测结果目录。resume_fix.json记录JSON配置比较修复，旧计时和修改前源码保留在recovery_evidence。verify_experiments.py在全量结果齐全后核对两个版本。

PDF排版另使用requirements-report.txt，源文件为build_report_pdf.py，Windows下读取系统宋体。该脚本将报告渲染成PDF并生成逐页PNG供检查。实验环境与绘图环境分别记录，results/render_environment.json保存实际本地绘图依赖；原始实验在远端固定版本执行。排版、绘图与数据生成均不计入方法运行时间。

结果与图表齐全后，依次运行verify_experiments.py、finalize_report.py、build_report_pdf.py --final和verify_report.py。实际对话是截至导出时的快照，范围与排除项见conversations/export_manifest.json。网页GPT原始问答中的引用标记按原文保留，报告正文使用可访问的来源链接。

## 资料与局限

- [H3官方层级说明](https://h3geo.org/docs/highlights/indexing/)
- [h3-py接口](https://uber.github.io/h3-py/api_verbose.html)
- [full模式已知问题报告](https://github.com/uber/h3/pull/1271)

full接口是实验功能，局部样本一致性不构成全域安全证明。B为边界压力分布，不能并入常规数据声称真实城市平均差异。已有细格编码为上游输入，计时与从原坐标开始的端到端成本应分别解释。相同不变数据重复查询时，预存粗计数是必要强基线。

