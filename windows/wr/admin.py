"""Deterministic native bundle builder and explicit, user-driven discovery."""
from __future__ import annotations

import datetime as dt
import io
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import time
import tomllib
from zoneinfo import ZoneInfo

from admin_records import read_manifest

from .core import (ROOT, STATE_ROOT, atomic_write, checked_file, compile_tex, inspect_pdf, metadata,
                   probe, publication_locks, refresh_pdf, sha256, stage_write, tex_escape, tsv)

STATES = {'included': 'O', 'exception': 'O*', 'missing': 'X', 'optional-missing': '--', 'unknown': '?'}
TOKEN = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*')


def paths(config):
    data = Path(config.get('admin_data') or STATE_ROOT / '.admin-wr')
    manifest = data / 'manager-manifest.toml' if config.get('admin_data') else STATE_ROOT / '.manager-manifest.toml'
    if not manifest.exists():
        manifest = STATE_ROOT / '.manager-manifest.toml'
    history = {}
    for directory in (data / 'manifests', STATE_ROOT / '.admin-wr/manifests',
                      Path(config['admin_output']) if config.get('admin_output') else None):
        if directory is None:
            continue
        if directory.exists() and not directory.is_dir():
            raise ValueError(f'이력 폴더가 아닙니다: {directory}')
        for file in sorted(directory.glob('*.manifest.tsv')):
            if not file.name.startswith('._'):
                history.setdefault(file.name.removesuffix('.manifest.tsv'), file)
    return manifest, data / 'manifests', history


def load_manager(config):
    file = paths(config)[0]
    manager = tomllib.loads(file.read_text(encoding='utf-8-sig'))
    validate_manager(manager, config)
    return manager


def validate_manager(manager, config):
    if manager.get('schema') != 1 or not manager.get('members'):
        raise ValueError('구성원 설정 schema=1과 members가 필요합니다.')
    root = Path(manager['storage_root'])
    if not root.is_absolute() or not root.is_dir():
        raise ValueError('보고서 저장소의 실제 절대 폴더를 지정하세요.')
    ZoneInfo(manager['timezone'])
    ids, orders = set(), set()
    for member in manager['members']:
        mid, order = member['id'], member['order']
        if not TOKEN.fullmatch(mid) or mid in ids or type(order) is not int or order < 1 or order in orders:
            raise ValueError('구성원 ID와 순서는 고유해야 합니다.')
        if not member.get('display_name') or type(member['required']) is not bool or not member.get('search_roots'):
            raise ValueError('구성원 이름, 필수 여부, 검색 폴더를 지정하세요.')
        tsv([[member['display_name']]])
        ids.add(mid)
        orders.add(order)
        for relative in member['search_roots']:
            path = Path(relative)
            if path.is_absolute() or '..' in path.parts:
                raise ValueError('검색 폴더는 저장소 안의 상대 경로여야 합니다.')
            directory = root / path
            if not directory.is_dir() or not directory.resolve().is_relative_to(root.resolve()):
                raise ValueError(f'검색 폴더를 확인하세요: {directory}')
            for candidate in (directory, *directory.parents):
                if candidate == root:
                    break
                if candidate.is_symlink() or getattr(candidate, 'is_junction', lambda: False)():
                    raise ValueError('검색 폴더에 연결 폴더를 사용할 수 없습니다.')
            if config.get('admin_output') and Path(config['admin_output']).resolve().is_relative_to(directory.resolve()):
                raise ValueError('합본 출력 폴더는 구성원 검색 폴더 밖이어야 합니다.')
    return manager


def save_manager(manager, config):
    validate_manager(manager, config)
    # JSON string quoting is valid TOML basic string quoting for these values.
    quote = lambda value: json.dumps(value, ensure_ascii=False)
    lines = ['schema = 1', 'storage_root = ' + quote(manager['storage_root']),
             'timezone = ' + quote(manager['timezone'])]
    for m in sorted(manager['members'], key=lambda m: m['order']):
        lines += ['', '[[members]]', 'id = ' + quote(m['id']), 'display_name = ' + quote(m['display_name']),
                  'order = ' + str(m['order']), 'required = ' + str(m['required']).lower(),
                  'search_roots = ' + quote(m['search_roots'])]
    destination = (Path(config['admin_data']) / 'manager-manifest.toml'
                   if config.get('admin_data') else STATE_ROOT / '.manager-manifest.toml')
    atomic_write(destination, '\n'.join(lines) + '\n')


