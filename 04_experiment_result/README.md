# Evaluation results and analysis

[Back to the artifact overview](../README.md)

Use this directory to reproduce the paper's execution statistics, tables, and figures for RQ1–RQ4. All required evaluation records are bundled. Running the scripts does not invoke an LLM or require credentials, compilation services, or the original industrial workspace. Precomputed outputs are available in [analysis/](analysis/) and [figures/](figures/).

## Quick start

Use **Python 3.10 or newer**. From the artifact repository root, enter this directory and install the dependencies (preferably in a virtual environment):

```bash
cd 04_experiment_result
python -m pip install -r requirements.txt
```

If you are already in `04_experiment_result`, skip the `cd` command. All commands below run from this directory.

```bash
# RQ1: correctness; RQ3: execution efficiency (shared evaluation records)
python analyze_results.py
python plot_rq1.py
python plot_rq3.py

# RQ2: design-artifact comparison
python analyze_rq2.py
python plot_rq2.py

# RQ4: context management
python analyze_rq4.py
```

The commands refresh the bundled outputs under `analysis/` and `figures/`. RQ1/RQ3 statistical analysis uses only the Python standard library; RQ2/RQ4 analysis also requires `openpyxl`. Plotting uses `matplotlib` and `numpy`. The requirements file covers all six commands.

## Find a result

| Paper result | Command | Main outputs |
|---|---|---|
| RQ1 correctness table and handler heatmap | `analyze_results.py`, `plot_rq1.py` | [summary.csv](analysis/summary.csv), [LaTeX table rows](analysis/rq1_table_rows.tex), [heatmap](figures/rq1_cpr_heatmap.pdf) |
| RQ2 design-artifact execution comparison | `analyze_rq2.py`, `plot_rq2.py` | [summary.csv](analysis/rq2/summary.csv), [LaTeX table rows](analysis/rq2/table_rows.tex), [per-handler figure](figures/rq2_per_handler_cpr.pdf) |
| RQ3 execution costs and trace categories | `analyze_results.py`, `plot_rq3.py` | [summary.csv](analysis/summary.csv), [trace summary](analysis/rq3_trace_summary.csv), [LaTeX trace table rows](analysis/rq3_trace_table_rows.tex), [efficiency figure](figures/rq3_efficiency_overall.pdf) |
| RQ4 context-management comparison | `analyze_rq4.py` | [summary.csv](analysis/rq4/summary.csv), [LaTeX table rows](analysis/rq4/table_rows.tex), [aggregate comparisons](analysis/rq4/findings.json) |

Each analysis also produces JSON summaries. Per-handler RQ1/RQ3 results are in [by_handler.csv](analysis/by_handler.csv); RQ2 per-handler results and sample counts are in [analysis/rq2/](analysis/rq2/).

### Optional output locations and paper checks

All plotting scripts accept `--output-dir`. The RQ2 and RQ4 analyzers also accept this option; the RQ1/RQ3 analyzer writes to `analysis/`.

```bash
python plot_rq1.py --output-dir custom_figures
python analyze_rq2.py --output-dir custom_analysis/rq2
```

If you also have the paper's `experimentResults.tex`, the following checks compare the computed RQ2 execution table and RQ4 table/narrative values with that source. Replace `path/to/experimentResults.tex` with its location; paper source is not required for the quick start.

```bash
python analyze_rq2.py --paper-source path/to/experimentResults.tex
python analyze_rq4.py --paper-source path/to/experimentResults.tex
```

## Input files

| Experiment | Inputs read by the scripts | Additional data formats |
|---|---|---|
| RQ1/RQ3 | [RQ13_runs.json](RQ13_runs.json), [RQ13_analysis_manifest.json](RQ13_analysis_manifest.json); trace analysis also uses [RQ3_trace_counts.json](RQ3_trace_counts.json) | [RQ1 correctness workbook](RQ1_correctness_raw.xlsx), [RQ3 efficiency workbook](RQ3_efficiency_raw.xlsx) |
| RQ2 | [RQ2_design_artifacts.xlsx](RQ2_design_artifacts.xlsx), [RQ2_handlers.json](RQ2_handlers.json) | [RQ2_evaluation_records.json](RQ2_evaluation_records.json) |
| RQ4 | [RQ4_context_management.xlsx](RQ4_context_management.xlsx); validation also hashes [RQ4_evaluation_records.json](RQ4_evaluation_records.json) | The JSON contains the same evaluation records as the workbook |

