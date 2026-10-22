#!/usr/bin/env python3
"""Plot RQ3 execution cost for the same evaluated records as RQ1."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from analyze_results import load_paper_runs, summarize
HERE = Path(__file__).resolve().parent
FIG_DIR = HERE / "figures"
SYSTEM_ORDER = ["uml2code", "kilocode", "opencode", "openhands", "claudecode"]
MODEL_ORDER = ["claude-opus-4-6", "claude-sonnet-4-6"]
SYSTEM_LABEL = {"uml2code": "SGCA", "kilocode": "Kilo Code", "opencode": "OpenCode", "openhands": "OpenHands", "claudecode": "Claude Code"}

def setup_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif"],
        "font.size": 11,
    })


def fig_overall_efficiency(rows):
    setup_style()

    data = {(r["system"], r["model"]): (r["tokens_k"], r["llm_calls"])
            for r in summarize(rows)}

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.16, 2.8))

    x = np.arange(len(SYSTEM_ORDER))
    width = 0.32
    labels = ["SGCA", "Kilo", "OpenCode", "OpenHands", "Claude"]

    # Tokens
    opus_tok = [data[(s, "claude-opus-4-6")][0] for s in SYSTEM_ORDER]
    sonnet_tok = [data[(s, "claude-sonnet-4-6")][0] for s in SYSTEM_ORDER]
    bars1 = ax1.bar(x - width/2, opus_tok, width, label="Opus",
                    color="#3b82f6", edgecolor="white", linewidth=0.5)
    bars2 = ax1.bar(x + width/2, sonnet_tok, width, label="Sonnet",
                    color="#93c5fd", edgecolor="white", linewidth=0.5)
    for series, bars in enumerate([bars1, bars2]):
        for bar in bars:
            ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20 + series * max(opus_tok + sonnet_tok) * 0.06,
                     f"{bar.get_height():.0f}", ha="center", va="bottom",
                     fontsize=10)
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, fontsize=11, rotation=40, ha="right")
    ax1.set_ylabel("Tokens (K)", fontsize=11)
    ax1.set_title("Token Consumption", fontsize=12, fontweight="bold")
    ax1.legend(fontsize=10, frameon=False, loc="upper left")
    ax1.set_ylim(0, max(opus_tok + sonnet_tok) * 1.25)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)

    # LLM Calls
    opus_calls = [data[(s, "claude-opus-4-6")][1] for s in SYSTEM_ORDER]
    sonnet_calls = [data[(s, "claude-sonnet-4-6")][1] for s in SYSTEM_ORDER]
    bars3 = ax2.bar(x - width/2, opus_calls, width, label="Opus",
                    color="#f97316", edgecolor="white", linewidth=0.5)
    bars4 = ax2.bar(x + width/2, sonnet_calls, width, label="Sonnet",
                    color="#fdba74", edgecolor="white", linewidth=0.5)
    for series, bars in enumerate([bars3, bars4]):
        for bar in bars:
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3 + series * 1.7,
                     f"{bar.get_height():.1f}", ha="center", va="bottom",
                     fontsize=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, fontsize=11, rotation=40, ha="right")
    ax2.set_ylabel("LLM Calls", fontsize=11)
    ax2.set_title("LLM Call Count", fontsize=12, fontweight="bold")
    ax2.legend(fontsize=10, frameon=False, loc="upper left")
    ax2.set_ylim(0, max(opus_calls + sonnet_calls) * 1.30)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)

    fig.subplots_adjust(wspace=0.42, bottom=0.30, top=0.86)
    out = FIG_DIR / "rq3_efficiency_overall.pdf"
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
    rows = load_paper_runs()
    fig_overall_efficiency(rows)
