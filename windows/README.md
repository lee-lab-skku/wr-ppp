# Windows native edition

Docker, WSL, Bash 없이 실행하는 추가 구현입니다. 기존 Linux/macOS 스크립트와 템플릿은 유지합니다.

## 일반 사용자 설치

GitHub Releases에서 `WeeklyReport-0.1.0-Setup.exe`를 다운로드하여 실행합니다.
바탕화면 바로가기 옵션을 유지하고 설치한 뒤 **Weekly Report** 아이콘으로 실행합니다.
Python과 TinyTeX가 포함되어 별도 설치가 필요 없습니다. Windows 10/11 x64용이며 현재 사용자 계정에 설치됩니다.
Windows 설정의 설치된 앱에서 제거할 수 있습니다. 사용자 설정과 작성한 보고서는 보존됩니다.
설치 파일에는 아직 코드 서명이 없습니다.

## 소스 코드에서 실행

1. Windows용 Python 3.11 이상을 설치합니다. Tcl/Tk, pip, Python launcher를 포함하세요.
2. 저장소의 `Windows-Setup.cmd`를 실행합니다. 프로젝트 안에 가상환경과 PDF 처리 패키지를 설치합니다.
3. Windows용 TeX Live를 설치하거나, 앱 설정의 **LaTeX 도구 준비** 버튼으로 프로젝트 전용 TinyTeX를 준비합니다. 기존 설치나 시스템 PATH는 변경하지 않습니다.
4. `Start-Weekly-Report.cmd`를 더블클릭합니다.
5. 설정에서 개인 PDF 출력 폴더와 TeX Live `bin/windows` 폴더를 선택하고 저장합니다.

현재 개발 PC의 MSYS Python 가상환경도 런처가 지원합니다. 일반 배포 패키지는 python.org CPython으로 만드세요.

## 작성

입력 화면에서 제목·이름·프로젝트·요약·PPP를 작성합니다. 그림과 CSV 표를 추가할 수 있습니다. 그림을 추가할 때 Abstract 뒤, Progress 뒤, Problems 뒤, Plans 뒤 중 삽입 위치를 선택합니다. 이전 버전에서 저장한 위치 정보 없는 그림은 Plans 뒤에 배치됩니다. 저장 시 `.wr.json`과 생성된 `.wr.tex`가 만들어집니다. 그림은 상대 경로의 `figures` 폴더에 복사됩니다. 보고서마다 별도 폴더를 사용하세요. 폴더명이 PDF 이름이 됩니다.

일반 문장 안의 수식은 `$a+b$`, 별도 줄의 수식은 `$$E=mc^2$$`처럼 입력합니다. 수식 밖의 `%`, `&`, `_` 같은 문자는 자동 처리됩니다. 닫히지 않은 수식과 파일·문서 조작 명령은 저장 단계에서 거절됩니다.

요약·Progress·Problems·Plans 입력창은 Markdown을 지원합니다. `## 소제목`은 기존 양식의 번호 있는 소제목, `- 항목`은 글머리표, `1. 항목`은 번호 목록, `**굵게**`, `*기울임*`, `` `코드` ``, `[이름](https://주소)`는 해당 LaTeX 표현으로 바뀝니다. **Markdown → LaTeX** 버튼을 누르면 결과를 LaTeX 탭에서 확인할 수 있습니다. 저장과 PDF 생성 때도 같은 변환을 자동 적용합니다. 원본 LaTeX 명령을 Markdown 입력창에 직접 넣으면 문자로 처리됩니다.

Markdown 제목의 숫자는 자동으로 생성하지 않습니다. `# 1.1 제목`처럼 사용자가 입력한 번호만 표시됩니다. `<style>...</style>`은 기본적으로 제거하고 기존 LaTeX 템플릿 서식을 적용합니다. 나중에 설정의 **사용자 Markdown 스타일 허용 (잠금 해제)**을 켜면 제한된 CSS를 LaTeX 설정으로 변환합니다. 잠금 해제 시 `@page`의 A4 여백, `body`의 글자 크기·줄 간격, `h1`~`h3`의 크기·줄 간격·여백, `p`의 문단 간격, `table`과 `th, td`의 크기·여백·셀 간격을 지원합니다. 파이프 표는 스타일 잠금 상태와 관계없이 LaTeX 표로 변환합니다. Markdown 이미지 경로는 자동으로 파일을 가져오지 못하므로 변환 결과에 첨부 필요 표시를 남기며, 실제 파일은 **그림 추가**로 선택합니다.

입력창 위의 서식 도구막대에서 글꼴(기본·명조·고딕·고정폭), 8–16pt 크기, 굵게, 기울임, 밑줄, 취소선, 코드, 링크, 불릿, 번호 목록과 3단계 소제목을 적용할 수 있습니다. 글자 서식은 한 문단 안의 텍스트를 선택한 뒤 적용합니다. 서식 표시는 작성 데이터에 함께 저장되고 기존 LaTeX 템플릿 안에서 변환됩니다.

