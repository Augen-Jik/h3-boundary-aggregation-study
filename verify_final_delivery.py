"""Bind reports, editable tables and experiment evidence to an inspected delivery.

--visual-reviewed records actual page inspection, not an automatic quality test.
Re-render and inspect the documents after changing them.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from docx import Document
from pypdf import PdfReader

ROOT = Path(__file__).parent

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read(path):
    return json.loads(path.read_text(encoding="utf-8"))

def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8", newline="\n")

parser = argparse.ArgumentParser()
parser.add_argument("--visual-reviewed", nargs=2, type=int, metavar=("PDF", "WORD"), required=True)
args = parser.parse_args()
source_path = ROOT / "report.md"
source = source_path.read_text(encoding="utf-8-sig")
tables = []
for block in re.findall(r"(?:^\|.*\n)+", source + "\n", re.M):
    tables.append([[c.strip() for c in line.strip().strip("|").split("|")]
                   for line in block.splitlines()
                   if not re.fullmatch(r"[| :\-]+", line.strip())])
docx_path = ROOT / "output/docx/H3_course_report.docx"
pdf_path = ROOT / "output/pdf/H3_course_report.pdf"
doc = Document(docx_path)
assert len(doc.tables) == len(tables) == 14
cells_checked = 0
for index, (table, expected) in enumerate(zip(doc.tables, tables), 1):
    actual = [[c.text for c in row.cells] for row in table.rows]
    assert actual == expected, ("Word table differs from Markdown", index)
    cells_checked += sum(map(len, expected))
figures = len(re.findall(r"^!\[", source, re.M))
equations = len(doc.element.xpath("//m:oMath"))
assert len(doc.inline_shapes) == figures == 25
assert equations == 1 and doc.core_properties.author == "jinchenying"
pdf = PdfReader(pdf_path)
assert pdf.metadata.author == "jinchenying"
assert args.visual_reviewed == [len(pdf.pages), 23] == [25, 23]
base = ROOT / "supplement_20261117"
summary = read(base / "derived/summary.json")
completion = read(base / "supplement_v3/completion.json")
assert completion["cost_workloads"] == 21 and completion["drift_workloads"] == 9
assert summary["new_region_cases"] == 108 and summary["new_region_points"] == 540000
assert summary["new_region_point_mismatches"] == summary["new_region_count_l1"] == 0
assert summary["workload_count_errors"] == summary["workload_point_errors"] == []
assert summary["regression_rows"] == 12 and summary["regression_failures"] == []
for name, digest in summary["raw_hashes"].items():
    assert sha(base / name) == digest, ("raw evidence changed", name)
for name, digest in summary["environment"]["hashes"].items():
    assert sha(base / name) == digest, ("frozen source changed", name)
structural = read(ROOT / "results/derived/report_structural_audit.json")
assert structural["pdf_sha256"] == sha(pdf_path)
word_audit = dict(author="jinchenying", pages=23, figures=figures,
    editable_tables=len(tables), table_cells_checked=cells_checked,
    native_equations=equations, result_tables_match_markdown=True,
    render_engine="Microsoft Word native PDF export; packaged render_docx.py with PDFium rasterizer",
    visual_page_review="PASS: all 23 rendered pages inspected",
    source_report_sha256=sha(source_path), docx_sha256=sha(docx_path))
write(ROOT / "results/derived/word_report_audit.json", word_audit)
final = dict(date="2026-11-17", author="jinchenying", pdf_pages=25, word_pages=23,
    figures=figures, editable_tables=len(tables), table_cells_checked=cells_checked,
    visual_page_review="PASS: all 25 PDF pages and all 23 Word-rendered pages inspected",
    source_report_sha256=sha(source_path), pdf_sha256=sha(pdf_path), docx_sha256=sha(docx_path),
    required_links_pass=structural["required_links_pass"], new_physical_experiments=True,
    cost_sequences=21, drift_sequences=9, new_region_cases=108, new_region_points=540000,
    regression_checks=12, supplement_source_hashes_pass=True, supplement_raw_hashes_pass=True,
    supplement_point_and_count_checks_pass=True,
    supplement_summary_sha256=sha(base / "derived/summary.json"),
    remote_complete_archive_sha256="f6117c6c29bc309cc5ba51f38577bdc76f7719c1865ebf3050d82b43b6a1cb26",
    remote_run_elapsed_seconds=1062,
    conversation_current_sha256={str(p.relative_to(ROOT / "conversations")): sha(p)
        for p in sorted((ROOT / "conversations").glob("*.md"))},
    conversation_scope="Current author-curated files; hashes identify these files and do not independently prove completeness or authenticity of earlier exports.",
    negative_results_retained="Small batches, boundary pressure, all 10-batch drift settings; streaming baseline uses less Python memory than M3.")
write(ROOT / "results/derived/final_delivery_audit.json", final)
print(json.dumps(final, ensure_ascii=False, indent=2))