def discover(manager):
    result = {}
    root = Path(manager['storage_root'])
    for m in sorted(manager['members'], key=lambda m: m['order']):
        files = set()
        for relative in m['search_roots']:
            for directory, dirs, names in os.walk(root / relative, followlinks=False):
                dirs[:] = [n for n in dirs if not (Path(directory) / n).is_symlink()
                           and not getattr(Path(directory) / n, 'is_junction', lambda: False)()]
                for name in names:
                    if name.lower().endswith('.pdf') and not name.startswith('._'):
                        files.add(checked_file(root, Path(directory) / name))
        result[m['id']] = sorted(files)
    return result


def history_rows(config, members, date):
    _, _, files = paths(config)
    current = metadata(date)
    history, issues, known = [], [], {}
    for week, file in files.items():
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])-W[1-5]', week) or week >= current['week-label']:
            continue
        try:
            parsed = read_manifest(file)
            bundle = parsed.bundle
            if bundle.week != week or bundle.state == 'draft':
                raise ValueError('최종 이력이 아닙니다.')
            if not config.get('admin_output'):
                raise ValueError('최종 PDF 경로를 확인하세요.')
            pdf = Path(config['admin_output']) / bundle.pdf_name
            if sha256(pdf) != bundle.pdf_sha256:
                raise ValueError('최종 PDF 해시 불일치')
            known[week] = ({entry.member_id: entry.state for entry in parsed.entries}, str(file))
        except (ValueError, OSError) as error:
            known[week] = ({}, str(file))
            issues.append(['issue', 'warning', 'history-unavailable', '-', f'검증할 수 없는 이력: {week}: {error}'])
    if not known:
        return [], [['issue', 'warning', 'first-run', '-', '검증된 이전 합본이 없습니다. 첫 합본을 검토하세요.']]
    # Canonical week labels are the month and ordinal of its Thursday.
    earliest = min(known)
    y, month, number = re.fullmatch(r'(\d{4})-(\d{2})-W([1-5])', earliest).groups()
    first = dt.date(int(y), int(month), 1)
    thursday = first + dt.timedelta(days=(3-first.weekday()) % 7 + (int(number)-1)*7)
    while thursday.isoformat() <= current['week-end']:
        week = metadata(thursday.isoformat())['week-label']
        if week >= current['week-label']:
            break
        states, evidence = known.get(week, ({}, 'No verified bundle record'))
        for m in members:
            history.append(['history', week, m['id'], states.get(m['id'], 'unknown'), evidence])
        thursday += dt.timedelta(days=7)
    return history, issues


def make_plan(manager, selected, config, date, reasons=None):
    """Selections are explicit user choices, never inferred from modification time."""
    reasons = reasons or {}
    candidates = discover(manager)
    rows = [['schema', 'admin-wr-plan/v1']]
    for m in sorted(manager['members'], key=lambda m: m['order']):
        mid = m['id']
        file = selected.get(mid)
        if file and Path(file).resolve() not in candidates[mid]:
            raise ValueError('선택한 PDF가 구성원의 검색 범위 밖에 있습니다.')
        state = 'included' if file else ('missing' if m['required'] else 'optional-missing')
        reason = 'user-selected' if file else 'missing-report'
        rows.append(['entry', str(m['order']), mid, m['display_name'], 'required' if m['required'] else 'optional',
                     state, str(Path(file).resolve()) if file else '-', reason])
        if not file and m['required']:
            rows.append(['issue', 'error', 'missing-report', mid, '필수 보고서가 선택되지 않았습니다.'])
        if file:
            info = probe(manager['storage_root'], file)
            if info['pages'] > 2:
                rows.append(['issue', 'warning', 'overlength-report', mid,
                             f'{info["pages"]} pages. ' + reasons.get(mid, '필수 근거를 유지하며 줄일 수 없는지 검토하세요.')])
        for candidate in candidates[mid]:
            rows.append(['candidate', mid, 'selected' if file and candidate == Path(file).resolve() else 'rejected',
                         str(candidate), 'user-selected' if file and candidate == Path(file).resolve() else 'not-selected'])
    history, issues = history_rows(config, manager['members'], date)
    return rows + history + issues


