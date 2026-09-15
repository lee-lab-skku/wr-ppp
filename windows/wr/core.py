from __future__ import annotations

import csv
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parents[2]))
STATE_ROOT = (Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'WeeklyReport'
              if getattr(sys, 'frozen', False) else ROOT)
DEFAULT_CONFIG = (Path(os.environ.get('LOCALAPPDATA', Path.home())) / 'WeeklyReport' / 'config.json'
                  if getattr(sys, 'frozen', False) else ROOT / '.windows-config.json')


def stage_write(path, data):
    path = Path(path)
    if path.exists() and not path.is_file():
        raise ValueError(f'파일 대신 다른 항목이 있습니다: {path}')
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data.encode('utf-8') if isinstance(data, str) else data)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        Path(name).unlink(missing_ok=True)
        raise
    return Path(name)


def atomic_write(path, data):
    staged = stage_write(path, data)
    try:
        try:
            os.replace(staged, path)
        except PermissionError as error:
            raise ValueError(
                f'파일을 교체할 수 없습니다: {path}\n'
                '같은 PDF가 열려 있다면 PDF 뷰어를 닫고 다시 시도하세요. '
                '계속 실패하면 보고서 전용 폴더와 다른 PDF 출력 폴더를 지정하세요.'
            ) from error
    finally:
        staged.unlink(missing_ok=True)


def config_path():
    return Path(os.environ.get('WR_CONFIG', DEFAULT_CONFIG))


def read_config():
    path = config_path()
    return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}


def save_config(config):
    for key in ('pdf_output', 'admin_output', 'admin_data', 'tex_bin'):
        if config.get(key) and not Path(config[key]).expanduser().is_absolute():
            raise ValueError(f'{key}: 절대 경로를 지정하세요.')
    atomic_write(config_path(), json.dumps(config, ensure_ascii=False, indent=2))


def metadata(value=None):
    if value and not re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        raise ValueError('날짜는 YYYY-MM-DD 형식이어야 합니다.')
    date = dt.date.fromisoformat(value) if value else dt.date.today()
    monday = date - dt.timedelta(days=date.weekday())
    thursday = monday + dt.timedelta(days=3)
    return {'report-date': date.isoformat(),
            'week-label': f'{thursday:%Y-%m}-W{(thursday.day - 1) // 7 + 1}',
            'week-start': monday.isoformat(),
            'week-end': (monday + dt.timedelta(days=6)).isoformat()}


def sha256(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def tsv(rows):
    output = io.StringIO(newline='')
    for row in rows:
        if any(any(c in str(v) for c in '\t\r\n') for v in row):
            raise ValueError('기록 필드에는 탭이나 줄바꿈을 넣을 수 없습니다.')
    csv.writer(output, delimiter='\t', lineterminator='\n', quoting=csv.QUOTE_NONE).writerows(rows)
    return output.getvalue()


def read_tsv(path):
    return [r for r in csv.reader(Path(path).read_text(encoding='utf-8-sig').splitlines(), delimiter='\t')
            if r and r[0] and not r[0].startswith('#')]


def tex_escape(text):
    mapping = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}', '#': r'\#', '$': r'\$',
               '%': r'\%', '&': r'\&', '_': r'\_', '^': r'\textasciicircum{}', '~': r'\textasciitilde{}'}
    return ''.join(mapping.get(c, c) for c in str(text))


_UNSAFE_MATH = re.compile(
    r'\\(?:input|include|write|openin|openout|read|catcode|usepackage|documentclass|begin|end|def|newcommand|csname)\b',
    re.IGNORECASE,
)


