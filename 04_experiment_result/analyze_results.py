#!/usr/bin/env python3
"""Reproduce RQ1/RQ3 from the evaluation records (Python 3.10+).

RQ13_runs.json contains measurements for five runs per configuration.
Documented infrastructure failures are excluded from the main analysis.
Only the Python standard library is needed for statistics and LaTeX table rows.
"""
import csv
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "analysis"
SYSTEMS = ["uml2code", "kilocode", "opencode", "openhands", "claudecode"]
MODELS = ["claude-opus-4-6", "claude-sonnet-4-6"]
KEYS = ["system", "model", "layer", "eval_id"]


def condition(row):
    return tuple(row[k] for k in KEYS)


def load_records():
    rows = json.loads((HERE / "RQ13_runs.json").read_text(encoding="utf-8"))
    assert len(rows) == 750
    assert len({r["run_id"] for r in rows}) == len(rows)
    counts = Counter(condition(r) for r in rows)
    assert len(counts) == 150 and set(counts.values()) == {5}
    manifest = json.loads((HERE / "RQ13_analysis_manifest.json").read_text(encoding="utf-8"))
    decisions = {r["run_id"]: r for r in manifest["runs"]}
    assert set(decisions) == {r["run_id"] for r in rows}
    for row in rows:
        assert row["analysis_include"] == decisions[row["run_id"]]["analysis_include"]
        assert row["analysis_reason"] == decisions[row["run_id"]]["analysis_reason"]
        assert row["expected_ut_total"] > 0
        if not row["analysis_include"]:
            assert decisions[row["run_id"]]["evidence"], "Exclusions require evidence"
    return rows


def normalize(rows):
    result = []
    for raw in rows:
        row = dict(raw)
        row["raw_ut_total"] = raw["ut_total"]
        row["raw_ut_passed"] = raw["ut_passed"]
        row["raw_ut_status"] = raw["ut_status"]
        row["ut_total"] = raw["expected_ut_total"]
        if not raw["compile_success"] or raw["ut_total"] == 0:
            row["ut_passed"] = 0
        assert 0 <= row["ut_passed"] <= row["ut_total"]
        row["ut_failed"] = row["ut_total"] - row["ut_passed"]
        row["ut_score"] = row["ut_passed"] / row["ut_total"]
        row["ut_status"] = "success" if (
            raw["ut_status"] == "success" and row["ut_passed"] == row["ut_total"]
        ) else "failure"
        result.append(row)
    return result


def load_paper_runs():
    """The identical analysis cohort for correctness and execution cost."""
    return normalize([r for r in load_records() if r["analysis_include"]])


def handler_macro_mean(rows, field):
    """Average within each (layer, handler), then weight handlers equally."""
    handlers = defaultdict(list)
    for row in rows:
        handlers[(row["layer"], row["eval_id"])].append(row[field])
    return statistics.mean(statistics.mean(values) for values in handlers.values())


def summarize(rows):
    output = []
    for system in SYSTEMS:
        for model in MODELS:
            group = [r for r in rows if (r["system"], r["model"]) == (system, model)]
            handlers = defaultdict(list)
            for r in group:
                handlers[(r["layer"], r["eval_id"])].append(r)
            assert len(handlers) == 15
            output.append({
                "system": system, "model": model, "n_runs": len(group), "n_handlers": len(handlers),
                "spr": statistics.mean(r["ut_status"] == "success" for r in group),
                "micro_cpr": sum(r["ut_passed"] for r in group) / sum(r["ut_total"] for r in group),
                "macro_cpr": statistics.mean(statistics.mean(r["ut_score"] for r in h) for h in handlers.values()),
                "tokens_k": handler_macro_mean(group, "token_total") / 1000,
                "llm_calls": handler_macro_mean(group, "llm_calls"),
                "tool_calls": handler_macro_mean(group, "tool_call_count"),
                "run_mean_tokens_k": statistics.mean(r["token_total"] for r in group) / 1000,
                "run_mean_llm_calls": statistics.mean(r["llm_calls"] for r in group),
                "run_mean_tool_calls": statistics.mean(r["tool_call_count"] for r in group),
            })
    return output