기존 `.tex`는 원본 편집 모드로 열 수 있습니다. 주석과 사용자 정의 코드를 유지합니다. 임의의 LaTeX를 폼으로 역변환하지 않으며, 원본 편집 모드에서는 폼 값이 적용되지 않습니다. 그림·표는 폼에서 PPP 뒤에 배치되므로 자유로운 배치는 원본 모드를 사용하세요.

날짜·일련번호·현재 폴더 저장 옵션을 지원합니다. 2페이지 초과는 경고하며 페이지나 내용을 자르지 않습니다. Windows 환경에서 생성하는 폼 소스에는 `kotex`를 추가합니다. 기존 소스에는 자동으로 패키지를 삽입하지 않습니다.

## 관리자

설정에서 최종 합본 출력과 선택적 관리자 데이터 폴더를 지정합니다. 구성원 설정에서 저장소·시간대와 구성원 ID, 이름, 순서, 필수 여부, 상대 검색 폴더를 입력합니다. NAS/UNC 경로는 현재 사용자에게 접근 권한이 있어야 합니다.

보고서를 검색한 뒤 구성원을 더블클릭하여 후보를 명시적으로 선택합니다. PDF 확인으로 내용과 페이지 수를 검토합니다. 수정 시각만으로 자동 선택하지 않습니다. **초안 생성 → PDF 및 문제 확인 → 검토 후 확정** 순서로 진행합니다. 초안 이후 계획이나 파일 내용이 바뀌면 확정이 거절됩니다.

기존 TOML 구성원 설정과 `admin-wr-plan/v1`, `admin-wr-bundle/v1` TSV 형식을 지원합니다. 기존 Linux 절대 경로는 Windows 경로로 직접 다시 지정해야 합니다. 파일을 자동 이동하지 않습니다. 이력은 외부 설정 위치, 저장소 로컬, 기존 최종 출력의 순서로 누락 파일에만 fallback합니다. 손상되거나 해시가 다른 이력은 우회하지 않고 검토 대상으로 표시합니다.

표지는 기존 LaTeX 자산으로 생성하며 전체 이력을 유지합니다. 한 페이지에 들어가지 않으면 실패합니다. 원본 PDF는 pypdf로 모든 페이지와 페이지 크기를 유지하여 합칩니다. 과거 상태는 포함/예외/필수 누락/선택 미포함/불명으로 구분합니다.

Slack 기능은 기존 Python 구현을 재사용합니다. 설정은 발송하지 않습니다. 필수 누락이 있는 초안에서 보류와 발송을 확인한 경우에만 보냅니다. 성공 중복 방지 및 불확실한 실패의 자동 재시도 금지를 유지합니다. Webhook은 관리자 데이터 폴더의 `slack-webhook.url`에 저장되므로 해당 폴더는 본인 또는 허가된 관리자만 읽을 수 있도록 Windows/NAS 접근 권한을 설정하세요.

## CLI / 기존 AI 워크플로 연결

```powershell
.\.venv\Scripts\python.exe windows\weekly_report.py setup --pdf-output C:\Reports --tex-bin C:\texlive\2026\bin\windows
.\.venv\Scripts\python.exe windows\weekly_report.py preflight
.\.venv\Scripts\python.exe windows\weekly_report.py report-build C:\Sources\W1\main.tex --date 2026-09-04 --serial 17 --here
.\.venv\Scripts\python.exe windows\weekly_report.py test
.\.venv\Scripts\python.exe windows\weekly_report.py report-metadata --date 2026-09-04
.\.venv\Scripts\python.exe windows\weekly_report.py admin-paths
.\.venv\Scripts\python.exe windows\weekly_report.py discover
.\.venv\Scripts\python.exe windows\weekly_report.py probe-report --storage-root C:\Reports --file C:\Reports\member-a\report.pdf
.\.venv\Scripts\python.exe windows\weekly_report.py build-bundle --storage-root C:\Reports --plan C:\Review\plan.tsv --date 2026-09-04 --draft --output-dir C:\Review\draft
.\.venv\Scripts\python.exe windows\weekly_report.py build-bundle --storage-root C:\Reports --plan C:\Review\plan.tsv --date 2026-09-04 --approved-with-issues --review C:\Review\draft\2026-09-W1.review.json
.\.venv\Scripts\python.exe windows\weekly_report.py notify-held --manifest C:\Review\draft\.manifests\2026-09-W1.manifest.tsv
```

Windows에서는 기존 스킬의 셸 명령을 위의 동명 하위 명령으로 대체하여 사용합니다. 작성·근거 검토·후보 판단은 기존 스킬의 정책대로 외부 AI 에이전트가 수행하며 앱 내부 AI API는 추가하지 않았습니다. 설정의 **AI 스킬 등록** 또는 `install-skills --services agents,claude --admin`으로 기존 스킬의 링크를 등록합니다. Windows 개발자 모드 또는 심볼릭 링크 권한이 필요합니다. 충돌 항목은 기본적으로 보존하며, `--replace-existing`은 파일/링크만 인접 백업 후 교체합니다. 디렉터리는 교체하지 않습니다. 등록 중 실패하면 링크 변경을 되돌립니다.