The RQ1/RQ3 workbooks expose the same 750 runs, split by harness, with correctness and cost fields respectively. `uml2code` / `SGCA` denotes the CANVAS coding agent. RQ2 records identify the design artifact, model, handler, developer, and run. RQ4 records identify the strategy, model, handler, and run.

## Analysis conventions

A handler is identified by `(layer, eval_id)`. The benchmark contains seven `application` handlers and eight `domain` handlers; HandleClearingReceipt and SyncRiskTradeEvc belong to the application layer. `run_id` identifies an RQ1/RQ3 run. Where present, `sample_id` contains an interface name and should not be used alone to distinguish layers.

The evaluation budget is **50 agent LLM calls**. In RQ4, auxiliary summarization calls do not consume this budget, but their calls and tokens are included in reported costs.

SPR is the fraction of artifacts passing their complete test suite. Micro CPR
pools passed and expected test counts across analyzed runs. Macro CPR averages
the 15 handler-level CPRs equally.

RQ3 costs use **handler-macro means** over the same analyzed runs: for each
harness–model pair, first average the recorded cost within each `(layer,
eval_id)` handler, then average the 15 handler means with equal weights.
Thus, a handler with one analyzed run has the same weight as a handler with
five; single-run estimates have limited reliability (see the RQ1/RQ3 exclusions below). For a cost measure
`x`, the calculation is `sum(mean(x[h]) for h in handlers) / 15`.

In `analysis/summary.json` and `summary.csv`, `tokens_k`, `llm_calls`, and
`tool_calls` are these macro means. The `run_mean_*` fields report pooled
run-level means as supplementary results. `analysis/by_handler.csv` provides
the constituent handler means. The RQ3 figure uses the macro fields directly;
the sensitivity analysis uses the same aggregation with exclusions disabled.

The RQ3 trace table also uses handler-macro means, reproduced in
`analysis/rq3_trace_summary.json` / `.csv` and `rq3_trace_table_rows.tex`.
Protocol calls comprise `spec_fetch`, `todo_write`, and
`user_request_completed`. Specification/top-level reads count reads of
Markdown specifications and guidance, excluding the entity/repository
dependency file (`实体类和对应仓储类的依赖代码.md`). Edits count `search_replace`,
`Edit`, `Write`, and `MultiEdit`; compilations count tools whose names contain
`compile`. Total tool calls include actions outside these selected categories.
Trace totals and LLM call counts are checked against `RQ13_runs.json`.

An uncompilable or unevaluated artifact contributes zero passed cases over its
full expected test suite; a raw `ut_total=0` must not remove its denominator.
`expected_ut_total` supplies this denominator. Normalized analysis records keep
the original counts in `raw_ut_*`; the raw workbooks do not rewrite them.
CANVAS compilation status uses the independent test evaluator, since not
calling the agent's compile tool does not imply an uncompilable artifact.

## RQ1/RQ3: shared evaluation records

Each harness–model–handler configuration has five runs (`repeat=5`): five harnesses × two models × 15 handlers × five runs = **750 records**. Both RQ1 and RQ3 use the same analyzed runs.

### Infrastructure exclusions and diagnostics

The dataset contains 750 raw records. Eight records with confirmed infrastructure
failures are excluded from both correctness and cost analysis:

| Configuration | Excluded records | Evidence | Analyzed runs |
|---|---:|---|---:|
| OpenHands–Opus–ActivatePayScore (application) | 4 | Repeated 600-second API connection timeouts followed by the run timeout | 1 |
| Claude Code–Opus–HandleClearingReceipt | 4 | Final compilation blocked by a missing generated dependency in another project source file | 1 |

The remaining 148 configurations each have five analyzed runs: **742 runs in
total**. OpenHands–Opus and Claude Code–Opus each contribute 71 runs; the other
harness–model configurations each contribute 75. Results for the two
single-run configurations have limited reliability as estimates of repeated
execution. The RQ1 heatmap marks them with an asterisk.