def validate_plan(rows, root, date):
    sizes = {'schema': 2, 'entry': 8, 'history': 5, 'candidate': 5, 'issue': 5}
    if [r for r in rows if r[0] == 'schema'] != [['schema', 'admin-wr-plan/v1']]:
        raise ValueError('admin-wr-plan/v1 계획 파일이 필요합니다.')
    if any(r[0] not in sizes or len(r) != sizes[r[0]] or any(not f for f in r) for r in rows):
        raise ValueError('계획 레코드 형식 오류')
    tsv(rows)
    entries = sorted([r for r in rows if r[0] == 'entry'], key=lambda r: int(r[1]))
    if not entries or len({r[1] for r in entries}) != len(entries) or len({r[2] for r in entries}) != len(entries):
        raise ValueError('구성원 ID와 순서는 고유해야 합니다.')
    ids = {r[2] for r in entries}
    sources = []
    for r in entries:
        if not re.fullmatch('[1-9][0-9]*', r[1]) or not TOKEN.fullmatch(r[2]) or not TOKEN.fullmatch(r[7]):
            raise ValueError('구성원 식별자/순서/사유 오류')
        if r[4] not in ('required', 'optional') or r[5] not in STATES or r[5] == 'unknown':
            raise ValueError('제출 상태 오류')
        if r[5] in ('included', 'exception'):
            sources.append(str(checked_file(root, r[6])))
        elif r[6] != '-' or (r[5] == 'missing') != (r[4] == 'required'):
            raise ValueError('누락 상태와 필수 여부가 일치하지 않습니다.')
        if r[5] in ('missing', 'exception') and not any(x[0] == 'issue' and x[3] == r[2] for x in rows):
            raise ValueError('누락/예외 구성원의 문제 설명이 필요합니다.')
    if len(set(sources)) != len(sources):
        raise ValueError('같은 PDF를 여러 구성원에게 선택할 수 없습니다.')
    seen_history, seen_candidates, selected_members = set(), set(), set()
    for r in rows:
        if r[0] == 'issue' and (r[1] not in ('warning', 'error') or not TOKEN.fullmatch(r[2]) or r[3] not in ids | {'-'}):
            raise ValueError('문제 레코드 오류')
        if r[0] == 'history':
            key = (r[1], r[2])
            if (not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])-W[1-5]', r[1]) or r[1] >= metadata(date)['week-label']
                    or r[2] not in ids or r[3] not in STATES or key in seen_history):
                raise ValueError('과거 이력 레코드 오류')
            seen_history.add(key)
        if r[0] == 'candidate':
            file = str(checked_file(root, r[3]))
            key = r[1], file
            if r[1] not in ids or r[2] not in ('selected', 'rejected') or not TOKEN.fullmatch(r[4]) or key in seen_candidates:
                raise ValueError('후보 레코드 오류')
            seen_candidates.add(key)
            if r[2] == 'selected':
                if r[1] in selected_members or not any(e[2] == r[1] and str(Path(e[6]).resolve()) == file for e in entries):
                    raise ValueError('선택 후보가 구성원 선택과 일치하지 않습니다.')
                selected_members.add(r[1])
    if any(r[0] == 'candidate' for r in rows) and selected_members != {e[2] for e in entries if e[6] != '-'}:
        raise ValueError('선택된 모든 구성원에 selected 후보 기록이 필요합니다.')
    return entries


