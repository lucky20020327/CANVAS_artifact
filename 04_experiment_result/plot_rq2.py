#!/usr/bin/env python3
"""Reproduce the RQ2 per-handler figure from the bundled evaluation workbook."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from analyze_rq2 import load_runs, aggregate, handlers, MODELS

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE / "figures"
MODEL_ORDER = MODELS
MODEL_SHORT = {MODELS[0]: "Opus", MODELS[1]: "Sonnet"}
ARM_ORDER = ["Enhanced UML", "Raw NL", "Spec-driven NL"]
ARM_LABEL = {a: a for a in ARM_ORDER}
ARM_COLORS = {"Enhanced UML": "#2563eb", "Raw NL": "#d97706", "Spec-driven NL": "#dc2626"}
HANDLER_SUM_CC = {(h["eval_id"], h["layer"]): h["sum_cc"] for h in handlers()}
HANDLER_LAYER_LABELS = {(h["eval_id"], h["layer"]): h["label"] for h in handlers()}
HANDLER_SHORT = {h["eval_id"]: h["label"] for h in handlers()}


def aggregate_by_handler(rows, model):
    return {(r["eval_id"], r["layer"]): r for r in rows if r["model"] == model}

def setup_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 8,
    })

def fig_per_handler_cpr(all_rows):
    setup_style()

    handlers_sorted = sorted(HANDLER_SUM_CC.keys(),
                             key=lambda h: -HANDLER_SUM_CC[h])

    fig, axes = plt.subplots(2, 2, figsize=(7.16, 4.8),
                             sharex=True, sharey="col")
    x_positions = np.arange(len(handlers_sorted))
    x_labels = [f"{HANDLER_LAYER_LABELS.get(h, HANDLER_SHORT[h[0]])} ({HANDLER_SUM_CC[h]})"
                for h in handlers_sorted]

    markers = {"Enhanced UML": "o", "Raw NL": "s", "Spec-driven NL": "D"}

    for row_index, model in enumerate(MODEL_ORDER):
        ax_cpr, ax_tok = axes[row_index]
        for arm in ARM_ORDER:
            arm_rows = [r for r in all_rows if r["arm"] == arm]
            agg = aggregate_by_handler(arm_rows, model)
            missing = set(handlers_sorted) - agg.keys()
            if missing:
                raise ValueError(
                    f"Missing {MODEL_SHORT[model]} results for {arm}: {sorted(missing)}"
                )

            cprs = [agg[h]["cpr"] * 100 for h in handlers_sorted]
            toks = [agg[h]["tokens_k"] for h in handlers_sorted]

            for ax, vals in [(ax_cpr, cprs), (ax_tok, toks)]:
                ax.plot(x_positions, vals, color=ARM_COLORS[arm],
                        marker=markers[arm], markersize=4.5, linewidth=1.3,
                        label=ARM_LABEL[arm],
                        markeredgecolor="white", markeredgewidth=0.4)

        ax_cpr.set_ylabel("Case Pass Rate (%)", fontsize=8)
        ax_cpr.set_ylim(-5, 108)
        ax_cpr.set_title(
            f"({chr(97 + 2 * row_index)}) {MODEL_SHORT[model]}: Functional Correctness",
            fontsize=8.5, fontweight="bold",
        )
        ax_tok.set_ylabel("Avg Tokens (K)", fontsize=8)
        ax_tok.set_title(
            f"({chr(98 + 2 * row_index)}) {MODEL_SHORT[model]}: Token Consumption",
            fontsize=8.5, fontweight="bold",
        )

    axes[0, 1].set_ylim(bottom=0)
    for ax in axes.flat:
        ax.set_xticks(x_positions)
        ax.set_xticklabels(x_labels, fontsize=6, rotation=60, ha="right")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="y", alpha=0.3, linewidth=0.5)
    for ax in axes[-1]:
        ax.set_xlabel(r"Handler ($\Sigma$CC)", fontsize=7.5)

    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="upper center", ncol=3,
               fontsize=8, frameon=False)
    fig.subplots_adjust(top=0.88, bottom=0.19, wspace=0.32, hspace=0.35)
    out = FIG_DIR / "rq2_per_handler_cpr.pdf"
    fig.savefig(out, bbox_inches="tight", dpi=300)
    print(f"Wrote {out}")
    plt.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=FIG_DIR)
    args = parser.parse_args()
    FIG_DIR = args.output_dir
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    _, by_handler = aggregate(load_runs())
    fig_per_handler_cpr(by_handler)