## 일반 사용자 설치

GitHub Releases에서 `WeeklyReport-0.1.0-Setup.exe`를 다운로드하여 실행합니다.
바탕화면 바로가기 옵션을 유지하고 설치한 뒤 **Weekly Report** 아이콘으로 실행합니다.
Python과 TinyTeX가 포함되어 별도 설치가 필요 없습니다. Windows 10/11 x64용이며 현재 사용자 계정에 설치됩니다.
Windows 설정의 설치된 앱에서 제거할 수 있습니다. 사용자 설정과 작성한 보고서는 보존됩니다.
설치 파일에는 아직 코드 서명이 없습니다.

## 소스 코드에서 실행·저장 차이

- `.windows-config.json`을 사용하며 Bash `.local-config`는 실행하거나 덮어쓰지 않습니다. 패키징된 앱 설정은 `%LOCALAPPDATA%/WeeklyReport/config.json`에 저장합니다. `WR_CONFIG`로 테스트용 경로를 지정할 수 있습니다.
- `latexmk` 대신 XeLaTeX를 참조 정보가 안정될 때까지 최대 5회 실행합니다. Perl은 필요하지 않습니다. BibTeX/Biber 등 별도 사용자 빌드 단계는 자동 실행하지 않습니다.
- 임시 사본에서 실행하고 shell escape를 끕니다. 이것은 Docker의 OS/네트워크 격리와 동등하지 않습니다. 기존의 격리 보장이 필요한 신뢰할 수 없는 소스는 기존 Docker 실행 경로를 사용하세요.
- 빌드 실패 시 기존 PDF를 유지합니다. 기존 스크립트의 빌드 전 로컬 PDF 삭제를 성공 후 정리로 변경하여 실패 시 원본 결과도 보존합니다.
- PDF와 이력 파일은 각각 원자적으로 교체하지만 한 트랜잭션은 아닙니다. 중간 중단은 다음 이력 조회의 해시 검증으로 확인합니다.
- GUI는 항상 초안을 먼저 검토합니다. CLI는 문제가 없는 명시적 계획에 대해 기존처럼 바로 최종 생성도 가능합니다.

## 테스트 / 배포

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s windows\tests -v
powershell -File windows\package.ps1
```

PyInstaller는 Python과 GUI 의존성을 포함한 `windows/dist/WeeklyReport/WeeklyReport.exe`와 명령용 `WeeklyReportCLI.exe`를 만듭니다. **전체 폴더**를 배포해야 합니다. `package.ps1 -IncludeTeX`는 준비된 `.runtime/TinyTeX`까지 `tex` 폴더에 포함하여 오프라인 실행이 가능한 배포 폴더를 만듭니다. 앱은 이 폴더의 도구를 자동 탐색합니다. 기본 패키지는 앱에서 LaTeX 도구 준비 버튼을 사용하거나 별도 설치가 필요합니다. 설치 마법사는 아래 명령으로 별도 생성합니다.

일반 자동 테스트는 실제 PDF 파일의 검사·병합과 업무 규칙을 검증하며, LaTeX 실행은 대체합니다. 실제 출력 검증은 별도로 `python windows/tests/real_build.py`를 실행합니다. `self-test --output <절대경로.json>`은 배포 EXE의 GUI 생성·리소스·PDF 라이브러리 로딩을 숨김 상태로 검사합니다. 기존 POSIX 셸 테스트는 native Windows에서 명시적으로 건너뛰고, Slack 공통 테스트는 실행합니다. Linux 동작은 POSIX 환경에서 별도 검증해야 합니다.

## 설치 파일 만들기

Inno Setup 6과 Python 빌드 환경, `.runtime/TinyTeX`가 필요합니다.

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File windows/build-installer.ps1 -Version 0.1.0
```

`-Compiler`로 ISCC.exe 경로를 지정할 수 있습니다. 검증된 최신 오프라인 배포 폴더가 이미 있으면 `-SkipPackage`로 포장만 수행합니다.
결과는 `windows/dist/installer/WeeklyReport-0.1.0-Setup.exe`와 SHA256 파일입니다.
소스 코드는 Git에 커밋하고, 설치 파일과 SHA256 파일은 GitHub Releases에 첨부합니다. `windows/dist`는 Git 추적에서 제외됩니다.

설치 파일 생성 전 `sanitize-bundle.py`가 배포 폴더에서 개발 PC의 TeX 로그·글꼴 캐시를 제거하고, 생성된 설정의 경로를 정리합니다. `-SkipPackage` 사용 시에도 `-Python`에 빌드용 Python 경로를 지정할 수 있습니다.