def review_fingerprint(rows, root, date):
    validate_plan(rows, root, date)
    files = sorted({r[6] for r in rows if r[0] == 'entry' and r[6] != '-'} |
                   {r[3] for r in rows if r[0] == 'candidate'})
    return {'date': date, 'plan': tsv(rows), 'sources': {
        f: {'sha256': sha256(checked_file(root, f)), 'mtime_ns': Path(f).stat().st_mtime_ns} for f in files}}


def build_bundle(rows, root, config, date, output=None, draft=False, approved=False, review=None):
    from pypdf import PdfReader, PdfWriter
    entries = validate_plan(rows, root, date)
    meta = metadata(date)
    fingerprint = review_fingerprint(rows, root, date)
    if approved and (not review or json.loads(Path(review).read_text(encoding='utf-8')) != fingerprint):
        raise ValueError('검토 기록이 없거나 원본/계획이 바뀌었습니다. 초안을 다시 생성하세요.')
    if draft and approved:
        raise ValueError('초안과 최종 승인은 동시에 지정할 수 없습니다.')
    if not draft and not (output or config.get('admin_output')):
        raise ValueError('최종 합본 출력 폴더를 지정하세요.')
    destdir = Path(output or (tempfile.mkdtemp(prefix='wr-review-') if draft else config['admin_output'])).resolve()
    if draft and config.get('admin_output') and destdir.is_relative_to(Path(config['admin_output']).resolve()):
        raise ValueError('초안은 최종 출력 폴더 밖에 저장해야 합니다.')
    issues = [r[:] for r in rows if r[0] == 'issue']
    history = [r for r in rows if r[0] == 'history']
    weeks = {r[1] for r in history}
    states = {(r[1], r[2]): r[3] for r in history}
    if any(states.get((w, e[2]), 'unknown') == 'unknown' for w in weeks for e in entries):
        issues.append(['issue', 'warning', 'history-unavailable', '-', '확인되지 않은 과거 제출 현황이 있습니다.'])
    infos = {e[2]: probe(root, e[6]) for e in entries if e[6] != '-'}
    for e in entries:
        if e[2] in infos and infos[e[2]]['pages'] > 2 and not any(i[2] == 'overlength-report' and i[3] == e[2] for i in issues):
            issues.append(['issue', 'warning', 'overlength-report', e[2], f'{infos[e[2]]["pages"]} pages; review required'])
    if issues and not draft and not approved:
        raise ValueError('검토가 필요한 문제가 있습니다. 초안을 생성하고 확인한 뒤 확정하세요.')
    state = 'draft' if draft else ('approved-with-issues' if approved else 'complete')
    with tempfile.TemporaryDirectory(prefix='wr-bundle-') as tmp:
        stage = Path(tmp)
        # The canonical cover retains its one-page overflow check and complete history.
        shutil.copyfile(ROOT / 'skills/admin-wr/assets/bundle.tex', stage / 'bundle.tex')
        values = {'Week': meta['week-label'], 'WeekStart': meta['week-start'], 'WeekEnd': meta['week-end'],
                  'ReportDate': date, 'IncludedCount': len(infos),
                  'RequiredIncludedCount': sum(e[4] == 'required' and e[6] != '-' for e in entries),
                  'RequiredCount': sum(e[4] == 'required' for e in entries)}
        data = '\\newif\\ifBundleDraft\n' + ('\\BundleDrafttrue' if draft else '\\BundleDraftfalse') + '\n'
        data += '\n'.join(r'\def\Bundle' + k + '{' + str(v) + '}' for k, v in values.items())
        (stage / 'bundle-data.tex').write_text(data, encoding='utf-8')
        (stage / 'bundle-includes.tex').write_text('', encoding='utf-8')
        for e in entries:
            states[meta['week-label'], e[2]] = e[5]
        table = [r'\begingroup\setlength{\tabcolsep}{2pt}',
                 r'\begin{tabularx}{\textwidth}{l*{' + str(len(entries)) + r'}{>{\centering\arraybackslash}X}}', r'\toprule',
                 'Week & ' + ' & '.join(r'\rotatebox{60}{\scriptsize ' + tex_escape(e[3]) + '}' for e in entries) + r' \\', r'\midrule']
        for week in sorted(weeks | {meta['week-label']}, reverse=True):
            if week == meta['week-label']:
                table.append(r'\rowcolor{currentweekblue}')
            table.append(week + ' & ' + ' & '.join(STATES[states.get((week, e[2]), 'unknown')] for e in entries) + r' \\')
        table += [r'\bottomrule\end{tabularx}\par\endgroup']
        (stage / 'bundle-history.tex').write_text('\n'.join(table), encoding='utf-8')
        cover = compile_tex(stage, 'bundle.tex', config)
        cover_reader = PdfReader(io.BytesIO(cover))
        if len(cover_reader.pages) != 1:
            raise ValueError('합본 표지는 정확히 1페이지여야 합니다.')
        writer = PdfWriter()
        writer.append(cover_reader)
        records = []
        next_page = 2
        for e in entries:
            _, order, mid, name, requirement, status, file, reason = e
            if file != '-':
                original = Path(file).read_bytes()
                staged = stage / (mid + '.pdf')
                staged.write_bytes(original)
                if sha256(staged) != infos[mid]['sha256']:
                    raise ValueError('합본 생성 중 원본이 변경되었습니다.')
                writer.append(PdfReader(io.BytesIO(original)))
                count = infos[mid]['pages']
                records.append(['entry', order, mid, name, requirement, status, str(Path(file).resolve().relative_to(Path(root).resolve())),
                                str(infos[mid]['mtime']), infos[mid]['sha256'], str(count), str(next_page), str(next_page + count - 1), reason])
                next_page += count
            else:
                records.append(['entry', order, mid, name, requirement, status, '-', '-', '-', '0', '-', '-', reason])
        buffer = io.BytesIO()
        writer.write(buffer)
        result = buffer.getvalue()
        final_stage = stage / 'result.pdf'
        final_stage.write_bytes(result)
        if inspect_pdf(final_stage)['pages'] != next_page - 1:
            raise ValueError('합본 페이지 수 검증 실패')
        if review_fingerprint(rows, root, date) != fingerprint:
            raise ValueError('생성 중 후보 파일이 변경되었습니다. 다시 검토하세요.')
        target = destdir / (meta['week-label'] + '.pdf')
        historydir = destdir / '.manifests' if draft else paths(config)[1]
        record_path = historydir / (meta['week-label'] + '.manifest.tsv')
        records = [['schema', 'admin-wr-bundle/v1'],
                   ['bundle', date, meta['week-label'], meta['week-start'], meta['week-end'], state,
                    'required' if draft else ('user-confirmed' if approved else 'not-required'), target.name, sha256(final_stage)],
                   ['created-at', str(int(time.time()))]] + history + records
        for r in rows:
            if r[0] == 'candidate':
                file = checked_file(root, r[3])
                records.append(['candidate', r[1], r[2], str(file.relative_to(Path(root).resolve())), str(int(file.stat().st_mtime)), sha256(file), r[4]])
        records += issues
        review_path = destdir / (meta['week-label'] + '.review.json')
        # Lock both destinations through publication, also across installations that
        # share only the PDF or history folder. Recheck sources after waiting.
        with publication_locks(target, record_path):
            if review_fingerprint(rows, root, date) != fingerprint:
                raise ValueError('발행 대기 중 후보 파일이 변경되었습니다. 다시 검토하세요.')
            staged_pdf = stage_write(target, result)
            staged_record = None
            try:
                staged_record = stage_write(record_path, tsv(records))
                os.replace(staged_pdf, target)
                refresh_pdf(target)
                # Separate replacements: hash validation detects an interrupted pair.
                os.replace(staged_record, record_path)
                if draft:
                    atomic_write(review_path, json.dumps(fingerprint, ensure_ascii=False, indent=2))
            finally:
                staged_pdf.unlink(missing_ok=True)
                if staged_record:
                    staged_record.unlink(missing_ok=True)
    return {'pdf': str(target), 'manifest': str(record_path), 'review': str(review_path) if draft else None,
            'issues': issues, 'state': state}
