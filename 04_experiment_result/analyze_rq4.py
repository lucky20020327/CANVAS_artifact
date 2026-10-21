#!/usr/bin/env python3
"""Reproduce RQ4 from bundled evaluation records (no model calls)."""
import argparse
import csv
import hashlib
import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
MODELS = ['opus', 'sonnet']
TASKS = [('开通支付分', 'APS', 36), ('HandleClearingReceipt', 'Clear', 14)]
STRATEGIES = [('filter_context', 'P'), ('summarize', 'S')]
BUDGET = 50


def load_runs():
    book = load_workbook(HERE/'RQ4_context_management.xlsx', read_only=True, data_only=True)
    iterator = book['Context management'].iter_rows(values_only=True)
    headers = next(iterator)
    rows = [dict(zip(headers, row)) for row in iterator]
    book.close()
    cells = defaultdict(set)
    identities = set()
    for row in rows:
        assert row['layer'] == 'application'
        identity = (row['model'], row['eval_id'], row['strategy'], row['round'])
        assert identity not in identities
        identities.add(identity)
        cells[identity[:-1]].add(row['round'])
        expected = dict((name, n) for name, _, n in TASKS)[row['eval_id']]
        assert row['ut_total'] == expected and 0 <= row['ut_passed'] <= expected
        assert row['compile_success'] or row['ut_passed'] == 0
        assert 0 <= row['agent_calls'] <= BUDGET
        assert row['llm_calls'] == row['agent_calls'] + row['compression_calls']
        assert all(row[m] >= 0 for m in ['tokens', 'edit_calls', 'compile_calls', 'read_calls', 'filter_calls', 'compression_calls'])
        row['spr'] = int(row['compile_success'] and row['ut_passed'] == expected)
        row['cpr'] = row['ut_passed'] / expected
    assert len(rows) == 40 and len(cells) == 8 and all(v == set(range(1,6)) for v in cells.values())
    return rows


def aggregate(rows):
    result = []
    for model in MODELS:
        for name, label, _ in TASKS:
            for strategy, symbol in STRATEGIES:
                cell = [r for r in rows if (r['model'],r['eval_id'],r['strategy'])==(model,name,strategy)]
                result.append(dict(model=model, layer='application', eval_id=name, task=label,
                                   strategy=strategy, symbol=symbol, n_runs=len(cell),
                                   **{metric:statistics.mean(r[metric] for r in cell) for metric in
                                      ['spr','cpr','tokens','agent_calls','compression_calls','llm_calls','edit_calls','compile_calls']}))
    return result


def findings(summary):
    groups = {strategy:[r for r in summary if r['strategy']==strategy] for strategy,_ in STRATEGIES}
    overall = {s:{m:statistics.mean(r[m] for r in cell) for m in ['spr','cpr','tokens','llm_calls','agent_calls']} for s,cell in groups.items()}
    ratios = []
    for model in MODELS:
        for name, label, _ in TASKS:
            p,s = [r for r in summary if r['model']==model and r['eval_id']==name]
            ratios.append(dict(model=model, task=label, token_ratio=p['tokens']/s['tokens'],
                               llm_ratio=p['llm_calls']/s['llm_calls'], agent_ratio=p['agent_calls']/s['agent_calls']))
    return dict(overall=overall, ratios=ratios,
                token_ratio=overall['filter_context']['tokens']/overall['summarize']['tokens'],
                llm_ratio=overall['filter_context']['llm_calls']/overall['summarize']['llm_calls'])


def table_rows(summary):
    lines = []
    for r in summary:
        tok = f"{r['tokens']/1000:,.0f}".replace(',', '{,}')
        calls = r['llm_calls']
        lines.append(f"& {r['symbol']} & {r['spr']:.3f} & {r['cpr']:.3f} & {tok} & {calls:.1f} & {r['edit_calls']:.1f} & {r['compile_calls']:.1f} " + r'\\')
    return '\n'.join(lines)+'\n'


def check_paper(path, summary, facts):
    text = path.read_text().split(r'\subsection{RQ4:',1)[1]
    normalize = lambda s: re.sub(r'\s+','',s)
    missing = [line for line in table_rows(summary).splitlines() if normalize(line) not in normalize(text)]
    if missing:
        raise ValueError('RQ4 table mismatch:\n'+'\n'.join(missing))
    expected = [f"{facts['token_ratio']:.2f}"+r'$\times$ the aggregate tokens',
                f"{facts['llm_ratio']:.2f}"+r'$\times$ the LLM calls',
                f"{facts['overall']['filter_context']['cpr']:.3f} versus {facts['overall']['summarize']['cpr']:.3f} mean CPR",
                f"{facts['overall']['filter_context']['spr']:.0%}".replace('%',r'\%')+' versus '+f"{facts['overall']['summarize']['spr']:.0%}".replace('%',r'\%')+' mean SPR']
    for claim in expected:
        assert claim in text, 'RQ4 narrative mismatch: '+claim
    print('Paper check: all 48 RQ4 table values and aggregate narrative claims match.')


def save(out, stem, rows):
    (out/(stem+'.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n')
    if isinstance(rows,list) and rows:
        with (out/(stem+'.csv')).open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',type=Path,default=HERE/'analysis/rq4')
    parser.add_argument('--paper-source',type=Path)
    args=parser.parse_args();args.output_dir.mkdir(parents=True,exist_ok=True)
    rows=load_runs();summary=aggregate(rows);facts=findings(summary)
    for name,data in [('runs',rows),('summary',summary),('findings',facts)]:
        save(args.output_dir,name,data)
    (args.output_dir/'table_rows.tex').write_text(table_rows(summary))
    save(args.output_dir,'validation',dict(n_runs=len(rows),n_cells=len(summary),runs_per_cell=5,
         agent_call_budget=BUDGET,llm_cost_definition='agent calls plus compression calls within the agent budget',
         source_sha256={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in
                        ['RQ4_context_management.xlsx','RQ4_evaluation_records.json']},
         aggregation='Mean run CPR within cells; equal cell means across models and handlers. Cost ratios divide sums, not average ratios.'))
    print(table_rows(summary));print(json.dumps(facts,ensure_ascii=False,indent=2))
    if args.paper_source:check_paper(args.paper_source,summary,facts)


if __name__=='__main__':
    main()
