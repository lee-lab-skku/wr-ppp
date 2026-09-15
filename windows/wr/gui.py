from __future__ import annotations

import csv
import datetime as dt
import io
import json
import os
from pathlib import Path
import queue
import shutil
import subprocess
import tempfile
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
import uuid
from zoneinfo import ZoneInfo

from . import admin, core
from .cli import notifications


class App(ttk.Frame):
    def __init__(self, root):
        super().__init__(root, padding=16)
        self.pack(fill='both', expand=True)
        self.root = root
        self.config = core.read_config()
        self.source = None
        self.form_file = None
        self.draft = None
        self.figures = []
        self.tables = []
        self.pending_figures = {}
        self.jobs = queue.Queue()
        self.busy = False
        self.manager = None
        self.selections = {}
        root.protocol('WM_DELETE_WINDOW', self.close)
        root.title('Weekly Report · 주간 연구 보고서')
        root.geometry('1120x850')
        root.minsize(900, 700)
        style = ttk.Style()
        if 'vista' in style.theme_names():
            style.theme_use('vista')
        ttk.Label(self, text='주간 연구 보고서', font=('Malgun Gothic', 20, 'bold')).pack(anchor='w')
        ttk.Label(self, text='작성 → 미리보기 → PDF 저장     |     관리자: 선택 → 초안 검토 → 확정').pack(anchor='w', pady=(3, 12))
        tabs = ttk.Notebook(self)
        tabs.pack(fill='both', expand=True)
        self.write_tab, self.admin_tab, self.settings_tab = (ttk.Frame(tabs, padding=12) for _ in range(3))
        for frame, title in ((self.write_tab, '보고서 작성'), (self.admin_tab, '관리자 취합'), (self.settings_tab, '설정')):
            tabs.add(frame, text=title)
        self.build_writer()
        self.build_admin()
        self.build_settings()
        self.status = tk.StringVar(value='설정에서 PDF 출력 폴더와 LaTeX 도구를 확인하세요.')
        ttk.Label(self, textvariable=self.status, wraplength=1000).pack(fill='x', pady=(10, 0))
        root.after(100, self.poll)

    def close(self):
        if self.busy:
            messagebox.showinfo('작업 중', '파일 생성 작업이 끝난 뒤 창을 닫아 주세요.')
            return
        if messagebox.askyesno('종료', '저장하지 않은 편집 내용은 사라집니다. 종료할까요?'):
            self.root.destroy()

    def guarded(self, action):
        try:
            if self.busy:
                raise ValueError('현재 작업이 끝난 뒤 실행하세요.')
            return action()
        except Exception as error:
            messagebox.showerror('확인 필요', str(error), parent=self.root)

    def button(self, frame, text, action):
        button = ttk.Button(frame, text=text, command=lambda: self.guarded(action))
        button.pack(side='left', padx=(0, 6), pady=4)
        return button

    def task(self, work, done):
        if self.busy:
            return
        self.busy = True
        self.status.set('작업 중입니다… 창을 닫지 마세요.')
        def worker():
            try:
                self.jobs.put((done, work(), None))
            except Exception as error:
                self.jobs.put((done, None, str(error)))
        threading.Thread(target=worker, daemon=True).start()

    def poll(self):
        try:
            done, result, error = self.jobs.get_nowait()
            self.busy = False
            if error:
                self.status.set('작업을 완료하지 못했습니다. 오류 내용을 확인하세요.')
                messagebox.showerror('작업 실패', error, parent=self.root)
            else:
                self.status.set('작업 완료')
                self.guarded(lambda: done(result))
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def entry(self, frame, label, value=''):
        row = ttk.Frame(frame)
        row.pack(fill='x', pady=3)
        ttk.Label(row, text=label, width=16).pack(side='left')
        variable = tk.StringVar(value=value)
        ttk.Entry(row, textvariable=variable).pack(side='left', fill='x', expand=True)
        return variable

    def build_writer(self):
        bar = ttk.Frame(self.write_tab)
        bar.pack(fill='x')
        for label, action in [('새 보고서', self.new_report), ('작성 파일 열기', self.open_form),
                              ('기존 .tex 열기', self.open_tex), ('템플릿 복사', self.copy_template),
                              ('저장', self.save_report), ('Markdown → LaTeX', self.preview_latex),
                              ('PDF 생성', self.build_report)]:
            self.button(bar, label, action)
        self.writer_mode = tk.StringVar(value='입력 화면으로 작성 중')
        ttk.Label(self.write_tab, textvariable=self.writer_mode).pack(anchor='w', pady=5)
        self.fields = {k: self.entry(self.write_tab, label) for k, label in [('title', '제목'), ('author', '작성자'), ('project', '프로젝트 / 팀')]}
        row = ttk.Frame(self.write_tab)
        row.pack(fill='x')
        self.date = tk.StringVar(value=dt.date.today().isoformat())
        self.serial = tk.StringVar()
        self.here = tk.BooleanVar()
        ttk.Label(row, text='날짜').pack(side='left')
        ttk.Entry(row, textvariable=self.date, width=14).pack(side='left', padx=8)
        ttk.Label(row, text='일련번호 (빈칸: 자동)').pack(side='left')
        ttk.Entry(row, textvariable=self.serial, width=8).pack(side='left', padx=8)
        ttk.Checkbutton(row, text='원본 폴더에 PDF 저장', variable=self.here).pack(side='left')
        self.editor_tabs = ttk.Notebook(self.write_tab)
        self.editor_tabs.pack(fill='both', expand=True, pady=10)
        self.texts = {}
        for key in ('abstract', 'Progress', 'Problems', 'Plans', 'LaTeX'):
            frame = ttk.Frame(self.editor_tabs)
            self.editor_tabs.add(frame, text='요약' if key == 'abstract' else key)
            text = tk.Text(frame, wrap='word', undo=True, font=('Malgun Gothic', 11), height=12)
            scroll = ttk.Scrollbar(frame, command=text.yview)
            text.configure(yscrollcommand=scroll.set)
            scroll.pack(side='right', fill='y')
            text.pack(fill='both', expand=True)
            self.texts[key] = text
        attachments = ttk.Frame(self.write_tab)
        attachments.pack(fill='x')
        self.button(attachments, '그림 추가', self.add_figure)
        self.button(attachments, '표 추가 (CSV)', self.add_table)
        self.button(attachments, '첨부 목록 / 삭제', self.manage_attachments)
        ttk.Label(self.write_tab, text='2페이지가 최대입니다. 초과 시 내용을 검토하며, 자동으로 자르거나 글꼴을 줄이지 않습니다.').pack(anchor='w')

    def new_report(self):
        if not messagebox.askyesno('새 보고서', '현재 편집 내용을 닫고 새 보고서를 작성할까요? 저장하지 않은 내용은 사라집니다.'):
            return
        self.source = self.form_file = None
        self.figures, self.tables, self.pending_figures = [], [], {}
        for variable in self.fields.values():
            variable.set('')
        for text in self.texts.values():
            text.delete('1.0', 'end')
        self.writer_mode.set('입력 화면으로 작성 중')
        self.editor_tabs.select(0)

    def values(self):
        return {**{k: v.get() for k, v in self.fields.items()},
                **{k: self.texts[k].get('1.0', 'end-1c') for k in ('abstract', 'Progress', 'Problems', 'Plans')},
                'figures': self.figures, 'tables': self.tables}

    def open_form(self):
        name = filedialog.askopenfilename(filetypes=[('작성 데이터', '*.wr.json')])
        if not name:
            return
        values = json.loads(Path(name).read_text(encoding='utf-8'))
        self.form_file, self.source = Path(name), None
        for k, variable in self.fields.items():
            variable.set(values.get(k, ''))
        for key in ('abstract', 'Progress', 'Problems', 'Plans'):
            self.texts[key].delete('1.0', 'end')
            self.texts[key].insert('1.0', values.get(key, ''))
        self.figures, self.tables = values.get('figures', []), values.get('tables', [])
        self.pending_figures = {}
        self.writer_mode.set(str(self.form_file))
        self.editor_tabs.select(0)

    def open_tex(self):
        name = filedialog.askopenfilename(filetypes=[('LaTeX', '*.tex')])
        if name:
            source = Path(name)
            contents = source.read_text(encoding='utf-8-sig')
            if not contents.strip():
                raise ValueError(
                    '선택한 .tex 파일이 비어 있습니다(0바이트). 다른 원본이나 백업 파일을 선택하세요.'
                )
            self.source, self.form_file = source, None
            self.texts['LaTeX'].delete('1.0', 'end')
            self.texts['LaTeX'].insert('1.0', contents)
            self.writer_mode.set('원본 LaTeX 편집: ' + name + ' (입력 폼은 적용되지 않습니다)')
            self.editor_tabs.select(4)

    def copy_template(self):
        name = filedialog.asksaveasfilename(initialfile='main.tex', defaultextension='.tex')
        if name:
            core.atomic_write(name, (core.ROOT / 'template.tex').read_bytes())
            self.source, self.form_file = Path(name), None
            self.texts['LaTeX'].delete('1.0', 'end')
            self.texts['LaTeX'].insert('1.0', self.source.read_text(encoding='utf-8'))
            self.writer_mode.set('원본 LaTeX 편집: ' + name)
            self.editor_tabs.select(4)

    def save_report(self):
        if self.source:
            contents = self.texts['LaTeX'].get('1.0', 'end-1c')
            if not contents.strip():
                raise ValueError('빈 내용으로 기존 .tex 파일을 덮어쓸 수 없습니다.')
            core.atomic_write(self.source, contents)
            return self.source
        if not self.form_file:
            name = filedialog.asksaveasfilename(initialfile='report.wr.json', defaultextension='.wr.json', filetypes=[('작성 데이터', '*.wr.json')])
            if not name:
                return None
            self.form_file = Path(name)
        for relative, file in self.pending_figures.items():
            target = self.form_file.parent / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, target)
        self.pending_figures.clear()
        values = self.values()
        # Form-generated sources have their own name and never overwrite an existing main.tex.
        source = self.form_file.with_suffix('.tex')
        core.atomic_write(source, core.form_source(values, self.config.get('allow_user_styles', False)))
        core.atomic_write(self.form_file, json.dumps(values, ensure_ascii=False, indent=2))
        self.writer_mode.set(str(self.form_file))
        self.status.set('저장했습니다: ' + str(source))
        return source

    def preview_latex(self):
        if self.source:
            raise ValueError('기존 .tex 편집 모드에서는 이미 LaTeX 원본을 편집하고 있습니다.')
        generated = core.form_source(self.values(), self.config.get('allow_user_styles', False))
        self.texts['LaTeX'].delete('1.0', 'end')
        self.texts['LaTeX'].insert('1.0', generated)
        self.editor_tabs.select(4)
        self.status.set('Markdown을 LaTeX로 변환했습니다. 저장·PDF 생성 때도 자동으로 다시 변환됩니다.')

    def add_figure(self):
        if self.source:
            raise ValueError('원본 편집 모드에서는 LaTeX의 ReportFigure 명령을 사용하세요.')
        name = filedialog.askopenfilename(filetypes=[('그림', '*.png *.jpg *.jpeg *.pdf')])
        if not name:
            return
        window = tk.Toplevel(self.root)
        window.title('그림 추가')
        window.transient(self.root)
        window.grab_set()
        caption = self.entry(window, '그림 설명')
        ttk.Label(window, text='삽입 위치').pack(anchor='w', padx=8, pady=(10, 2))
        labels = {'Abstract와 Progress 사이': 'after_abstract', 'Progress와 Problems 사이': 'after_progress',
                  'Problems와 Plans 사이': 'after_problems', 'Plans 뒤': 'after_plans'}
        position = tk.StringVar(value='Plans 뒤')
        ttk.Combobox(window, textvariable=position, values=list(labels), state='readonly', width=34).pack(fill='x', padx=8)
        def add():
            identity = uuid.uuid4().hex
            relative = 'figures/' + identity + Path(name).suffix.lower()
            self.pending_figures[relative] = Path(name)
            self.figures.append({'file': relative, 'caption': caption.get(), 'id': identity,
                                 'position': labels[position.get()]})
            window.destroy()
            self.status.set('그림을 추가했습니다: ' + position.get())
        buttons = ttk.Frame(window)
        buttons.pack(fill='x', padx=8, pady=12)
        ttk.Button(buttons, text='추가', command=lambda: self.guarded(add)).pack(side='left')
        ttk.Button(buttons, text='취소', command=window.destroy).pack(side='left', padx=6)

    def add_table(self):
        if self.source:
            raise ValueError('원본 편집 모드에서는 LaTeX의 ReportTable 명령을 사용하세요.')
        text = simpledialog.askstring('표', 'CSV 행을 입력하세요 (행 구분은 ;). 예: 항목,점수;기준,71.4;개선,73.7')
        if not text:
            return
        rows = list(csv.reader(io.StringIO(text.replace(';', '\n'))))
        if not rows or any(len(r) != len(rows[0]) for r in rows):
            raise ValueError('각 행의 열 수가 같아야 합니다.')
        caption = simpledialog.askstring('표', '표 설명:')
        if caption is not None:
            self.tables.append({'rows': rows, 'caption': caption})

    def manage_attachments(self):
        window = tk.Toplevel(self.root)
        window.title('첨부 목록')
        listing = tk.Listbox(window, width=70)
        listing.pack(fill='both', expand=True)
        def refresh():
            listing.delete(0, 'end')
            for item in self.figures:
                positions = {'after_abstract': 'Abstract 뒤', 'after_progress': 'Progress 뒤',
                             'after_problems': 'Problems 뒤', 'after_plans': 'Plans 뒤'}
                listing.insert('end', '그림: ' + item['caption'] + ' · ' + positions.get(item.get('position', 'after_plans'), 'Plans 뒤'))
            for item in self.tables:
                listing.insert('end', '표: ' + item['caption'])
        def remove():
            if listing.curselection():
                index = listing.curselection()[0]
                if index < len(self.figures):
                    item = self.figures.pop(index)
                    self.pending_figures.pop(item['file'], None)
                else:
                    self.tables.pop(index-len(self.figures))
                refresh()
        ttk.Button(window, text='선택 삭제', command=remove).pack()
        refresh()

    def build_report(self):
        source = self.save_report()
        if not source:
            return
        date, serial, here = self.date.get(), self.serial.get() or None, self.here.get()
        core.metadata(date)
        def done(result):
            self.status.set(f'PDF 저장 완료 · {result["pages"]}페이지 · {result["pdf"]}')
            if result['pages'] > 2:
                messagebox.showwarning('분량 검토', f'{result["pages"]}페이지입니다. 2페이지 제한과 불가피한 예외 사유를 검토하세요.')
            os.startfile(result['pdf'])
        self.task(lambda: core.build_report(source, self.config.copy(), date, serial, here), done)

    def build_settings(self):
        self.settings = {}
        for key, label in [('pdf_output', '개인 PDF 출력'), ('tex_bin', 'LaTeX bin 폴더'),
                           ('admin_output', '최종 합본 출력'), ('admin_data', '관리자 데이터')]:
            self.settings[key] = self.entry(self.settings_tab, label, self.config.get(key, ''))
            chooser = ttk.Frame(self.settings_tab)
            chooser.pack(fill='x')
            self.button(chooser, label + ' 선택', lambda k=key: self.choose_directory(k))
        self.allow_user_styles = tk.BooleanVar(value=bool(self.config.get('allow_user_styles', False)))
        ttk.Checkbutton(
            self.settings_tab,
            text='사용자 Markdown 스타일 허용 (잠금 해제)',
            variable=self.allow_user_styles,
        ).pack(anchor='w', pady=(12, 0))
        ttk.Label(
            self.settings_tab,
            text='꺼짐: 기존 보고서 템플릿 서식 사용 · 켜짐: <style>의 여백·글자 크기·표 스타일 적용',
        ).pack(anchor='w')
        bar = ttk.Frame(self.settings_tab)
        bar.pack(fill='x', pady=15)
        self.button(bar, '설정 저장', self.save_settings)
        self.button(bar, '실행 환경 검사', lambda: self.task(lambda: core.preflight(self.config), lambda r: messagebox.showinfo('실행 환경', json.dumps(r, ensure_ascii=False, indent=2))))
        self.button(bar, 'Slack 연결 설정', self.configure_slack)
        more = ttk.Frame(self.settings_tab)
        more.pack(fill='x')
        self.button(more, 'LaTeX 도구 준비', self.install_tex)
        self.button(more, 'AI 스킬 등록', self.install_skills)
        ttk.Label(self.settings_tab, text='Windows용 TeX Live의 bin/windows 폴더를 지정하세요.\n기존 Docker 설정은 변경하지 않습니다.\n로컬 TeX 실행은 shell escape를 차단하지만 Docker와 같은 격리 환경은 아닙니다.', wraplength=900).pack(anchor='w', pady=15)

    def install_tex(self):
        if not messagebox.askyesno('LaTeX 도구 준비', 'TinyTeX와 보고서에 필요한 패키지를 다운로드합니다. 인터넷과 충분한 디스크 공간이 필요합니다. 진행할까요?'):
            return
        directory = core.STATE_ROOT / '.runtime'
        def work():
            result = subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
                                     str(core.ROOT / 'windows/install-tex.ps1'), '-InstallRoot', str(directory)],
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0), timeout=3600)
            if result.returncode:
                raise ValueError(result.stdout.decode('utf-8', errors='replace')[-10000:])
            return str(directory / 'TinyTeX/bin/windows')
        def done(path):
            self.settings['tex_bin'].set(path)
            self.save_settings()
            self.status.set('LaTeX 도구가 준비되었습니다.')
        self.task(work, done)

    def install_skills(self):
        from .skills import install
        window = tk.Toplevel(self.root)
        window.title('AI 스킬 등록')
        services = {name: tk.BooleanVar(value=name == 'agents') for name in ('agents', 'claude')}
        for name, variable in services.items():
            ttk.Checkbutton(window, text=name, variable=variable).pack(anchor='w', padx=20, pady=5)
        administrator = tk.BooleanVar(value=True)
        replace = tk.BooleanVar()
        ttk.Checkbutton(window, text='관리자 스킬 포함', variable=administrator).pack(anchor='w', padx=20)
        ttk.Checkbutton(window, text='충돌한 파일/링크는 백업 후 교체 (디렉터리 제외)', variable=replace).pack(anchor='w', padx=20)
        def register():
            result = install([name for name, value in services.items() if value.get()], administrator.get(), replace.get())
            messagebox.showinfo('등록 완료', json.dumps(result, ensure_ascii=False, indent=2))
            window.destroy()
        ttk.Button(window, text='등록', command=lambda: self.guarded(register)).pack(pady=15)

    def choose_directory(self, key):
        value = filedialog.askdirectory()
        if value:
            self.settings[key].set(value)

    def save_settings(self):
        config = {k: v.get().strip() for k, v in self.settings.items()}
        config['allow_user_styles'] = self.allow_user_styles.get()
        core.save_config(config)
        self.config = config
        self.draft = None
        self.status.set('설정을 저장했습니다.')

    def configure_slack(self):
        value = simpledialog.askstring('Slack 연결', 'Incoming Webhook URL (설정만 저장하며 발송하지 않습니다):', show='*')
        if value:
            notifications().validate_webhook(value)
            core.atomic_write(admin.paths(self.config)[1].parent / 'slack-webhook.url', value + '\n')
            self.status.set('Slack 연결을 저장했습니다. 메시지는 보내지 않았습니다.')

    def build_admin(self):
        bar = ttk.Frame(self.admin_tab)
        bar.pack(fill='x')
        for label, action in [('구성원 설정', self.edit_manager), ('보고서 검색', self.search_reports),
                              ('PDF 확인', self.inspect_selected), ('초안 생성', self.create_draft),
                              ('검토 후 확정', self.promote), ('보류 / Slack', self.hold)]:
            self.button(bar, label, action)
        self.admin_date = self.entry(self.admin_tab, '취합 날짜', dt.date.today().isoformat())
        self.roster = ttk.Treeview(self.admin_tab, columns=('name', 'required', 'file'), show='headings', height=12)
        for key, text in [('name', '구성원'), ('required', '필수 제출'), ('file', '선택 PDF (더블클릭하여 선택)')]:
            self.roster.heading(key, text=text)
        self.roster.column('name', width=130)
        self.roster.column('required', width=80)
        self.roster.column('file', width=620)
        self.roster.pack(fill='both', expand=True, pady=10)
        self.roster.bind('<Double-1>', lambda e: self.guarded(self.choose_candidate))
        self.admin_log = tk.Text(self.admin_tab, height=9, wrap='word', font=('Malgun Gothic', 10))
        self.admin_log.pack(fill='both', expand=True)
        ttk.Label(self.admin_tab, text='보고서의 작성자·기간·최종 버전을 확인하고 선택하세요. 수정 시각만으로 자동 선택하지 않습니다.').pack(anchor='w', pady=5)

    def edit_manager(self):
        try:
            manager = admin.load_manager(self.config)
        except FileNotFoundError:
            manager = {'schema': 1, 'storage_root': '', 'timezone': 'Asia/Seoul', 'members': []}
        window = tk.Toplevel(self.root)
        window.title('구성원 설정')
        window.geometry('920x650')
        rootvar = self.entry(window, '보고서 저장소', manager['storage_root'])
        def choose():
            path = filedialog.askdirectory(parent=window)
            if path:
                rootvar.set(path)
        ttk.Button(window, text='저장소 선택', command=choose).pack()
        zonevar = self.entry(window, '시간대', manager['timezone'])
        members = {m['id']: dict(m) for m in manager['members']}
        listing = ttk.Treeview(window, columns=('name', 'order', 'required', 'folders'), show='headings', height=8)
        for key, label in [('name', '이름'), ('order', '표시 순서'), ('required', '필수 제출'), ('folders', '검색 폴더')]:
            listing.heading(key, text=label)
        listing.pack(fill='both', expand=True, padx=10, pady=10)
        namevar = self.entry(window, '구성원 이름')
        ordervar = self.entry(window, '표시 순서', str(max((m['order'] for m in members.values()), default=0) + 1))
        requiredvar = tk.BooleanVar(value=True)
        ttk.Checkbutton(window, text='매주 제출이 필요한 구성원', variable=requiredvar).pack(anchor='w', padx=20)
        ttk.Label(window, text='검색 폴더 (저장소 내부 상대 경로, 한 줄에 하나)').pack(anchor='w', padx=20)
        folders = tk.Text(window, height=3)
        folders.pack(fill='x', padx=20)
        selected = [None]
        def refresh():
            listing.delete(*listing.get_children())
            for m in sorted(members.values(), key=lambda x: x['order']):
                listing.insert('', 'end', iid=m['id'], values=(m['display_name'], m['order'], '필수' if m['required'] else '선택', ', '.join(m['search_roots'])))
        def load_member(event=None):
            if not listing.selection():
                return
            selected[0] = listing.selection()[0]
            member = members[selected[0]]
            namevar.set(member['display_name'])
            ordervar.set(str(member['order']))
            requiredvar.set(member['required'])
            folders.delete('1.0', 'end')
            folders.insert('1.0', '\n'.join(member['search_roots']))
        listing.bind('<<TreeviewSelect>>', load_member)
        def clear():
            selected[0] = None
            listing.selection_remove(*listing.selection())
            namevar.set('')
            ordervar.set(str(max((m['order'] for m in members.values()), default=0) + 1))
            requiredvar.set(True)
            folders.delete('1.0', 'end')
        def browse_folder():
            if not rootvar.get():
                raise ValueError('먼저 보고서 저장소를 선택하세요.')
            value = filedialog.askdirectory(parent=window, initialdir=rootvar.get())
            if value:
                relative = Path(value).resolve().relative_to(Path(rootvar.get()).resolve())
                folders.insert('end', str(relative) + '\n')
        def update_member():
            mid = selected[0] or 'member-' + uuid.uuid4().hex[:10]
            updated = {'id': mid, 'display_name': namevar.get().strip(), 'order': int(ordervar.get()),
                       'required': requiredvar.get(), 'search_roots': folders.get('1.0', 'end-1c').splitlines()}
            proposed = dict(members)
            proposed[mid] = updated
            admin.validate_manager({'schema': 1, 'storage_root': rootvar.get(), 'timezone': zonevar.get(), 'members': list(proposed.values())}, self.config)
            members[mid] = updated
            refresh()
            clear()
        def remove_member():
            if selected[0] and messagebox.askyesno('구성원 삭제', '이 구성원을 현재 명단에서 제외할까요? 기존 PDF와 이력은 삭제하지 않습니다.', parent=window):
                members.pop(selected[0])
                refresh()
                clear()
        actions = ttk.Frame(window)
        actions.pack(fill='x', padx=20)
        for label, action in [('검색 폴더 선택', browse_folder), ('구성원 추가 / 반영', update_member), ('새 구성원', clear), ('선택 구성원 제외', remove_member)]:
            self.button(actions, label, action)
        refresh()
        def save():
            admin.save_manager({'schema': 1, 'storage_root': rootvar.get(), 'timezone': zonevar.get(), 'members': list(members.values())}, self.config)
            self.draft = None
            window.destroy()
        ttk.Button(window, text='저장', command=lambda: self.guarded(save)).pack(pady=10)

    def search_reports(self):
        self.manager = admin.load_manager(self.config)
        self.admin_date.set(dt.datetime.now(ZoneInfo(self.manager['timezone'])).date().isoformat())
        def done(candidates):
            self.candidates = candidates
            self.selections = {}
            self.draft = None
            self.roster.delete(*self.roster.get_children())
            for m in sorted(self.manager['members'], key=lambda m: m['order']):
                self.roster.insert('', 'end', iid=m['id'], values=(m['display_name'], '필수' if m['required'] else '선택', f'미선택 · 후보 {len(candidates[m["id"]])}개'))
            self.admin_log.delete('1.0', 'end')
            self.admin_log.insert('1.0', '구성원을 더블클릭하여 후보를 선택하세요. PDF 확인 버튼으로 내용과 페이지 수를 검사할 수 있습니다.')
        self.task(lambda: admin.discover(self.manager), done)

    def choose_candidate(self):
        if not self.roster.selection():
            return
        mid = self.roster.selection()[0]
        window = tk.Toplevel(self.root)
        window.title('보고서 선택')
        listing = tk.Listbox(window, width=120, height=16)
        listing.pack(fill='both', expand=True)
        listing.insert('end', '(미선택 / 누락)')
        for file in self.candidates[mid]:
            listing.insert('end', str(file))
        def choose():
            if not listing.curselection():
                return
            index = listing.curselection()[0]
            self.selections[mid] = str(self.candidates[mid][index-1]) if index else None
            values = list(self.roster.item(mid, 'values'))
            values[2] = self.selections[mid] or '미선택'
            self.roster.item(mid, values=values)
            self.draft = None
            window.destroy()
        ttk.Button(window, text='선택', command=choose).pack(pady=5)

    def inspect_selected(self):
        if not self.roster.selection():
            return
        file = self.selections.get(self.roster.selection()[0])
        if not file:
            raise ValueError('먼저 PDF를 선택하세요.')
        def done(info):
            self.admin_log.delete('1.0', 'end')
            self.admin_log.insert('1.0', f'{info["pages"]}페이지 · SHA256 {info["sha256"]}\n\n' + info['text'])
            os.startfile(file)
        self.task(lambda: core.probe(self.manager['storage_root'], file), done)

    def create_draft(self):
        if not self.manager:
            raise ValueError('구성원을 설정하고 보고서를 검색하세요.')
        date, selections, config = self.admin_date.get(), self.selections.copy(), self.config.copy()
        manager = self.manager
        core.metadata(date)
        def work():
            plan = admin.make_plan(manager, selections, config, date)
            result = admin.build_bundle(plan, manager['storage_root'], config, date, draft=True)
            return result, plan, date, selections, config
        def done(value):
            self.draft = value
            result = value[0]
            self.admin_log.delete('1.0', 'end')
            self.admin_log.insert('1.0', result['pdf'] + '\n\n' + '\n'.join(' · '.join(r[1:]) for r in result['issues']))
            os.startfile(result['pdf'])
        self.task(work, done)

    def promote(self):
        if not self.draft:
            raise ValueError('먼저 초안을 생성하고 검토하세요.')
        result, plan, date, selections, config = self.draft
        if date != self.admin_date.get() or selections != self.selections or config != self.config:
            raise ValueError('날짜·선택·설정이 바뀌었습니다. 초안을 다시 생성하세요.')
        details = '\n'.join(' · '.join(r[1:]) for r in result['issues']) or '기록된 문제 없음'
        if not messagebox.askyesno('합본 최종 확정', details + '\n\n초안 PDF와 선택 보고서를 검토했으며 이 내용으로 최종 저장할까요?'):
            return
        def done(value):
            self.draft = None
            self.status.set('최종 합본 저장: ' + value['pdf'])
            os.startfile(value['pdf'])
        self.task(lambda: admin.build_bundle(plan, self.manager['storage_root'], config, date,
                                            approved=True, review=result['review']), done)

    def hold(self):
        if not self.draft:
            raise ValueError('먼저 초안을 생성하세요.')
        result = self.draft[0]
        if self.draft[2] != self.admin_date.get() or self.draft[3] != self.selections or self.draft[4] != self.config:
            raise ValueError('날짜·선택·설정이 바뀌었습니다. 초안을 다시 생성하세요.')
        module = notifications()
        payload, fingerprint = module.notice(Path(result['manifest']))
        preview = payload['blocks'][0]['text']['text']
        if not messagebox.askyesno('취합 보류 및 Slack 발송', preview + '\n\n취합을 보류하고 설정된 Slack 채널에 이 알림을 보낼까요?'):
            return
        self.task(lambda: module.send(admin.paths(self.config)[1].parent, payload, fingerprint),
                  lambda _: self.status.set('보류 알림 처리를 완료했습니다. 합본은 확정하지 않았습니다.'))


def run():
    root = tk.Tk()
    App(root)
    root.mainloop()