def rich_text(text):
    """Escape prose while preserving explicit $...$ and $$...$$ math."""
    source = str(text)
    result = []
    prose_start = 0
    index = 0
    while index < len(source):
        if source[index] != '$' or (index and source[index - 1] == '\\'):
            index += 1
            continue
        delimiter = '$$' if source.startswith('$$', index) else '$'
        result.append(tex_escape(source[prose_start:index]))
        end = source.find(delimiter, index + len(delimiter))
        if end < 0:
            raise ValueError(f'닫히지 않은 수식이 있습니다: {delimiter}로 시작한 수식을 닫아 주세요.')
        formula = source[index + len(delimiter):end]
        if not formula.strip():
            raise ValueError('빈 수식은 사용할 수 없습니다.')
        if delimiter == '$' and ('\n' in formula or '\r' in formula):
            raise ValueError('$...$ 인라인 수식 안에는 줄바꿈을 넣을 수 없습니다.')
        if _UNSAFE_MATH.search(formula):
            raise ValueError('수식에는 문서나 파일을 조작하는 LaTeX 명령을 사용할 수 없습니다.')
        result.extend((delimiter, formula, delimiter))
        index = end + len(delimiter)
        prose_start = index
    result.append(tex_escape(source[prose_start:]))
    return ''.join(result).replace(r'\textbackslash{}\$', r'\$')


def markdown_inline(text):
    """Convert supported inline Markdown while escaping raw LaTeX."""
    source = str(text)
    tokens = {}

    def keep(value):
        key = f'WRMDTOKEN{len(tokens)}ZZ'
        tokens[key] = value
        return key

    pattern = re.compile(
        r'(\[font=(?:serif|sans|mono)\].+?\[/font\]|\[size=(?:8|9|10|11|12|14|16)\].+?\[/size\]|'
        r'`[^`\r\n]+`|(?<!\\)\$\$[^$\r\n]+\$\$|(?<!\\)\$[^$\r\n]+\$|'
        r'\*\*[^*\r\n]+\*\*|(?<!\*)\*[^*\r\n]+\*|\+\+[^+\r\n]+\+\+|~~[^~\r\n]+~~|'
        r'!\[[^\]\r\n]+\]\([^\)\r\n]+\)|\[[^\]\r\n]+\]\([^\)\r\n]+\))'
    )

    def convert(match):
        value = match.group(0)
        image_match = re.fullmatch(r'!\[([^]]+)\]\(([^)]+)\)', value)
        if image_match:
            return keep(r'\textit{[그림 추가 필요: ' + markdown_inline(image_match.group(1)) + ']}')
        font_match = re.fullmatch(r'\[font=(serif|sans|mono)\](.+)\[/font\]', value)
        if font_match:
            command = {'serif': r'\textrm', 'sans': r'\textsf', 'mono': r'\texttt'}[font_match.group(1)]
            return keep(command + '{' + markdown_inline(font_match.group(2)) + '}')
        size_match = re.fullmatch(r'\[size=(8|9|10|11|12|14|16)\](.+)\[/size\]', value)
        if size_match:
            size = int(size_match.group(1))
            return keep(r'{\fontsize{' + str(size) + 'pt}{' + str(round(size * 1.2, 1)) +
                        r'pt}\selectfont ' + markdown_inline(size_match.group(2)) + '}')
        if value.startswith('`'):
            return keep(r'\texttt{' + tex_escape(value[1:-1]) + '}')
        if value.startswith('$'):
            return keep(rich_text(value))
        if value.startswith('**'):
            return keep(r'\textbf{' + markdown_inline(value[2:-2]) + '}')
        if value.startswith('*'):
            return keep(r'\emph{' + markdown_inline(value[1:-1]) + '}')
        if value.startswith('++'):
            return keep(r'\underline{' + markdown_inline(value[2:-2]) + '}')
        if value.startswith('~~'):
            return keep(r'\sout{' + markdown_inline(value[2:-2]) + '}')
        label, url = re.fullmatch(r'\[([^]]+)\]\(([^)]+)\)', value).groups()
        if not re.fullmatch(r'https?://[^\s{}\\]+', url):
            raise ValueError('Markdown 링크는 http:// 또는 https:// 주소만 지원합니다.')
        safe_url = ''.join({'%': r'\%', '#': r'\#', '&': r'\&', '_': r'\_'}.get(c, c) for c in url)
        return keep(r'\href{' + safe_url + '}{' + markdown_inline(label) + '}')

    substituted = pattern.sub(convert, source)
    if re.search(r'(?<!\\)\$', substituted):
        raise ValueError('닫히지 않은 수식이 있습니다. $로 시작한 수식을 $로 닫아 주세요.')
    converted = tex_escape(substituted).replace(r'\textbackslash{}\$', r'\$')
    for key, value in tokens.items():
        converted = converted.replace(key, value)
    return converted


