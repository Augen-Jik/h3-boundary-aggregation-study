"""Structural final-report checks supplement, and do not replace, page review."""
import hashlib
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

root = Path(__file__).parent
source = (root / "report.md").read_text(encoding="utf-8")
assert not any(word in source for word in ["待导出", "待填", "成本实验进行中", "最终报告尚未"])
images = re.findall(r"!\[[^]]*\]\(([^)]+)\)", source)
assert len(images) >= 8 and all((root / p).is_file() for p in images)
pdf_path = root / (sys.argv[sys.argv.index("--pdf") + 1] if "--pdf" in sys.argv
                   else "output/pdf/H3_course_report.pdf")
reader = PdfReader(pdf_path)
assert reader.metadata.author == "jinchenying"
assert len(reader.pages) >= 8
links = []
pdf_text = "\n".join(page.extract_text() for page in reader.pages)
assert "条件性优化" in pdf_text, "PDF does not contain the current research position"
for page in reader.pages:
    assert len(page.extract_text().strip()) > 30
    for annotation in page.get("/Annots", []):
        action = annotation.get_object().get("/A", {})
        if "/URI" in action:
            links.append(str(action["/URI"]))
required = ["https://github.com/Augen-Jik/h3-boundary-aggregation-study",
            "https://github.com/Augen-Jik/h3-boundary-aggregation-study/blob/main/conversations/01_codex_actual.md",
            "https://github.com/Augen-Jik/h3-boundary-aggregation-study/blob/main/conversations/02_web_gpt_review.md"]
assert all(link in links for link in required), links
export = json.loads((root / "conversations/export_manifest.json").read_text())
assert export["website_review_export_complete"]
assert hashlib.sha256((root / "conversations/01_codex_actual.md").read_bytes()).hexdigest() == export["output_sha256"]
result = dict(pages=len(reader.pages), figures=len(images), author=reader.metadata.author,
              pdf_path=str(pdf_path.relative_to(root)),
              required_links_pass=True, dialogue_hash_pass=True,
              pdf_sha256=hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
              visual_page_review="required separately after latest render")
(root / "results/derived/report_structural_audit.json").write_text(json.dumps(result, indent=2))
print(json.dumps(result))
