"""Audit the published evidence offline or classify preapproved research requests."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile

from bioguard import core, judge

ROOT = Path(__file__).resolve().parent
DATA = ROOT / 'data'
RECORDS = ROOT / 'results' / 'records'
METHODS = ('unprompted', 'none', 'boundary', 'fusion', 'low_relevance')


def cases_by_id():
    return {row['id']: row for row in core.read_jsonl(DATA / 'requests.jsonl')}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def verify():
    manifest = core.read_json(ROOT / 'results' / 'checksums.json')
    for name, digest in manifest.items():
        require(core.hash_file(ROOT / name) == digest, f'File changed: {name}')
    cases = cases_by_id()
    groups = core.read_json(DATA / 'groups.json')
    original_ids = {r['original_id']: r['id'] for r in cases.values()}
    approvals = core.ApprovedInputs()
    for case in cases.values():
        approvals.message(case)
    counts = Counter()
    for row in core.read_jsonl(RECORDS / 'model-only/decisions.jsonl'):
        case = cases[row['id']]
        counts[case['expected'], row.get('decision', row['status'])] += 1
    correct = sum(counts[a,a] for a in core.ACTIONS)
    baseline = core.read_jsonl(RECORDS / 'model-only/decisions.jsonl')
    require(len(baseline) == len(cases) == len({r['id'] for r in baseline}), 'Incomplete model-only coverage')
    require({r['id'] for r in baseline} == set(cases), 'Unexpected model-only IDs')
    print(f'无项目政策  {correct}/{len(cases)}  误拦 {counts["allow","restrict"]}  多余澄清 {counts["allow","clarify"]}  受限漏放 {counts["restrict","allow"]}')
    key_group = set(groups['evidence-comparison'])
    evidence = core.read_jsonl(RECORDS / 'evidence-comparison/decisions.jsonl')
    indexed = {(original_ids[r['id']], r['method']): r for r in evidence}
    require(len(indexed) == len(evidence) and set(indexed) == {(cid, m) for cid in key_group for m in METHODS[1:]}, 'Missing or duplicate comparison rows')
    for method in METHODS:
        hits = citations = successes = 0
        for cid in key_group:
            if method == 'unprompted':
                row = next(r for r in baseline if r['id'] == cid)
            else:
                row = indexed[cid, method]
            ref = set(cases[cid]['relevant_cards'])
            successes += row['status'] == 'ok' and row.get('decision') == cases[cid]['expected']
            hits += bool(ref.intersection(r['id'] for r in row.get('retrieved', [])[:3]))
            citations += bool(ref.intersection(row.get('evidence_ids', [])))
        print(f'{method:14}  动作 {successes}/{len(key_group)}  检索命中 {hits}  引用命中 {citations}')
    ledgers = list(RECORDS.glob('*/decisions.jsonl'))
    print(f'已验证 {len(manifest)} 份文件，涵盖 {sum(len(core.read_jsonl(p)) for p in ledgers)} 行调用记录。')


def run(group, methods):
    cases = cases_by_id()
    selected = list(cases) if group == 'all' else core.read_json(DATA / 'groups.json')[group]
    policy = core.read_json(ROOT / 'policy/knowledge.json')
    retriever = None
    if any(m not in ('unprompted', 'none') for m in methods):
        from bioguard.retrieval import EvidenceRetriever
        retriever = EvidenceRetriever(policy['cards'])
    registry = core.ApprovedInputs()
    for cid in selected:
        registry.message(cases[cid])
    client = core.DeepSeek(core.acquire_key(), registry)
    parent = ROOT / 'local-runs'
    parent.mkdir(exist_ok=True)
    out = Path(tempfile.mkdtemp(prefix=group + '-', dir=parent))
    settings = dict(group=group, methods=methods, model=core.MODEL, endpoint=core.ENDPOINT,
                    temperature=0, data_sha256=core.hash_file(DATA/'requests.jsonl'),
                    policy_sha256=core.hash_file(ROOT/'policy/knowledge.json'))
    (out/'settings.json').write_text(json.dumps(settings, indent=2), encoding='utf8')
    print(f'结果目录 {out}', flush=True)
    scores = Counter()
    with (out/'decisions.jsonl').open('x', encoding='utf8') as stream:
        for i, cid in enumerate(selected):
            case = cases[cid]
            for method in methods[i % len(methods):] + methods[:i % len(methods)]:
                ranked = [] if method in ('unprompted','none') else retriever.rank(case['input'], method)
                prompt = judge.MODEL_ONLY_PROMPT if method == 'unprompted' else judge.context(policy, ranked)
                raw = client.classify(case, prompt)
                verdict = judge.parse_model_only(raw) if method == 'unprompted' else judge.parse_policy(raw, policy, ranked)
                row = dict(id=cid, method=method, retrieved=ranked, utc=datetime.now(timezone.utc).isoformat(), **verdict)
                stream.write(json.dumps(row, ensure_ascii=False) + '\n')
                stream.flush()
                if row['status'] == 'api_failure':
                    raise SystemExit('接口连接失败，已保留已完成记录。')
                scores[method] += verdict.get('decision') == case['expected'] and verdict['status'] == 'ok'
    for method in methods:
        print(f'{method}  {scores[method]}/{len(selected)}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('verify', help='Verify saved results without an API credential')
    live = sub.add_parser('run', help='Make new, billable API calls')
    live.add_argument('--group', required=True, choices=['all', *core.read_json(DATA/'groups.json')])
    live.add_argument('--method', nargs='+', choices=METHODS, required=True)
    args = parser.parse_args()
    if args.command == 'verify':
        verify()
    else:
        run(args.group, list(dict.fromkeys(args.method)))