def write_json(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(name, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def summarize_traces(rows):
    traces = json.loads((HERE / "RQ3_trace_counts.json").read_text(encoding="utf-8"))
    expected = {r["run_id"]: r for r in rows if r["system"] in ("uml2code", "claudecode")
                and r["model"] == "claude-opus-4-6"}
    assert len(traces) == len(expected)
    assert {r["run_id"] for r in traces} == set(expected)
    for trace in traces:
        original = expected[trace["run_id"]]
        assert condition(trace) == condition(original)
        assert trace["total_tool_calls"] == original["tool_call_count"]
        assert trace["llm_calls"] == original["llm_calls"]
    fields = ["protocol", "specification_reads", "edits", "compiles", "total_tool_calls", "llm_calls"]
    summary = []
    for system in ["uml2code", "claudecode"]:
        group = [r for r in traces if r["system"] == system]
        assert len({(r["layer"], r["eval_id"]) for r in group}) == 15
        summary.append({"system": system, "model": "claude-opus-4-6", "n_runs": len(group),
                        **{field: handler_macro_mean(group, field) for field in fields},
                        **{"run_mean_" + field: statistics.mean(r[field] for r in group) for field in fields}})
    write_json("rq3_trace_summary.json", summary)
    write_csv("rq3_trace_summary.csv", summary)
    labels = ["Protocol (fetch/todo/done)", "Specification/top-level reads", "Edit", "Compile",
              "Total tool calls", "LLM calls"]
    lines = [f"{label} & {summary[0][field]:.1f} & {summary[1][field]:.1f} " + r"\\"
             for label, field in zip(labels, fields)]
    (OUT / "rq3_trace_table_rows.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    raw = load_records()
    rows = load_paper_runs()
    summary = summarize(rows)
    write_json("runs.json", rows)
    write_json("summary.json", summary)
    write_csv("summary.csv", summary)
    by_handler = []
    groups = defaultdict(list)
    for r in rows:
        groups[condition(r)].append(r)
    for key, group in sorted(groups.items()):
        by_handler.append({**dict(zip(KEYS, key)), "n_runs": len(group),
                           "cpr": statistics.mean(r["ut_score"] for r in group),
                           "spr": statistics.mean(r["ut_status"] == "success" for r in group),
                           "tokens_k": statistics.mean(r["token_total"] for r in group) / 1000,
                           "llm_calls": statistics.mean(r["llm_calls"] for r in group),
                           "tool_calls": statistics.mean(r["tool_call_count"] for r in group)})
    write_csv("by_handler.csv", by_handler)
    summarize_traces(rows)
    write_json("sensitivity_including_infrastructure_failures.json", summarize(normalize(raw)))
    # Diagnostic comparison only; the main tables include all interrupted runs.
    target = [r for r in rows if r['system'] == 'claudecode' and r['model'] == 'claude-sonnet-4-6']
    interrupted = [r for r in target if r['analysis_reason'] == 'model_output_limit_interruption']
    failed = {r['run_id'] for r in interrupted if r['ut_status'] != 'success'}
    diagnostic = [r for r in target if r['run_id'] not in failed]
    assert len(interrupted) == 6 and len(failed) == 5
    def diagnostic_summary(group):
        return dict(n_runs=len(group), n_suite_passed=sum(r['ut_status'] == 'success' for r in group),
                    spr=statistics.mean(r['ut_status'] == 'success' for r in group),
                    micro_cpr=sum(r['ut_passed'] for r in group) / sum(r['ut_total'] for r in group),
                    macro_cpr=handler_macro_mean(group, 'ut_score'))
    write_json('output_truncation_diagnostic.json', dict(
        interrupted_runs=6, interrupted_suite_passed=1, interrupted_suite_not_passed=5,
        diagnostic_excluded_run_ids=sorted(failed),
        main=diagnostic_summary(target), diagnostic=diagnostic_summary(diagnostic),
        scope='Diagnostic comparison only; all six interrupted runs are included in the main results.'))
    labels = {"uml2code": r"\agentname{}", "kilocode": "Kilo Code", "opencode": "OpenCode",
              "openhands": "OpenHands", "claudecode": "Claude Code"}
    table = []
    for model, short in zip(MODELS, ["Opus", "Sonnet"]):
        table += [rf"\multicolumn{{5}}{{l}}{{\textit{{{short}}}}} \\", r"\midrule"]
        for system in SYSTEMS:
            r = next(r for r in summary if r["system"] == system and r["model"] == model)
            table.append(f"{labels[system]} & {r['n_runs']} & {r['spr']:.3f} & "
                         f"{r['micro_cpr']:.3f} & {r['macro_cpr']:.3f} " + r"\\")
        table.append(r"\midrule" if short == "Opus" else r"\bottomrule")
    (OUT / "rq1_table_rows.tex").write_text("\n".join(table) + "\n", encoding="utf-8")
    print(f"Evaluated records: {len(raw)}; analyzed: {len(rows)}; infrastructure exclusions: {len(raw)-len(rows)}")
    for r in by_handler:
        if r["n_runs"] < 5:
            print("Limited sample:", *(r[k] for k in KEYS), "n=", r["n_runs"])


if __name__ == "__main__":
    main()
