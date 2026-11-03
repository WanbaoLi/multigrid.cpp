#!/usr/bin/env python3
"""Read an optimization ledger and write reviewable experience outside it.

No history receipt, checkpoint, report or best pointer in the ledger is changed.
Unregistered/diagnostic reports are evidence only, never completed ranked runs.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
import campaign as ledger

FAILURES = {'failed','timeout','cleanup_failed'}
RANKABLE_STATES = {'measured','best','inconclusive'}


def metadata_files(root):
    return sorted([*root.glob('campaign.json'), *root.glob('best.json'),
                   *root.glob('attempts/*/attempt.json'), *root.glob('events/*.json'),
                   *root.glob('best-history/*.json')])


def fingerprint(paths):
    return {str(path):ledger.digest(path) for path in paths}


def evidence_files(path):
    result = []
    for directory, directories, files in os.walk(path):
        directories[:] = [d for d in directories if d not in {'source','build','artifacts','.git','__pycache__'}]
        for name in sorted(files):
            target = Path(directory)/name
            if target.is_symlink():
                continue
            result.append(target)
    return sorted(result)


def report_view(report):
    return {key:report.get(key) for key in [
        'complete','measurements_complete','timing_scope','zero_initial_guess',
        'input_sha256','source_manifest_sha256','library_sha256','library_path',
        'comparison_key','configuration','setup_seconds','samples','verification']}


def collect(campaign_root, verify_artifacts=False):
    root = Path(campaign_root).resolve()
    before = fingerprint(metadata_files(root))
    reads, errors = {}, []
    def reject_constant(value):
        raise ValueError(f'Nonfinite JSON number: {value}')
    def read(path):
        raw = path.read_bytes()
        reads[str(path)] = hashlib.sha256(raw).hexdigest()
        return json.loads(raw.decode('utf-8'),parse_constant=reject_constant)
    config = read(root/'campaign.json')
    events = []
    for path in sorted((root/'events').glob('*.json')):
        try:
            events.append(dict(path=str(path),record=read(path)))
        except (OSError,ValueError) as exc:
            errors.append(dict(path=str(path),error=str(exc)))
    accepted_ids = {row['record'].get('attempt') for row in events
                    if row['record'].get('kind') in ('promote','rollback')}
    best = read(root/'best.json') if (root/'best.json').exists() else None
    best_history = []
    for path in sorted((root/'best-history').glob('*.json')):
        try:
            best_history.append(dict(path=str(path),record=read(path)))
        except (OSError,ValueError) as exc:
            errors.append(dict(path=str(path),error=str(exc)))
    attempts = []
    for path in sorted((root/'attempts').glob('*')):
        if not path.is_dir():
            continue
        row = dict(id=path.name,path=str(path),status='unreadable',complete_full12=False,
                   rank_eligible=False,exclusion_reasons=[],errors=[])
        attempts.append(row)
        try:
            data = read(path/'attempt.json')
        except (OSError,ValueError) as exc:
            row['errors'].append(str(exc))
            row['unresolved'] = True
            continue
        row.update(status=data.get('status','unknown'),created=data.get('created'),
                   proposal=data.get('proposal',{}),conclusions=data.get('conclusions',[]),
                   stages=data.get('stages',{}),snapshot=data.get('snapshot',{}),
                   registered_report=data.get('report'),accepted_in_history=path.name in accepted_ids,
                   current_best=bool(best and best.get('attempt') == path.name))
        row['unresolved'] = not row['conclusions'] and not row['accepted_in_history']
        row['current_failure'] = row['status'] in FAILURES or any(
            stage.get('status') in FAILURES for stage in row['stages'].values())
        row['blocked'] = row['status'] == 'blocked'
        row['interrupted'] = row['status'] == 'interrupted' or any(
            stage.get('status') == 'interrupted' for stage in row['stages'].values())
        row['running_checkpoint'] = any(stage.get('status') == 'running' for stage in row['stages'].values())
        files = evidence_files(path)
        row['log_paths'] = [str(p) for p in files if p.suffix == '.log']
        row['profile_paths'] = [str(p) for p in files
            if any(word in p.name.lower() for word in ['profile','perf','runtime'])]
        for stage in row['stages'].values():
            argv=stage.get('argv',[])
            for flag in ['--profile-output','--profile-directory']:
                if flag in argv and argv.index(flag)+1 < len(argv):
                    row['profile_paths'].append(argv[argv.index(flag)+1])
        row['conclusion_evidence'] = [link for c in row['conclusions'] for link in c.get('evidence',[])]
        row['unregistered_measurements'] = []
        row['raw_measurement_reports'] = []
        registered_path = path/'report.json'
        for report_path in [p for p in files if p.name == 'result.json']:
            try:
                report = read(report_path)
                raw=dict(path=str(report_path),
                    diagnostic=report.get('timing_scope') != 'full12_api',
                    complete=report.get('complete') is True,
                    measurements_complete=report.get('measurements_complete') is True,
                    counted_as_completed=False,rank_eligible=False,report=report_view(report),
                    matches_ingested_report=bool(data.get('report') and
                        ledger.object_digest(report)==data['report']['sha256']))
                row['raw_measurement_reports'].append(raw)
                if not raw['matches_ingested_report']:
                    row['unregistered_measurements'].append(raw)
            except (OSError,ValueError) as exc:
                row['errors'].append(f'{report_path}: {exc}')
        if not data.get('report'):
            row['exclusion_reasons'].append('No report was ingested into this attempt')
            continue
        try:
            report = read(registered_path)
            row['report_path'] = str(registered_path)
            row['report'] = report_view(report)
            if ledger.object_digest(report) != data['report']['sha256']:
                raise ledger.EvidenceError('Ingested report digest changed')
            summary = ledger.validate_report(report,config,data['snapshot']['source_manifest_sha256'])
            if data['report'].get('library_sha256') != report['library_sha256']:
                raise ledger.EvidenceError('Ingested library identity differs from report')
            if verify_artifacts:
                ledger.checked_attempt(root,path.name,config)
                row['artifact_check'] = 'source/archive/library hashes verified'
            else:
                row['artifact_check'] = 'not rehashed; ledger report identity and full12 numerical contract checked'
            row.update(complete_full12=True,performance=summary)
            if summary['relative_spread'] > config['maximum_relative_spread']:
                row['exclusion_reasons'].append('Sample spread exceeds campaign threshold')
            if row['status'] not in RANKABLE_STATES or row['current_failure']:
                row['exclusion_reasons'].append('Current attempt/stage status is not eligible for ranking')
            row['rank_eligible'] = not row['exclusion_reasons']
        except (OSError,ValueError,KeyError,TypeError,ledger.EvidenceError) as exc:
            row['errors'].append(str(exc))
            row['evidence_failure'] = True
            row['exclusion_reasons'].append('Ingested report or evidence contract failed')
    after = fingerprint(metadata_files(root))
    changed_reads = [path for path,sha in reads.items() if not Path(path).is_file() or ledger.digest(path) != sha]
    consistent = before == after and not changed_reads
    if not consistent:
        for row in attempts:
            row['rank_eligible'] = False
            row['exclusion_reasons'].append('Ledger changed during summary read; regenerate before comparison')
    groups = {}
    for row in attempts:
        if not row['rank_eligible']:
            continue
        key = ledger.object_digest(row['report']['comparison_key'])
        group = groups.setdefault(key,dict(comparison_key=row['report']['comparison_key'],rows=[]))
        group['rows'].append(dict(attempt=row['id'],median_seconds=row['performance']['median_seconds'],
            relative_spread=row['performance']['relative_spread'],
            steady_samples=row['performance']['steady_samples'],
            configuration=row['report']['configuration'],current_best=row.get('current_best',False)))
    for group in groups.values():
        group['rows'].sort(key=lambda item:(item['median_seconds'],item['attempt']))
    statuses = Counter(row['status'] for row in attempts)
    counts = dict(attempts_total=len(attempts),ingested_complete_full12=sum(r['complete_full12'] for r in attempts),
        rank_eligible=sum(r['rank_eligible'] for r in attempts),
        failed=sum(r.get('current_failure',False) or r.get('evidence_failure',False) for r in attempts),
        evidence_failures=sum(r.get('evidence_failure',False) for r in attempts),
        blocked=sum(r.get('blocked',False) for r in attempts),
        interrupted=sum(r.get('interrupted',False) for r in attempts),
        running_checkpoints=sum(r.get('running_checkpoint',False) for r in attempts),
        unresolved=sum(r.get('unresolved',False) for r in attempts),
        evidence_errors=len(errors)+sum(len(r['errors']) for r in attempts),statuses=dict(statuses))
    best_valid=bool(consistent and best and any(r['id']==best.get('attempt') and r['complete_full12']
                               and not r.get('current_failure') for r in attempts))
    return dict(schema=1,generated_at=ledger.now(),campaign=str(root),objective=config['objective'],
        campaign_contract={k:config.get(k) for k in ['baseline_commit','input_sha256','reference_sha256',
            'residual_limit','solution_relative_error_limit','minimum_gain','maximum_relative_spread',
            'minimum_steady_samples','reference_skill','reference_manifest']},
        read_consistent=consistent,ledger_metadata_sha256=ledger.object_digest(before),
        ledger_files_read_sha256=reads,changed_files_during_read=changed_reads,
        artifact_verification_requested=verify_artifacts,counts=counts,attempts=attempts,
        unresolved_attempts=[r['id'] for r in attempts if r.get('unresolved',False)],
        best=best,best_report_contract_valid=best_valid,best_history=best_history,
        best_events=[r for r in events if r['record'].get('kind') in ('promote','rollback')],
        events=events,comparable_groups=groups,errors=errors,
        interpretation='Rankings are observed medians within identical comparison keys, not promotions or cross-node hardware claims; unresolved controls need explicit conclusions')


def inline(value):
    return str(value).replace('|','\\|').replace('\n',' ')


def link(path,label=None):
    return f'[{label or Path(path).name}](<{str(path).replace(chr(92),"/")}>)'


def render_markdown(summary):
    counts=summary['counts']
    lines=['# 可写优化经验汇总','',
        f"生成时间：{summary['generated_at']}。本文件可补充分析，重新生成会覆盖；正式结论仍用账本 `conclude` 记录。",'',
        f"账本：`{summary['campaign']}`；目标：完整 12 列传播子公共 API 墙时；读取一致：{summary['read_consistent']}。",'',
        f"共 {counts['attempts_total']} 轮；完整已导入报告 {counts['ingested_complete_full12']}；可比较 {counts['rank_eligible']}；"
        f"当前失败 {counts['failed']}；blocked {counts['blocked']}；中断 {counts['interrupted']}；"
        f"running 检查点 {counts['running_checkpoints']}；未结论 {counts['unresolved']}。",'',
        'running 仅指记录状态，本工具不探测进程是否仍存活。局部算子、未 ingest、diagnostic、精度未通过和缺失报告不算完成或排名。',
        '默认复核报告身份与完整数值契约；`--verify-artifacts` 额外重算冻结源码、归档和库摘要。', '',
        '## 当前最佳与回滚历史','']
    if summary['best']:
        best=summary['best']
        lines += [f"账本指针：**{best['attempt']}**，保存的中位数 {best.get('median_seconds')} 秒。该指针不会因本汇总的排序而改变。",'']
        if not summary['best_report_contract_valid']:
            lines += ['**该指针未通过本次完整报告契约检查，请检查证据；不能据此宣称当前最佳版仍正确。**','']
    else:
        lines += ['尚无已接受最佳版本。','']
    for entry in summary['best_events']:
        event=entry['record']
        lines.append(f"- {event.get('time')}：{event['kind']} → {event.get('attempt')}；控制 {event.get('against')}；原因 {inline(event.get('reason',''))}；{link(entry['path'],'事件证据')}")
    lines += ['', '## 下轮先处理的未结论轮次','']
    if not summary['unresolved_attempts']:
        lines += ['没有缺少结论的轮次。','']
    else:
        for row in summary['attempts']:
            if row.get('unresolved'):
                lines.append(f"- **{row['id']}**：{row['status']}；完整已导入={row['complete_full12']}；"
                             f"{link(str(Path(row['path'])/'attempt.json'),'检查点')}；下一步检查日志并记录结论。")
        lines.append('')
    lines += ['## 同一比较键内的完整求解测量','',
              '以下是测量中位数排序，不是自动晋升；不同组禁止直接排名。噪声超过门槛的组内样本也不进入此表。','']
    for key,group in summary['comparable_groups'].items():
        lines += [f'比较组 `{key[:12]}`：`{json.dumps(group["comparison_key"],ensure_ascii=False)}`','',
            '| 轮次 | 稳态中位数/秒 | 稳态全部样本/秒 | 相对极差 | 配置 |',
            '|---|---:|---|---:|---|']
        for row in group['rows']:
            lines.append(f"| {row['attempt']} | {row['median_seconds']:.6f} | {', '.join(f'{v:.6f}' for v in row['steady_samples'])} | "
                         f"{row['relative_spread']:.2%} | {inline(json.dumps(row['configuration'],ensure_ascii=False))} |")
        lines.append('')
    if not summary['comparable_groups']:
        lines += ['当前没有可排名的完整测量。','']
    lines += ['## 每轮假设、证据和结论','']
    for row in summary['attempts']:
        proposal=row.get('proposal',{})
        lines += [f"### {row['id']} — {row['status']}",'',
            f"问题：{proposal.get('bottleneck','未记录')}。假设：{proposal.get('hypothesis','未记录')}。",'',
            f"改动：{proposal.get('change','未记录')}。机制：{proposal.get('mechanism','未记录')}。",'',
            f"重试条件：{proposal.get('retry_conditions','未记录')}；前轮：{proposal.get('retry_of','无')}。",'']
        report=row.get('report')
        if report:
            validation=report.get('verification') or {}
            lines += [f"完整已导入={row['complete_full12']}；可排名={row['rank_eligible']}；"
                f"独立验证列数={validation.get('columns')}；最大真实残差={validation.get('max_true_residual')}；"
                f"参考解误差={validation.get('solution_relative_error','未提供')}。",'',
                f"源码 SHA256：`{report.get('source_manifest_sha256')}`；库 SHA256：`{report.get('library_sha256')}`。",'',
                f"配置：`{json.dumps(report.get('configuration'),ensure_ascii=False)}`。",'']
            samples=report.get('samples') or []
            for sample in samples if isinstance(samples,list) else []:
                if not isinstance(sample,dict):
                    continue
                stats=sample.get('stats') or []
                residuals=[s.get('true_residual') for s in stats if isinstance(s,dict)
                           and isinstance(s.get('true_residual'),(int,float))] if isinstance(stats,list) else []
                lines.append(f"- 第 {sample.get('repeat')} 轮，预热={sample.get('warmup')}：{sample.get('wall_seconds')} 秒；"
                             f"列数={len(residuals)}；最大残差={max(residuals) if residuals else '缺失'}。")
            lines.append('')
        if row.get('exclusion_reasons'):
            lines += ['排除原因：'+'；'.join(row['exclusion_reasons'])+'。','']
        for conclusion in row.get('conclusions',[]):
            lines += [f"结论（{conclusion.get('time')}，{conclusion.get('status')}）：{conclusion.get('conclusion')}。",'']
        if row.get('unresolved'):
            lines += ['**尚未记录结论；不能把测量结束当作优化方向已经处理完毕。**','']
        paths=list(dict.fromkeys(row.get('log_paths',[])+row.get('profile_paths',[])+row.get('conclusion_evidence',[])))
        if paths:
            lines += ['证据：','']+[f'- {link(p)}' for p in paths]+['']
        for error in row.get('errors',[]):
            lines += [f'证据检查错误：{error}。','']
        if row.get('unregistered_measurements'):
            lines += [f"另保留 {len(row['unregistered_measurements'])} 个原始 measurement/diagnostic 报告；不作为该轮已导入完成或排名的依据。",'']
    lines += ['## 恢复、结论与回滚入口','',
        '本工具不修改账本，也不生成历史阅读回执。下轮阅读本经验后，仍先调用 `history` 获取提案回执。', '',
        '```bash',
        f"python tools/optimization/campaign.py --campaign \"{summary['campaign']}\" history",
        '# 核对原阶段的 argv/cwd/env/timeout，准备原命令 JSON 后显式恢复：',
        'python tools/optimization/campaign.py --campaign CAMPAIGN run ID --stage STAGE --command COMMAND.json --retry-interrupted --reason "已确认旧作业结束及所属进程清理"',
        '# 已失败/超时用 --retry-failed，并说明归因后的变化；不要自动重跑未知状态。',
        'python tools/optimization/campaign.py --campaign CAMPAIGN conclude ID --status inconclusive --conclusion "证据支持的结论与下一步" --evidence LOG REPORT',
        'python tools/optimization/campaign.py --campaign CAMPAIGN rollback ACCEPTED_ID --reason "回归证据"',
        '```','',
        '精确每列统计、全部检查点及 best-history 见同名 JSON；回滚只移动已验收版本指针，不删除实验。']
    return '\n'.join(lines)+'\n'


def write_summary(campaign_root, output, verify_artifacts=False):
    root,output=Path(campaign_root).resolve(),Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError('Summary output must be outside the read-only campaign ledger')
    result=collect(root,verify_artifacts)
    output.mkdir(parents=True,exist_ok=True)
    ledger.atomic(output/'experience.json',result)
    markdown=output/'experience.md'
    temporary=markdown.with_name(markdown.name+'.tmp')
    temporary.write_text(render_markdown(result),encoding='utf-8')
    temporary.replace(markdown)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--campaign',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--verify-artifacts',action='store_true')
    args=parser.parse_args()
    try:
        result=write_summary(args.campaign,args.output,args.verify_artifacts)
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print(f'summarize: {exc}',file=sys.stderr)
        return 2
    print(json.dumps(dict(output=str(args.output.resolve()),counts=result['counts'],
                          read_consistent=result['read_consistent']),indent=2))
    return 0 if result['read_consistent'] and not result['counts']['evidence_errors'] else 2


if __name__=='__main__':
    sys.exit(main())