`RQ13_analysis_manifest.json` records inclusion decisions and the supporting
log excerpts with anonymized internal file paths, source-log hashes, and event
indices. A build-environment failure does not
establish concurrency as its root cause.

Compilation or test failure, output truncation, and high token usage alone do
not justify exclusion. In particular, the six Claude Code–Sonnet output-limit
interruptions remain in the analysis. Runs whose compilation tool succeeded
but whose independent test build failed also remain unless the available
evidence establishes an infrastructure failure. Of the six output-limit
interruptions, one passes the complete test suite and five do not. The
diagnostic comparison in `analysis/output_truncation_diagnostic.json` removes
only those five from the diagnostic calculation: 64 of 70 runs pass, giving
91.4% SPR, 87.3% Micro CPR, and 93.1% Macro CPR. The main tables include all six.


`analysis/sensitivity_including_infrastructure_failures.json` reports results without infrastructure exclusions. `RQ3_trace_counts.json` links per-run action counts to `run_id` and source-trace SHA-256.

## RQ2: design-artifact comparison

The comparison uses Enhanced UML, Raw NL, and Spec-driven NL under the CANVAS coding agent. Enhanced UML has five runs per handler–model combination; each NL condition has two developer artifacts with five runs per artifact.

`analyze_rq2.py` writes overall and per-handler summaries, sample counts, run-level metrics, LaTeX table rows, and `validation.json` under `analysis/rq2/`. `plot_rq2.py` reads the same evaluation data and generates the per-handler figure.

### Samples and missing records

There are 150 Enhanced UML runs (five per handler–model), 293 Raw NL runs,
and 300 Spec-driven NL runs. Each NL condition targets five runs per developer
artifact and ten per handler–model. Available Raw NL records differ as follows:

| Model | Handler | Developer 1 | Developer 2 | Total |
|---|---|---:|---:|---:|
| Opus | QueryPayScoreHomeData | 5 | 4 | 9 |
| Sonnet | HandleClearingReceipt | 4 | 0 | 4 |

Other NL configurations have ten records. Analyze available records without
imputing missing runs or excluding additional records. Within each handler,
available runs receive equal weight; developer weights can consequently differ.
The sparse Sonnet–HandleClearingReceipt cell does not represent both developers.

### Metrics

RQ2 uses a budget of 50 agent LLM calls. Each evaluation record contributes its full
expected test denominator. CPR is computed from the integer passed and expected
test counts; costs are taken from the token and call fields in that record.

Micro CPR pools passed/expected test counts. Macro CPR, tokens, and LLM calls
first average available runs within each `(layer, eval_id)` handler, then
weight all 15 handlers equally. `RQ2_handlers.json` supplies the expected test
counts, plot labels, and cumulative cyclomatic complexities. Wilcoxon tests
pair the 15 handler means: Enhanced UML > NL for CPR, and NL > Enhanced UML
for tokens. The implementation uses exact sign permutations with midranks for
ties and drops zero differences; fractions avoid numerical tie/zero artifacts.
P-values are unadjusted for multiple comparisons.

## RQ4: context management

`RQ4_context_management.xlsx` contains 40 evaluation records: two strategies,
two models, two application-layer handlers, and five runs per configuration.
`RQ4_evaluation_records.json` provides the same records in JSON format.

RQ4 uses a budget of 50 agent LLM calls. Auxiliary summarization calls do not
count toward this budget; reported LLM calls and tokens include both agent and
summarization calls. Edit and compilation counts include failed tool attempts. CPR is computed from integer
passed/expected test counts, and SPR indicates whether the complete suite passes.

`analysis/rq4/summary.csv` and `.json` provide all eight configurations;
`table_rows.tex` provides the paper values; `findings.json` provides aggregate
CPR/SPR and cost ratios; `runs.json` provides the analyzed per-run data.
Aggregate quality equally weights the four model–handler configurations.
Cost ratios divide total costs across equally sized configurations.

Pruning/Summarization mean CPR is 0.931/0.806 and SPR is 65%/50%; Pruning uses
0.77 times the tokens and 0.59 times the total LLM calls. The main cost
reduction and correctness gains occur with Sonnet. Opus token costs remain
close and its correctness comparison remains mixed. These comparisons are
descriptive and do not establish an isolated causal effect.
