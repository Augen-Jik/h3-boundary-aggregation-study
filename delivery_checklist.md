# 课程项目交付核查

作者 jinchenying。以下状态由实际结果与文件核查支持。

| 要求 | 交付证据 | 状态 |
|---|---|---|
| 具体切入点与知识边界 | report.md第1、2节，细格父级与直接粗编码的点计数口径 | 完成 |
| 可复现反例 | results/pilot，实际坐标及边界图 | 完成 |
| 原版开发与评测 | 90组开发、180组评测、180万次点归属检查 | 完成 |
| 原版成本与不利结果 | workload_snapshot，18条成本工作负载，7次重复 | 完成 |
| 数值边界失败保留 | supplement/boundary_probes.json，46080次检查中的4条误判 | 完成 |
| 修订版回归与开发 | revision_v2，46080次边界检查、90组开发 | 完成 |
| 修订版新评测 | 种子200至209，180组，180万次点归属检查 | 完成 |
| 修订版新成本 | 种子200至202，18条工作负载，20批次与7次重复 | 完成 |
| 强基线与输入条件 | 不变数据计数复制、已有细格输入和端到端成本范围 | 已在报告解释 |
| 实验覆盖与版本绑定 | results/derived/experiment_coverage_audit.json | 通过 |
| 实际AI协作记录 | conversations/README.md索引及6个实际记录文件 | 已整理并脱敏 |
| 记录完整性边界 | 早期原图未由接口返回，附件占位保留；内部推理不导出 | 已明确披露 |
| 最终图文报告 | report.md、output/pdf/H3_course_report.pdf | 14页、13图 |
| PDF结构与逐页视觉检查 | results/derived/report_structural_audit.json、final_delivery_audit.json | 通过 |
| 署名与贡献说明 | 唯一署名jinchenying，AI参与及代拟问题如实说明 | 完成 |
| 公开提交入口 | https://github.com/Augen-Jik/h3-boundary-aggregation-study | 最终文件随本清单发布 |

独立评测仅指同一已知区域和生成分布下的新随机种子，不是空间域外泛化。有限探测不能代替几何证明。原版与修订版性能分别与各自同期直接编码基线比较，不把不同种子的版本差异解释为因果效果。

