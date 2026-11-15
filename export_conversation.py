"""Export displayed H3 messages and tool records, excluding hidden reasoning."""
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

source = Path(r"C:\Users\Augen\.codex\sessions\2026\11\08\rollout-2026-11-08T13-24-20-01a1b966-6db0-7ca0-9a55-5e031202a794.jsonl")
root = Path(__file__).parent
output = root / "conversations"
output.mkdir(exist_ok=True)
lines = []
active = False
counts = Counter()
first = None
last = None
for index, line in enumerate(source.open(encoding="utf-8")):
    record = json.loads(line)
    if record.get("type") != "response_item":
        continue
    item = record.get("payload", {})
    if not active:
        active = item.get("role") == "user" and "根据该计划和脚本" in str(item)
    if not active:
        continue
    kind = item.get("type")
    if kind == "reasoning" or item.get("channel") == "analysis":
        continue
    if kind == "message":
        if item.get("role") not in ("user", "assistant"):
            continue
        content = "\n".join(c.get("text", "[Non-text content: " + c.get("type", "unknown") + "]")
                            for c in item.get("content", []))
        role = item["role"].title()
        if "<codex_internal_context" in content:
            role += " / 自动目标上下文"
        body = content
    elif kind in ("function_call", "custom_tool_call", "function_call_output", "custom_tool_call_output"):
        role = "Tool / " + kind
        body = "````json\n" + json.dumps(item, ensure_ascii=False, indent=2) + "\n````"
    else:
        continue
    # Match credentials introduced by the Chinese field name, across JSON escapes.
    body = re.sub(r"(密码\s*[:：]?\s*)[A-Za-z0-9]{8,}", r"\1[已脱敏：服务器密码]", body)
    body = re.sub(r"(?i)(password\s*[=:]\s*['\"]?)[A-Za-z0-9]{8,}", r"\1[REDACTED PASSWORD]", body)
    stamp = record.get("timestamp", "unknown")
    lines.append(f"## {role} · {stamp}\n\n{body}\n")
    counts[kind] += 1
    first = first or index
    last = index
header = """# H3 课程项目实际 AI 协作记录

平台为 Codex 桌面应用。本文件来自本地当前会话的实际记录，按原顺序保存H3项目开始后的用户消息、公开AI回答及工具调用和结果。自动目标上下文另外标注，不能当作作者再次主动提问。隐藏推理和重复计费事件不导出。服务器密码字段脱敏。网页GPT技术审查是另一个真实会话，尚须单独导出，其内容没有由本文件重建。

本文件是截至导出时的快照。此后新增对话需重新导出。前置STAG研究对话不属于本课程项目，未混入。计划书中的逐轮问题属于脚本，不能当作已经发生的学生对话。

"""
text = header + "\n".join(lines)
path = output / "01_codex_actual.md"
path.write_text(text, encoding="utf-8")
manifest = dict(source_session_id="01a1b966-6db0-7ca0-9a55-5e031202a794",
                first_source_line=first, last_source_line=last, counts=dict(counts),
                output_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                excluded="hidden reasoning, duplicate event records, pre-H3 material",
                redacted="server password fields", website_review_export_complete=False)
(output / "export_manifest.json").write_text(json.dumps(manifest, indent=2))
print(json.dumps(manifest))
