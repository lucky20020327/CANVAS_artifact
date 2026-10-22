#!/usr/bin/env python3
"""Generate RQ1 figure: side-by-side CPR and SPR heatmaps for all runs."""

import csv
from pathlib import Path
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec
import numpy as np

HERE = Path(__file__).resolve().parent
FIG_DIR = HERE / "figures"
FIG_DIR.mkdir(parents=True, exist_ok=True)

SYSTEM_ORDER = ["uml2code", "kilocode", "opencode", "openhands", "claudecode"]
SYSTEM_LABEL = {
    "uml2code": "SGCA",
    "kilocode": "Kilo Code",
    "opencode": "OpenCode",
    "openhands": "OpenHands",
    "claudecode": "Claude Code",
}
MODEL_ORDER = ["claude-opus-4-6", "claude-sonnet-4-6"]
MODEL_LABEL = {"claude-opus-4-6": "Opus", "claude-sonnet-4-6": "Sonnet"}

EXCLUDED_EVAL = "查询用户服务授权记录的统计数据"
EXCLUDED_DOMAIN_EVAL = "开通支付分"

HANDLER_SHORT = {
    "开通支付分": "ActivatePayScore",
    "更新已了解分数提示标记": "UpdateScoreHint",
    "查询支付分首页数据": "QueryPayScoreHomeData",
    "登陆支付分小程序": "LoginMiniApp",
    "记录用户后续需要提醒的信息": "RecordUserReminder_app",
    "HandleClearingReceipt": "HandleClearingReceipt",
    "SyncRiskTradeEvc": "SyncRiskTradeEvc",
    "查询支付分账户信息": "QueryAccount",
    "查询用户相关配置": "QueryUserConfig",
    "查询用户订单的统计数据": "QueryOrderStats",
    "查询非居民身份证实名身份可通过支付密码核身的资格": "VerifyNonResID",
    "记录用户需后续提醒的信息": "RecordUserReminder_dom",
    "验证用户是否可以开通微信支付分": "VerifyCanActivate",
    "验证用户是否已经开通微信支付分": "VerifyIsActivated",
}

HANDLER_LAYER_LABELS = {
    ("application", "更新已了解分数提示标记"): "UpdateScoreHint_app",
    ("domain", "更新已了解分数提示标记"): "UpdateScoreHint_dom",
}

# Cumulative cyclomatic complexity (ΣCC) from ground-truth handlers in
# dataset/code/dataset.csv.  Tuple key disambiguates handlers that share an
# eval_id across application and domain layers.
HANDLER_SUM_CC = {
    ("application", "开通支付分"): 78,
    ("application", "HandleClearingReceipt"): 29,
    ("application", "SyncRiskTradeEvc"): 50,
    ("application", "查询支付分首页数据"): 15,
    ("application", "更新已了解分数提示标记"): 11,
    ("application", "记录用户后续需要提醒的信息"): 10,
    ("application", "登陆支付分小程序"): 9,
    ("domain", "查询非居民身份证实名身份可通过支付密码核身的资格"): 5,
    ("domain", "查询支付分账户信息"): 10,
    ("domain", "记录用户需后续提醒的信息"): 9,
    ("domain", "更新已了解分数提示标记"): 8,
    ("domain", "验证用户是否已经开通微信支付分"): 7,
    ("domain", "验证用户是否可以开通微信支付分"): 25,
    ("domain", "查询用户相关配置"): 28,
    ("domain", "查询用户订单的统计数据"): 6,
}


def handler_sort_key(layer_eid):
    layer, eid = layer_eid
    return (-HANDLER_SUM_CC.get((layer, eid), 0), layer, eid)

def load_data():
    """Use the same frozen, measured cohort as the RQ1 table and RQ3."""
    from analyze_results import load_paper_runs
    return load_paper_runs()


def merge_layer(layer):
    if layer == "application":
        return "application"
    return layer


def build_matrices(rows):
    groups = defaultdict(list)
    for r in rows:
        groups[
            (r["system"], r["model"], merge_layer(r["layer"]), r["eval_id"])
        ].append(r)

    handler_set = set()
    for r in rows:
        handler_set.add((merge_layer(r["layer"]), r["eval_id"]))

    handler_list = sorted(handler_set, key=handler_sort_key)

    configs = [(sys, mdl) for sys in SYSTEM_ORDER for mdl in MODEL_ORDER]
    n_h = len(handler_list)
    n_c = len(configs)

    cpr = np.full((n_h, n_c), np.nan)
    spr = np.full((n_h, n_c), np.nan)
    sample_counts = np.zeros((n_h, n_c), dtype=int)

    for hi, (layer, eid) in enumerate(handler_list):
        for ci, (sys, mdl) in enumerate(configs):
            runs = groups.get((sys, mdl, layer, eid), [])
            if runs:
                n = len(runs)
                sample_counts[hi, ci] = n
                tp = sum(int(r["ut_passed"]) for r in runs)
                tt = sum(int(r["ut_total"]) for r in runs)
                cpr[hi, ci] = tp / tt * 100 if tt > 0 else 0
                spr[hi, ci] = (
                    sum(1 for r in runs if r["ut_status"] == "success")
                    / n
                    * 100
                )

    return handler_list, configs, cpr, spr, sample_counts


