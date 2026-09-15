"""Opt-in real XeLaTeX + native PDF integration checks; no external messages."""
import json
from pathlib import Path
import shutil
import struct
import sys
import zlib

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wr import core, admin


def png(width, height, pixels):
    def chunk(kind, data):
        return struct.pack('!I', len(data)) + kind + data + struct.pack('!I', zlib.crc32(kind + data) & 0xffffffff)
    scanlines = b''.join(b'\0' + pixels[y * width * 3:(y+1) * width * 3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(scanlines)) + chunk(b'IEND', b''))


def main():
    qa = core.ROOT / '.runtime/qa'
    qa.mkdir(parents=True, exist_ok=True)
    source = qa / 'sources/한글 보고서'
    (source / 'figures').mkdir(parents=True, exist_ok=True)
    chart = bytes(c for y in range(100) for x in range(300)
                  for c in ((38, 70, 110) if (x // 60) % 2 == 0 and y > 30 else (238, 244, 250)))
    (source / 'figures/test.png').write_bytes(png(300, 100, chart))
    values = {'title': '윈도우 보고서 검증', 'author': '테스트 작성자', 'project': '검증 팀',
              'abstract': '이 문서는 프로그램 검증용 예시이며 실제 연구 결과가 아닙니다.',
              'Progress': '한글 입력과 PDF 생성을 확인합니다. 특수문자 & _ % #도 일반 텍스트로 표시합니다. 수식 $a_1+b^2$도 표시합니다.',
              'Problems': '실제 연구의 문제를 기술하는 입력 영역입니다.',
              'Plans': '다음 주 계획을 기록하는 입력 영역입니다.',
              'figures': [{'file': 'figures/test.png', 'id': 'test', 'caption': '그림 첨부 검증'}],
              'tables': [{'caption': '표 입력 검증', 'rows': [['항목', '상태'], ['한글', '확인'], ['PDF', '확인']]}]}
    values['Progress'] = '''<style>
@page { size: A4; margin: 9mm 10mm 8mm 10mm; }
body { font-size: 8.7pt; line-height: 1.18; margin: 0; padding: 0; }
h1 { font-size: 15pt; line-height: 1.02; margin: 0 0 2px 0; }
h2 { font-size: 11.3pt; line-height: 1.06; margin: 5px 0 2px 0; }
h3 { font-size: 9.6pt; line-height: 1.06; margin: 3px 0 1px 0; }
p { margin: 1px 0 2px 0; }
table { width: 100%; border-collapse: collapse; font-size: 7.9pt; margin: 2px 0 3px 0; }
th, td { padding: 1.5px 3px; border: 1px solid #aaa; }
</style>
## Markdown Conversion
### Formatting

Converted text and formula $a_1+b^2$.

| Item | Median | Maximum |
|---|---:|---:|
| Exposure | 3.2 ms | 9.1 ms |
| Upload | 4.5 ms | 12.0 ms |'''
    (source / 'report.wr.json').write_text(json.dumps(values, ensure_ascii=False, indent=2), encoding='utf-8')
    tex = source / 'main.tex'
    tex.write_text(core.form_source(values, allow_styles=True), encoding='utf-8')
    config = dict(core.read_config(), pdf_output=str(qa / 'reports'), admin_output=str(qa / 'final'), admin_data=str(qa / 'data'))
    report = core.build_report(tex, config, date='2026-09-11', serial=17)
    assert report['pages'] <= 2
    assert '테스트 작성자' in report['text'], report['text']
    assert '2026-09-W2' in report['text']
    assert 'Markdown Conversion' in report['text'] and 'Converted text' in report['text']
    assert 'Item' in report['text'] and '9.1 ms' in report['text']
    assert 'Weekly Report #17' in report['text'] and '1 / 1' in report['text']
    assert 'a' in report['text'] and 'b' in report['text']
    manager = {'schema': 1, 'storage_root': str(qa / 'reports'), 'timezone': 'Asia/Seoul', 'members': [
        {'id': 'a', 'display_name': '테스트 작성자', 'order': 1, 'required': True, 'search_roots': ['.']},
        {'id': 'b', 'display_name': '미제출 예시', 'order': 2, 'required': True, 'search_roots': ['.']}]}
    plan = admin.make_plan(manager, {'a': report['pdf']}, config, '2026-09-04')
    previous = admin.build_bundle(plan, manager['storage_root'], config, '2026-09-04', output=qa / 'review-previous', draft=True)
    final = admin.build_bundle(plan, manager['storage_root'], config, '2026-09-04', approved=True, review=previous['review'])
    plan = admin.make_plan(manager, {'a': report['pdf']}, config, '2026-09-11')
    current = admin.build_bundle(plan, manager['storage_root'], config, '2026-09-11', output=qa / 'review-current', draft=True)
    info = core.inspect_pdf(current['pdf'])
    assert info['pages'] == report['pages'] + 1
    assert '2026-09-W1' in info['text'] and '2026-09-W2' in info['text']
    results = {'report': {'pdf': report['pdf'], 'pages': report['pages']}, 'previous_final': final, 'current_draft': current}
    core.atomic_write(qa / 'results.json', json.dumps(results, ensure_ascii=False, indent=2))
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