def markdown_styles(text):
    """Remove embedded CSS and return the supported rules for LaTeX rendering."""
    source = str(text)
    blocks = re.findall(r'<style\b[^>]*>(.*?)</style\s*>', source, flags=re.IGNORECASE | re.DOTALL)
    source = re.sub(r'<style\b[^>]*>.*?</style\s*>', '', source, flags=re.IGNORECASE | re.DOTALL)
    rules = {}
    for block in blocks:
        block = re.sub(r'/\*.*?\*/', '', block, flags=re.DOTALL)
        for selector, declarations in re.findall(r'([^{}]+)\{([^{}]*)\}', block):
            for name in selector.split(','):
                name = name.strip().lower()
                if name not in ('@page', 'body', 'h1', 'h2', 'h3', 'p', 'table', 'th', 'td'):
                    continue
                properties = rules.setdefault(name, {})
                for declaration in declarations.split(';'):
                    if ':' not in declaration:
                        continue
                    key, value = (part.strip().lower() for part in declaration.split(':', 1))
                    if key in ('size', 'margin', 'padding', 'font-size', 'line-height',
                               'width', 'border', 'border-collapse'):
                        properties[key] = value
    return source.strip(), rules


def css_length(value, default='0pt'):
    if str(value).strip() == '0':
        return '0pt'
    match = re.fullmatch(r'(-?\d+(?:\.\d+)?)(mm|pt|px)', str(value).strip())
    if not match:
        return default
    number, unit = float(match.group(1)), match.group(2)
    if unit == 'px':
        number, unit = number * 0.75, 'pt'
    return f'{number:g}{unit}'


def css_box(value):
    pieces = str(value).split()
    if not 1 <= len(pieces) <= 4:
        return None
    values = [css_length(piece, None) for piece in pieces]
    if any(piece is None for piece in values):
        return None
    if len(values) == 1:
        return values * 4
    if len(values) == 2:
        return [values[0], values[1], values[0], values[1]]
    if len(values) == 3:
        return [values[0], values[1], values[2], values[1]]
    return values


def css_font(rule, default):
    value = rule.get('font-size', default)
    match = re.fullmatch(r'(\d+(?:\.\d+)?)(pt|px)', value)
    if not match:
        return float(re.match(r'[\d.]+', default).group())
    size = float(match.group(1))
    return size * 0.75 if match.group(2) == 'px' else size


def heading_latex(level, title, styles):
    content = markdown_inline(title)
    if not styles:
        if level == 1:
            return r'\ReportHeading{' + content + '}'
        if level == 2:
            return r'\par\noindent{\bfseries ' + content + r'}\par'
        return r'\par\noindent{\itshape ' + content + r'}\par'
    rule = styles.get(f'h{min(level, 3)}', {})
    defaults = {1: '15pt', 2: '11.3pt', 3: '9.6pt'}
    size = css_font(rule, defaults[min(level, 3)])
    leading_value = rule.get('line-height', '1.06')
    leading = size * (float(leading_value) if re.fullmatch(r'\d+(?:\.\d+)?', leading_value) else 1.06)
    margins = css_box(rule.get('margin', '0pt')) or ['0pt'] * 4
    weight = r'\bfseries ' if level <= 3 else r'\itshape '
    return (r'\par\vspace{' + margins[0] + r'}\noindent{\fontsize{' + f'{size:g}' +
            r'pt}{' + f'{leading:g}' + r'pt}\selectfont ' + weight + content +
            r'}\par\vspace{' + margins[2] + '}')


