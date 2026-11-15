# H3 跨分辨率聚合中的边界归属偏差与局部重编码方法

作者 jinchenying。数据挖掘与技术课程项目，AI辅助过程与贡献如实记录。

本仓库研究已知细格编码的点数据如何汇总到指定粗格口径。H3的逻辑父子索引与严格几何包含不同，这是已有知识。本项目实现局部重编码与几何缓存，并测量逐点、计数、热点与运行成本。

## 当前状态

开发验证90组与独立评测180组已完成。180组覆盖杭州和南京、U/C/B模拟分布、三个分辨率对及种子100至109，共180万次点归属检查，局部方法逐点匹配直接编码。该结果限定测试样本。新批次成本实验正在执行，最终报告和完整实际对话尚未交付。

- [报告初稿](report_draft.md)
- [题目计划与提示脚本](proposal.md)
- [老师要求](teacher_requirements.md)
- [实际设计决定与证据范围](decisions.md)
- [实验分层汇总](results/derived/independent_summary.csv)

## 复现

Python3.12，H3 Python/C4.5.0，numpy1.26.4，pyproj3.8.0，matplotlib3.9.4。创建独立环境后按requirements.txt安装。数据全部为合成观测点，输入规则见datasets.py。

```bash
python pilot.py
python develop.py
python develop_distributions.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python evaluate.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 python workloads.py
```

绘图由summarize.py生成。该脚本读取snapshot/results/evaluation中的180个结果文件。计时数据应在同一安静环境串行运行。配置和代码哈希冻结于评测结果目录。resume_fix.json记录了JSON配置比较修复，原计时保留在timing_contention_preserved目录。

## 资料与局限

- [H3官方层级说明](https://h3geo.org/docs/highlights/indexing/)
- [h3-py接口](https://uber.github.io/h3-py/api_verbose.html)
- [full模式已知问题报告](https://github.com/uber/h3/pull/1271)

full接口是实验功能，局部样本一致性不构成全域安全证明。B为边界压力分布，不能并入常规数据声称真实城市平均差异。已有细格编码为上游输入，计时与从原坐标开始的端到端成本应分别解释。相同不变数据重复查询时，预存粗计数是必要强基线。
