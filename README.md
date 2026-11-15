# H3 跨分辨率聚合中的边界归属偏差与局部重编码方法

作者 jinchenying。数据挖掘与技术课程项目，AI辅助过程与贡献如实记录。

本仓库研究已知细格编码的点数据如何汇总到指定粗格口径。H3的逻辑父子索引与严格几何包含不同，这是已有知识。本项目实现局部重编码与几何缓存，并测量逐点、计数、热点与运行成本。

## 当前状态

原版开发90组、随机评测180组和成本18组已完成。之后的46080次极近边界检查发现4条内部误判，全部保留。修订版增加数值余量探测，重新通过边界与90组开发检查，并以新种子200至209完成180组随机评测，均逐点匹配直接编码。修订版成本正在执行。实际Codex记录和网页GPT问答已公开快照，最终报告与对话末次更新仍待完成。

- [报告初稿](report_draft.md)
- [题目计划与提示脚本](proposal.md)
- [老师要求](teacher_requirements.md)
- [实际设计决定与证据范围](decisions.md)
- [实验分层汇总](results/derived/independent_summary.csv)
- [实际Codex协作记录](conversations/01_codex_actual.md)
- [网页GPT技术审查](conversations/02_web_gpt_review.md)
- [提交核查清单](delivery_checklist.md)

## 复现

Python3.12，H3 Python/C4.5.0，numpy1.26.4，pyproj3.8.0，matplotlib3.9.4。创建独立环境后按requirements.txt安装。数据全部为合成观测点，输入规则见datasets.py。

建议在Linux与Python3.12下创建独立环境后执行以下命令，输出目录必须不存在。

```bash
python reproduce.py --version v1 --output /absolute/path/h3_v1_rerun
python reproduce.py --version v2 --output /absolute/path/h3_v2_rerun
```

每次复现串行运行边界检查、开发验证、随机评测与成本实验。修订版若边界检查失败会停止并保留记录。只检查入口而不运行实验时可添加--prepare-only。不要同时启动两个计时任务。

绘图由summarize.py、summarize_workloads.py、extra_figures.py与boundary_figure.py生成。添加--revision-v2可汇总修订版，原版读取snapshot/results/evaluation与workload_snapshot，修订版读取revision_v2/results。配置和代码哈希冻结于评测结果目录。resume_fix.json记录JSON配置比较修复，旧计时和修改前源码保留在recovery_evidence。verify_experiments.py在全量结果齐全后核对两个版本。

## 资料与局限

- [H3官方层级说明](https://h3geo.org/docs/highlights/indexing/)
- [h3-py接口](https://uber.github.io/h3-py/api_verbose.html)
- [full模式已知问题报告](https://github.com/uber/h3/pull/1271)

full接口是实验功能，局部样本一致性不构成全域安全证明。B为边界压力分布，不能并入常规数据声称真实城市平均差异。已有细格编码为上游输入，计时与从原坐标开始的端到端成本应分别解释。相同不变数据重复查询时，预存粗计数是必要强基线。