def markdown_table(lines, index, styles):
    def cells(line):
        return [part.strip() for part in line.strip().strip('|').split('|')]
    if index + 1 >= len(lines) or '|' not in lines[index]:
        return None
    header, separator = cells(lines[index]), cells(lines[index + 1])
    if not header or len(header) != len(separator) or not all(re.fullmatch(r':?-{3,}:?', cell) for cell in separator):
        return None
    rows = []
    cursor = index + 2
    while cursor < len(lines) and '|' in lines[cursor] and lines[cursor].strip():
        row = cells(lines[cursor])
        if len(row) != len(header):
            raise ValueError('Markdown 표의 모든 행은 열 개수가 같아야 합니다.')
        rows.append(row)
        cursor += 1
    table_rule, cell_rule = styles.get('table', {}), {**styles.get('th', {}), **styles.get('td', {})}
    size = css_font(table_rule, '7.9pt')
    margins = css_box(table_rule.get('margin', '0pt')) or ['0pt'] * 4
    padding = css_box(cell_rule.get('padding', '1.5px 3px')) or ['1.125pt', '2.25pt'] * 2
    spec = '|' + '|'.join('X' for _ in header) + '|'
    head = ' & '.join(r'\textbf{' + markdown_inline(cell) + '}' for cell in header) + r' \\'
    body = ''.join('\n' + ' & '.join(markdown_inline(cell) for cell in row) + r' \\ \hline' for row in rows)
    latex = (r'\par\vspace{' + margins[0] + r'}{\fontsize{' + f'{size:g}' + 'pt}{' +
             f'{size * 1.18:g}' + r'pt}\selectfont\setlength{\tabcolsep}{' + padding[1] +
             r'}\begin{tabularx}{\linewidth}{' + spec + r'}\hline ' + head + r' \hline' + body +
             r'\end{tabularx}}\par\vspace{' + margins[2] + '}')
    return latex, cursor


def markdown_to_latex(text, styles=None):
    """Convert a controlled Markdown subset into the report's LaTeX structure."""
    text, own_styles = markdown_styles(text)
    styles = {**own_styles, **(styles or {})}
    lines = str(text).replace('\r\n', '\n').replace('\r', '\n').split('\n')
    output = []
    list_kind = None

    def close_list():
        nonlocal list_kind
        if list_kind:
            output.append(r'\end{' + list_kind + '}')
            list_kind = None

    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        table = markdown_table(lines, index, styles)
        if table:
            close_list()
            latex, index = table
            output.append(latex)
            continue
        if stripped.startswith('$$'):
            close_list()
            formula = stripped[2:]
            if formula.endswith('$$') and len(formula) > 2:
                formula = formula[:-2]
            else:
                collected = [formula]
                index += 1
                while index < len(lines) and not lines[index].rstrip().endswith('$$'):
                    collected.append(lines[index])
                    index += 1
                if index >= len(lines):
                    raise ValueError('닫히지 않은 $$...$$ 수식이 있습니다.')
                collected.append(lines[index].rstrip()[:-2])
                formula = '\n'.join(collected).strip()
            if not formula.strip() or _UNSAFE_MATH.search(formula):
                raise ValueError('빈 수식 또는 허용되지 않는 LaTeX 명령이 있습니다.')
            output.extend((r'\[', formula, r'\]'))
        elif not stripped:
            close_list()
            if output and output[-1] != '':
                output.append('')
        elif re.match(r'^#{1,6}\s+', stripped):
            close_list()
            level = len(re.match(r'^(#+)', stripped).group(1))
            title = re.sub(r'^#{1,6}\s+', '', stripped)
            output.append(heading_latex(level, title, styles))
        elif re.match(r'^[-+*]\s+', stripped):
            if list_kind != 'itemize':
                close_list()
                list_kind = 'itemize'
                output.append(r'\begin{itemize}')
            output.append(r'\item ' + markdown_inline(re.sub(r'^[-+*]\s+', '', stripped)))
        elif re.match(r'^\d+[.)]\s+', stripped):
            if list_kind != 'enumerate':
                close_list()
                list_kind = 'enumerate'
                output.append(r'\begin{enumerate}')
            output.append(r'\item ' + markdown_inline(re.sub(r'^\d+[.)]\s+', '', stripped)))
        else:
            close_list()
            hard_break = line.endswith('  ')
            output.append(markdown_inline(line.rstrip()) + (r'\\' if hard_break else ''))
        index += 1
    close_list()
    return '\n'.join(output).strip()