def draw_heatmap(
    ax,
    matrix,
    title,
    handler_list,
    configs,
    show_ylabels,
    sample_counts,
):
    """Draw one heatmap panel (CPR or SPR)."""
    colors = [
        (0.00, "#b2182b"),
        (0.35, "#ef8a62"),
        (0.55, "#fddbc7"),
        (0.72, "#f6e8a3"),
        (0.84, "#d9ef8b"),
        (0.92, "#91cf60"),
        (0.97, "#1a9850"),
        (1.00, "#006837"),
    ]
    cmap = mcolors.LinearSegmentedColormap.from_list("quality", colors, N=256)
    norm = mcolors.Normalize(vmin=0, vmax=100)

    n_h, n_c = matrix.shape
    im = ax.imshow(
        matrix, aspect="auto", cmap=cmap, norm=norm, interpolation="nearest"
    )

    ax.set_xticks(range(n_c))
    bottom_labels = []
    for _, m in configs:
        bottom_labels.append("O" if m == "claude-opus-4-6" else "S")
    ax.set_xticklabels(bottom_labels, fontsize=8)
    ax.xaxis.set_ticks_position("top")
    ax.xaxis.set_label_position("top")
    ax.tick_params(axis="x", length=0, pad=1)

    for si, sys in enumerate(SYSTEM_ORDER):
        center = si * 2 + 0.5
        ax.text(
            center,
            -0.03,
            {"uml2code": "SGCA", "kilocode": "Kilo\nCode", "opencode": "Open\nCode", "openhands": "Open\nHands", "claudecode": "Claude\nCode"}[sys],
            ha="center",
            va="top",
            fontsize=7.5,
            fontweight="bold",
            rotation=0,
            transform=ax.get_xaxis_transform(),
        )

    ax.text(
        0.5,
        1.14,
        title,
        ha="center",
        va="bottom",
        fontsize=9,
        fontweight="bold",
        transform=ax.transAxes,
    )

    for si in range(1, len(SYSTEM_ORDER)):
        ax.axvline(x=si * 2 - 0.5, color="#94a3b8", linewidth=0.6)

    if show_ylabels:
        y_labels = [
            f"{HANDLER_LAYER_LABELS.get((layer, eid), HANDLER_SHORT.get(eid, eid[:14]))} "
            f"({HANDLER_SUM_CC.get((layer, eid), '?')})"
            for layer, eid in handler_list
        ]
        ax.set_yticks(range(n_h))
        ax.set_yticklabels(y_labels, fontsize=7.5)
        ax.set_ylabel(r"Handler ($\Sigma$CC)", fontsize=8)
    else:
        ax.set_yticks([])

    for hi in range(n_h):
        for ci in range(n_c):
            val = matrix[hi, ci]
            if np.isnan(val):
                continue
            fw = "bold" if val < 80 else "normal"
            if val >= 99.5:
                label = "100"
            else:
                label = f"{val:.0f}"
            if sample_counts[hi, ci] < 5:
                label += "*"
            ax.text(
                ci,
                hi,
                label,
                ha="center",
                va="center",
                fontsize=7,
                color="#111827",
                fontweight=fw,
            )

    return im


def fig_dual_heatmap(rows):
    handler_list, configs, cpr, spr, sample_counts = build_matrices(rows)

    plt.rcParams.update(
        {
            "font.family": "serif",
            "font.serif": ["Times New Roman", "DejaVu Serif"],
            "font.size": 7,
        }
    )

    fig = plt.figure(figsize=(7.16, 3.8))
    gs = GridSpec(1, 3, figure=fig, width_ratios=[1, 1, 0.05], wspace=0.08)

    ax_cpr = fig.add_subplot(gs[0, 0])
    ax_spr = fig.add_subplot(gs[0, 1])
    ax_cb = fig.add_subplot(gs[0, 2])

    im_cpr = draw_heatmap(
        ax_cpr,
        cpr,
        "Case Pass Rate (CPR)",
        handler_list,
        configs,
        show_ylabels=True,
        sample_counts=sample_counts,
    )
    im_spr = draw_heatmap(
        ax_spr,
        spr,
        "Suite Pass Rate (SPR)",
        handler_list,
        configs,
        show_ylabels=False,
        sample_counts=sample_counts,
    )

    cb = fig.colorbar(im_cpr, cax=ax_cb)
    cb.set_label("Pass Rate (%)", fontsize=8)
    cb.set_ticks([0, 50, 80, 90, 95, 100])
    cb.ax.tick_params(labelsize=7.5)

    fig.subplots_adjust(top=0.82, bottom=0.03, left=0.22, right=0.94)
    out = FIG_DIR / "rq1_cpr_heatmap.pdf"
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
    rows = load_data()
    print(f"Loaded {len(rows)} runs")
    fig_dual_heatmap(rows)
    print("Done.")
