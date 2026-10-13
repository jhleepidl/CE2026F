"""Inspectable HTML, JSON and CSV outputs, including original API records."""
import csv
import html
import json
from pathlib import Path


def save_report(directory, report, key=None):
    directory = Path(directory); directory.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if key and key in text: raise RuntimeError("Secret detected; refusing to save report.")
    temporary = directory / "results.tmp"
    temporary.write_text(text); temporary.replace(directory / "results.json")
    result = report.get("result", {})
    rows = result.get("rows", report.get("partial_rows", []))
    fields = ("case_id", "tier", "repeat", "outcome_points", "outcome_max", "quality", "success", "virtual_minutes", "net_transport_spend_usd", "retained_cancel_fees_usd", "error_type")
    with (directory / "cases.csv").open("w", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=fields); writer.writeheader()
        writer.writerows({k: row.get(k) for k in fields} for row in rows)
    def esc(value): return html.escape(str(value))
    def details(label, value):
        return "<details><summary>" + esc(label) + "</summary><pre>" + esc(json.dumps(value, indent=2, ensure_ascii=False)) + "</pre></details>"
    table = "<table><tr>" + "".join("<th>" + esc(k) + "</th>" for k in fields) + "</tr>"
    table += "".join("<tr>" + "".join("<td>" + esc(r.get(k)) + "</td>" for k in fields) + "</tr>" for r in rows) + "</table>"
    grade = report.get("grade")
    summary = "Provisional public score: " + str(round(grade["score"], 2)) + " / " + str(grade["max_score"]) if grade else "Diagnostic run; no provisional public grade."
    if not grade and result.get("complete"):
        summary = (str(report.get("split")) + " diagnostic: mean travel outcome "
            + str(round(result["outcome_points"], 2)) + " / 90; no official /100 grade.")
    contents = '<!doctype html><html lang="en"><meta charset="utf-8"><title>Travel evaluation</title><style>body{font:16px system-ui;max-width:1100px;margin:32px auto;padding:0 16px}table{border-collapse:collapse}td,th{padding:8px;border:1px solid #ccc}pre{white-space:pre-wrap;overflow-wrap:anywhere}details{margin:16px 0}</style>'
    contents += "<h1>Travel planning with dynamic replanning</h1><p>" + esc(summary) + "</p>"
    usage = result.get("usage", {})
    if usage:
        contents += "<h2>Model usage and cost</h2><p>Estimated API cost (with reported cache discounts): USD " + esc(usage.get("estimated_usd")) + ". Cache-neutral grading cost: USD " + esc(usage.get("grading_usd")) + ". These are separate accounting values; grading cost is not an invoice.</p>"
        contents += "<p>Model requests: " + esc(usage.get("calls")) + "; input tokens: " + esc(usage.get("input_tokens")) + "; cached input: " + esc(usage.get("cached_tokens")) + "; output tokens: " + esc(usage.get("output_tokens")) + ".</p>"
    from .fp_cases import FP_OUTCOME_POINTS, FP_EFFICIENCY_MAX
    points = grade["criterion_points"] if grade else result.get("criterion_points", {})
    if points:
        maxima = dict(FP_OUTCOME_POINTS, efficiency=FP_EFFICIENCY_MAX)
        contents += "<h2>Criterion scores</h2><table><tr><th>Criterion</th><th>Points</th><th>Maximum</th></tr>"
        for name, value in points.items():
            contents += "<tr><td>" + esc(name) + "</td><td>" + esc(round(value, 2)) + "</td><td>" + esc(maxima[name]) + "</td></tr>"
        contents += "</table>"
    if result.get("tiers"):
        contents += "<h2>Scores by difficulty</h2><table><tr><th>Difficulty</th><th>Outcome /90</th><th>Contribution</th><th>Complete success</th></tr>"
        for tier, value in result["tiers"].items():
            contents += "<tr><td>" + esc(tier) + "</td><td>" + esc(round(value["outcome_points"], 2)) + "</td><td>" + esc(round(value["outcome_contribution"], 2)) + " / " + esc(round(value["contribution_max"], 2)) + "</td><td>" + esc(str(value["successful_episodes"]) + " / " + str(value["episodes"])) + "</td></tr>"
        contents += "</table><p>Official balanced banks contribute up to 30 points per tier. API efficiency is added once for the whole bank. Display rounding does not change the stored score.</p>"
    contents += "<h2>Episode results</h2>" + table
    contents += details("Configuration and protocol", {k:report.get(k) for k in ("version", "split", "local_cases_file", "tier_filter", "implementation_sha256", "config", "protected_changes")})
    contents += details("Outcome components and usage", {k:result.get(k) for k in ("complete", "quality", "success_rate", "components", "usage", "tiers")})
    if grade: contents += details("Score calculation", grade)
    for row in rows: contents += details(str(row["case_id"]) + " repeat " + str(row["repeat"]) + ": tools and solver context", row)
    contents += details("Every API request, actual reply and token usage", report.get("requests", []))
    contents += "</html>"
    if key and key in contents: raise RuntimeError("Secret detected in HTML report.")
    (directory / "report.html").write_text(contents)