def markdown_document_style(styles):
    commands = []
    page = styles.get('@page', {})
    margins = css_box(page.get('margin', ''))
    if margins:
        commands.append(r'\geometry{top=' + margins[0] + ',right=' + margins[1] +
                        ',bottom=' + margins[2] + ',left=' + margins[3] +
                        r',includefoot,footskip=4mm}')
    body = styles.get('body', {})
    size = css_font(body, '10pt')
    line_height = body.get('line-height', '1.2')
    factor = float(line_height) if re.fullmatch(r'\d+(?:\.\d+)?', line_height) else 1.2
    commands.append(r'\newcommand{\WRMarkdownBodyStyle}{\fontsize{' + f'{size:g}' +
                    'pt}{' + f'{size * factor:g}' + r'pt}\selectfont}')
    paragraph = styles.get('p', {})
    paragraph_margin = css_box(paragraph.get('margin', ''))
    if paragraph_margin:
        commands.append(r'\setlength{\parskip}{' + paragraph_margin[2] + '}')
    return '\n'.join(commands)


def tool(name, config):
    if config.get('tex_bin'):
        found = shutil.which(name, path=config['tex_bin'])
        if found:
            return found
    portable = Path(sys.executable).parent / 'tex/bin/windows' if getattr(sys, 'frozen', False) else ROOT / '.runtime/TinyTeX/bin/windows'
    found = shutil.which(name, path=str(portable))
    if found:
        return found
    found = shutil.which(name)
    if not found:
        raise ValueError(f'{name}를 찾을 수 없습니다. Windows용 TeX Live를 설치하고 설정에서 bin 폴더를 선택하세요.')
    return found


def preflight(config):
    from pypdf import PdfReader  # noqa: F401
    import zoneinfo
    zoneinfo.ZoneInfo('Asia/Seoul')
    return {'xelatex': tool('xelatex', config), 'python': sys.version.split()[0],
            'build_mode': 'native; shell escape disabled; not a container sandbox'}


def latex_error_summary(log):
    lines = str(log).splitlines()
    markers = [i for i, line in enumerate(lines)
               if 'LaTeX Error:' in line or re.match(r'^!\s', line) or re.search(r':\d+:\s', line)]
    if not markers:
        return '\n'.join(lines[-25:])
    start = markers[-1]
    return '\n'.join(lines[start:min(len(lines), start + 16)]).strip()


def compile_tex(directory, source, config, definitions=''):
    engine = tool('xelatex', config)
    env = os.environ.copy()
    env['PATH'] = str(Path(engine).parent) + os.pathsep + env.get('PATH', '')
    env['TEXINPUTS'] = str(ROOT).replace('\\', '/') + '//' + os.pathsep + env.get('TEXINPUTS', '')
    env['openout_any'] = 'p'
    env['openin_any'] = 'p'
    # Direct XeLaTeX avoids latexmk's external Perl requirement on Windows.
    # Repeat until reference/lastpage auxiliary data stabilizes.
    previous = None
    logs = []
    for run in range(5):
        command = [engine, '-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error',
                   '-file-line-error', '-jobname=wr-result', definitions + r'\input{' + source + '}']
        result = subprocess.run(command, cwd=directory, env=env, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=180,
                                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        log = result.stdout.decode('utf-8', errors='replace')
        logs.append(log)
        if result.returncode:
            raise ValueError('LaTeX 변환 실패:\n' + latex_error_summary(log))
        aux = b''.join(p.read_bytes() for p in sorted(Path(directory).glob('wr-result.*'))
                       if p.suffix in ('.aux', '.out', '.toc'))
        if run and aux == previous:
            pdf = Path(directory) / 'wr-result.pdf'
            inspect_pdf(pdf)
            return pdf.read_bytes()
        previous = aux
    raise ValueError('5회 실행 후에도 참조/쪽번호가 안정되지 않았습니다. 소스를 확인하세요.')


def inspect_pdf(path):
    from pypdf import PdfReader
    data = Path(path).read_bytes()
    reader = PdfReader(io.BytesIO(data))
    if reader.is_encrypted:
        raise ValueError(f'암호화된 PDF는 사용할 수 없습니다: {path}')
    if not reader.pages:
        raise ValueError(f'빈 PDF입니다: {path}')
    text = '\n'.join(p.extract_text() or '' for p in reader.pages)
    return {'pages': len(reader.pages), 'sha256': hashlib.sha256(data).hexdigest(),
            'text': text, 'creation-date': str((reader.metadata or {}).get('/CreationDate', '-'))}


def checked_file(root, file):
    root, file = Path(root).resolve(), Path(file)
    if not file.is_absolute() or file.suffix.lower() != '.pdf' or not file.is_file():
        raise ValueError(f'올바른 절대 PDF 경로가 아닙니다: {file}')
    if file.is_symlink() or getattr(file, 'is_junction', lambda: False)():
        raise ValueError('연결 파일은 허용하지 않습니다.')
    resolved = file.resolve()
    if not resolved.is_relative_to(root):
        raise ValueError('보고서가 지정된 저장소 밖에 있습니다.')
    current = file.parent
    while current != root and current != current.parent:
        if current.is_symlink() or getattr(current, 'is_junction', lambda: False)():
            raise ValueError('연결 폴더는 검색하지 않습니다.')
        current = current.parent
    return resolved


def probe(root, file):
    file = checked_file(root, file)
    before = (file.stat().st_mtime_ns, sha256(file))
    info = inspect_pdf(file)
    if before != (file.stat().st_mtime_ns, sha256(file)) or before[1] != info['sha256']:
        raise ValueError('검사 중 원본 PDF가 변경되었습니다.')
    return dict(info, file=str(file), mtime=int(file.stat().st_mtime))


def build_report(source, config, date=None, serial=None, here=False):
    source = Path(source).resolve()
    if source.suffix.lower() != '.tex' or not source.is_file():
        raise ValueError('TeX 소스 파일을 선택하세요.')
    if not config.get('pdf_output'):
        raise ValueError('설정에서 PDF 출력 폴더를 먼저 지정하세요.')
    configured = Path(config['pdf_output']).expanduser()
    if not configured.is_absolute():
        raise ValueError('PDF 출력 폴더는 절대 경로여야 합니다.')
    name = source.parent.name + '.pdf'
    dest = (source.parent if here else configured) / name
    if serial is not None and (not re.fullmatch(r'[1-9][0-9]*', str(serial))):
        raise ValueError('일련번호는 양의 정수여야 합니다.')
    if serial is None:
        serial = 1 + sum(p.name != name for p in configured.glob('*.pdf') if p.is_file() and not p.is_symlink())
    meta = metadata(date)
    definitions = (rf'\def\ReportSerialNumber{{{serial}}}'
                   rf'\def\ReportDate{{{meta["report-date"]}}}'
                   rf'\def\ReportWeekLabel{{{meta["week-label"]}}}')
    # Do not delete an existing output before a successful build.
    with tempfile.TemporaryDirectory(prefix='wr-build-') as tmp:
        stage = Path(tmp) / 'src'
        def ignore(directory, names):
            return [n for n in names if n in ('.git', '.venv', '.windows-deps', '.runtime', '__pycache__')
                    or (Path(directory) / n).is_symlink()
                    or getattr(Path(directory) / n, 'is_junction', lambda: False)()]
        shutil.copytree(source.parent, stage, ignore=ignore)
        # A fixed ASCII entry name avoids TeX quoting problems with Unicode/space filenames.
        shutil.copyfile(source, stage / 'wr-input.tex')
        result = compile_tex(stage, 'wr-input.tex', config, definitions)
        atomic_write(dest, result)
    if not here:
        local = source.parent / name
        if local.resolve() != dest.resolve() and local.exists():
            local.unlink()
    return {'pdf': str(dest.resolve()), 'serial': serial, **meta, **inspect_pdf(dest)}


def form_source(values, allow_styles=False):
    cleaned = dict(values)
    styles = {}
    for key in ('abstract', 'Progress', 'Problems', 'Plans'):
        cleaned[key], found = markdown_styles(values.get(key, ''))
        if allow_styles:
            for selector, properties in found.items():
                styles.setdefault(selector, {}).update(properties)
    header = '\n'.join([r'\documentclass[10pt,a4paper]{article}', r'\usepackage{weekly-report}',
                        r'\usepackage{kotex}', markdown_document_style(styles), r'\begin{document}',
                        r'\ReportHeader' + ''.join('{' + rich_text(values.get(k, '')) + '}' for k in ('title', 'author', 'project'))])
    figures = values.get('figures', [])
    valid_positions = {'after_abstract', 'after_progress', 'after_problems', 'after_plans'}
    def figure_parts(position):
        generated = []
        for item in figures:
            item_position = item.get('position', 'after_plans')
            if item_position not in valid_positions:
                raise ValueError('그림 삽입 위치가 올바르지 않습니다.')
            if item_position != position:
                continue
            if not re.fullmatch(r'figures/[A-Za-z0-9_-]+\.(png|jpg|jpeg|pdf)', item['file']) or not re.fullmatch(r'[A-Za-z0-9_-]+', item['id']):
                raise ValueError('그림 경로/식별자 형식이 올바르지 않습니다.')
            generated.append(r'\ReportFigure{' + item['file'] + '}{' + rich_text(item['caption']) + '}{fig:' + item['id'] + '}{45mm}')
        return generated
    parts = [header, r'\WRMarkdownBodyStyle', r'\begin{reportabstract}',
             markdown_to_latex(cleaned.get('abstract', ''), styles), r'\end{reportabstract}']
    parts += figure_parts('after_abstract')
    for key in ('Progress', 'Problems', 'Plans'):
        parts += [r'\begin{pppbox}{' + key + '}', markdown_to_latex(cleaned.get(key, ''), styles), r'\end{pppbox}']
        parts += figure_parts({'Progress': 'after_progress', 'Problems': 'after_problems', 'Plans': 'after_plans'}[key])
    for i, table in enumerate(values.get('tables', [])):
        rows = table['rows']
        if not rows or not rows[0] or any(len(row) != len(rows[0]) for row in rows):
            raise ValueError('표의 모든 행은 같은 열 수여야 합니다.')
        body = ' \\\\\n'.join(' & '.join(rich_text(c) for c in row) for row in rows) + r' \\'
        parts += [r'\ReportTable{' + ' '.join(['L'] * len(rows[0])) + '}{' + body + '}{' + rich_text(table['caption']) + '}{tab:' + str(i) + '}']
    return '\n\n'.join(parts + [r'\end{document}', ''])
