# Windows native edition

Docker, WSL, Bash 없이 실행하는 추가 구현입니다. 기존 Linux/macOS 스크립트와 템플릿은 유지합니다.

## 일반 사용자 설치

GitHub Releases에 Windows 설치 파일이 첨부된 릴리스에서 `WeeklyReport-<버전>-Setup.exe`를 다운로드하여 실행합니다.
바탕화면 바로가기 옵션을 유지하고 설치한 뒤 **Weekly Report** 아이콘으로 실행합니다.
Python과 TinyTeX가 포함되어 별도 설치가 필요 없습니다. Windows 10/11 x64용이며 현재 사용자 계정에 설치됩니다.
Windows 설정의 설치된 앱에서 제거할 수 있습니다. 사용자 설정과 작성한 보고서는 보존됩니다.
설치 파일에는 아직 코드 서명이 없습니다.

## 소스 코드에서 실행

Windows PowerShell 5.1 이상 또는 PowerShell 7, Windows용 Python 3.11 이상(Tcl/Tk, pip, venv 포함)이 필요합니다.
저장소 루트에서 다음을 실행합니다.

```powershell
.\Windows-Setup.ps1
.\windows\install-tex.ps1
.\Start-Weekly-Report.ps1
```

Python launcher를 사용할 수 없으면 `Windows-Setup.ps1 -Python 'C:\Python313\python.exe'`처럼 지정합니다.
설치는 저장소 `.venv`를 만들거나 재사용하며 입력 대기 없이 종료합니다.
기존 비 Windows 가상환경은 보존하고 오류를 내므로 먼저 이름을 바꾸고 다시 실행하세요.
TinyTeX는 Python에 포함되는 패키지가 아니라 별도로 준비하는 TeX 배포판입니다.
`install-tex.ps1`은 프로젝트 `.runtime/TinyTeX`에 설치하며, 기존 Windows TeX Live가 있다면 이 단계를 생략하고 앱 설정에 `bin/windows` 경로를 지정할 수 있습니다.
시스템 PATH와 다른 TeX 설치는 변경하지 않습니다.

기존 `Windows-Setup.cmd`와 `Start-Weekly-Report.cmd`는 제거되었습니다.
소스 사용자는 같은 이름의 `.ps1`로 전환하세요.
설치 EXE와 바탕화면 바로가기는 PowerShell 런처 없이 직접 실행됩니다.
실행 정책이 스크립트를 차단하면 해당 호출에만 `powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\Windows-Setup.ps1` 형식을 사용하세요.

`Start-Weekly-Report.ps1`은 저장소 가상환경을 사용하며, 인수가 없으면 GUI를 엽니다.
인수를 주면 기존 Python CLI로 그대로 전달하고 종료 코드와 stdout/stderr를 보존합니다.
다른 작업 폴더에서 절대 경로로 호출해도 동작하며 상대 입력 경로는 호출한 폴더 기준입니다.
기존 `WR_CONFIG` 환경 변수는 덮어쓰지 않습니다.

## 작성

입력 화면에서 제목·이름·프로젝트·요약·PPP를 작성합니다. 그림과 CSV 표를 추가할 수 있습니다. 그림을 추가할 때 Abstract 뒤, Progress 뒤, Problems 뒤, Plans 뒤 중 삽입 위치를 선택합니다. 이전 버전에서 저장한 위치 정보 없는 그림은 Plans 뒤에 배치됩니다. 저장 시 `.wr.json`과 생성된 `.wr.tex`가 만들어집니다. 그림은 상대 경로의 `figures` 폴더에 복사됩니다. 보고서마다 별도 폴더를 사용하세요. 폴더명이 PDF 이름이 됩니다.

일반 문장 안의 수식은 `$a+b$`, 별도 줄의 수식은 `$$E=mc^2$$`처럼 입력합니다. 수식 밖의 `%`, `&`, `_` 같은 문자는 자동 처리됩니다. 닫히지 않은 수식과 파일·문서 조작 명령은 저장 단계에서 거절됩니다.

요약·Progress·Problems·Plans 입력창은 Markdown을 지원합니다. `## 소제목`은 번호 없는 소제목, `- 항목`은 글머리표, `1. 항목`은 번호 목록, `**굵게**`, `*기울임*`, `` `코드` ``, `[이름](https://주소)`는 해당 LaTeX 표현으로 바뀝니다. **Markdown → LaTeX** 버튼을 누르면 결과를 LaTeX 탭에서 확인할 수 있습니다. 저장과 PDF 생성 때도 같은 변환을 자동 적용합니다. 원본 LaTeX 명령을 Markdown 입력창에 직접 넣으면 문자로 처리됩니다.

Markdown 제목의 숫자는 자동으로 생성하지 않습니다. `# 1.1 제목`처럼 사용자가 입력한 번호만 표시됩니다. `<style>...</style>`은 기본적으로 제거하고 기존 LaTeX 템플릿 서식을 적용합니다. 나중에 설정의 **사용자 Markdown 스타일 허용 (잠금 해제)**을 켜면 제한된 CSS를 LaTeX 설정으로 변환합니다. 잠금 해제 시 `@page`의 A4 여백, `body`의 글자 크기·줄 간격, `h1`~`h3`의 크기·줄 간격·여백, `p`의 문단 간격, `table`과 `th, td`의 크기·여백·셀 간격을 지원합니다. 파이프 표는 스타일 잠금 상태와 관계없이 LaTeX 표로 변환합니다. Markdown 이미지 경로는 자동으로 파일을 가져오지 못하므로 변환 결과에 첨부 필요 표시를 남기며, 실제 파일은 **그림 추가**로 선택합니다.

입력창 위의 서식 도구막대에서 글꼴(기본·명조·고딕·고정폭), 8–16pt 크기, 굵게, 기울임, 밑줄, 취소선, 코드, 링크, 불릿, 번호 목록과 3단계 소제목을 적용할 수 있습니다. 글자 서식은 한 문단 안의 텍스트를 선택한 뒤 적용합니다. 서식 표시는 작성 데이터에 함께 저장되고 기존 LaTeX 템플릿 안에서 변환됩니다.

기존 `.tex`는 원본 편집 모드로 열 수 있습니다. 주석과 사용자 정의 코드를 유지합니다. 임의의 LaTeX를 폼으로 역변환하지 않으며, 원본 편집 모드에서는 폼 값이 적용되지 않습니다. 그림은 폼에서 삽입 위치를 고를 수 있고 표는 PPP 뒤에 배치됩니다. 더 자유로운 배치는 원본 모드를 사용하세요.

날짜·일련번호·현재 폴더 저장 옵션을 지원합니다. 2페이지 초과는 경고하며 페이지나 내용을 자르지 않습니다. Windows 환경에서 생성하는 폼 소스에는 `kotex`를 추가합니다. 기존 소스에는 자동으로 패키지를 삽입하지 않습니다.

## 관리자

설정에서 최종 합본 출력과 선택적 관리자 데이터 폴더를 지정합니다. 구성원 설정에서 저장소·시간대와 구성원 ID, 이름, 순서, 필수 여부, 상대 검색 폴더를 입력합니다. NAS/UNC 경로는 현재 사용자에게 접근 권한이 있어야 합니다.

보고서를 검색한 뒤 구성원을 더블클릭하여 후보를 명시적으로 선택합니다. PDF 확인으로 내용과 페이지 수를 검토합니다. 수정 시각만으로 자동 선택하지 않습니다. **초안 생성 → PDF 및 문제 확인 → 검토 후 확정** 순서로 진행합니다. 초안 이후 계획이나 파일 내용이 바뀌면 확정이 거절됩니다.

기존 TOML 구성원 설정과 `admin-wr-plan/v1`, `admin-wr-bundle/v1` TSV 형식을 지원합니다. 기존 Linux 절대 경로는 Windows 경로로 직접 다시 지정해야 합니다. 파일을 자동 이동하지 않습니다. 이력은 외부 설정 위치, 저장소 로컬, 기존 최종 출력의 순서로 누락 파일에만 fallback합니다. 손상되거나 해시가 다른 이력은 우회하지 않고 검토 대상으로 표시합니다.

표지는 기존 LaTeX 자산으로 생성하며 전체 이력을 유지합니다. 한 페이지에 들어가지 않으면 실패합니다. 원본 PDF는 pypdf로 모든 페이지와 페이지 크기를 유지하여 합칩니다. 과거 상태는 포함/예외/필수 누락/선택 미포함/불명으로 구분합니다.

Slack 기능은 기존 Python 구현을 재사용합니다. 설정은 발송하지 않습니다. 필수 누락이 있는 초안에서 보류와 발송을 확인한 경우에만 보냅니다. 성공 중복 방지 및 불확실한 실패의 자동 재시도 금지를 유지합니다. Webhook은 관리자 데이터 폴더의 `slack-webhook.url`에 저장되므로 해당 폴더는 본인 또는 허가된 관리자만 읽을 수 있도록 Windows/NAS 접근 권한을 설정하세요.

## CLI / 기존 AI 워크플로 연결

```powershell
.\Start-Weekly-Report.ps1 setup --pdf-output C:\Reports --tex-bin C:\texlive\2026\bin\windows
.\Start-Weekly-Report.ps1 preflight
.\Start-Weekly-Report.ps1 report-build C:\Sources\W1\main.tex --date 2026-09-04 --serial 17 --here
.\Start-Weekly-Report.ps1 test
.\Start-Weekly-Report.ps1 report-metadata --date 2026-09-04
.\Start-Weekly-Report.ps1 admin-paths
.\Start-Weekly-Report.ps1 discover
.\Start-Weekly-Report.ps1 probe-report --storage-root C:\Reports --file C:\Reports\member-a\report.pdf
.\Start-Weekly-Report.ps1 build-bundle --storage-root C:\Reports --plan C:\Review\plan.tsv --date 2026-09-04 --draft --output-dir C:\Review\draft
.\Start-Weekly-Report.ps1 build-bundle --storage-root C:\Reports --plan C:\Review\plan.tsv --date 2026-09-04 --approved-with-issues --review C:\Review\draft\2026-09-W1.review.json
.\Start-Weekly-Report.ps1 notify-held --manifest C:\Review\draft\.manifests\2026-09-W1.manifest.tsv
```

Windows에서는 기존 스킬의 셸 명령을 위의 동명 하위 명령으로 대체하여 사용합니다. 작성·근거 검토·후보 판단은 기존 스킬의 정책대로 외부 AI 에이전트가 수행하며 앱 내부 AI API는 추가하지 않았습니다. 설정의 **AI 스킬 등록** 또는 `install-skills --services agents,claude,antigravity --admin`으로 기존 스킬의 링크를 등록합니다. Windows 개발자 모드 또는 심볼릭 링크 권한이 필요합니다. 충돌 항목은 기본적으로 보존하며, `--replace-existing`은 파일/링크만 인접 백업 후 교체합니다. 디렉터리는 교체하지 않습니다. 등록 중 실패하면 링크 변경을 되돌립니다.

`codex`, `gemini`, `copilot`은 `agents`의 별칭이며 동일 대상은 한 번만 설치합니다.
등록 도중 사용자가 바꾼 항목은 롤백에서 보존하고, 복원하지 못한 백업의 경로를 표시합니다.

## 소스 코드에서 실행·저장 차이

- `.windows-config.json`을 사용하며 Bash `.local-config`는 실행하거나 덮어쓰지 않습니다. 패키징된 앱 설정은 `%LOCALAPPDATA%/WeeklyReport/config.json`에 저장합니다. `WR_CONFIG`로 테스트용 경로를 지정할 수 있습니다.
- `latexmk` 대신 XeLaTeX를 참조 정보가 안정될 때까지 최대 5회 실행합니다. Perl은 필요하지 않습니다. BibTeX/Biber 등 별도 사용자 빌드 단계는 자동 실행하지 않습니다.
- 임시 사본에서 실행하고 shell escape를 끕니다. 이것은 Docker의 OS/네트워크 격리와 동등하지 않습니다. 기존의 격리 보장이 필요한 신뢰할 수 없는 소스는 기존 Docker 실행 경로를 사용하세요.
- 빌드 실패 시 기존 PDF를 유지합니다. 로컬 PDF는 새 출력이 검증되고 저장된 후 정리합니다.
- PDF와 이력 파일의 대상 경로를 모두 잠근 뒤 원본을 재검증하고 각각 원자적으로 교체하지만 한 트랜잭션은 아닙니다. 중간 중단은 다음 이력 조회의 해시 검증으로 확인합니다.
- GUI는 항상 초안을 먼저 검토합니다. CLI는 문제가 없는 명시적 계획에 대해 기존처럼 바로 최종 생성도 가능합니다.

Git 릴리스 자동 업데이트는 Linux/macOS Bash 실행 경로에서만 지원합니다.
Windows 소스는 사용자가 Git 체크아웃을 갱신하고, 설치본은 새 설치 파일로 갱신합니다.
발행 잠금이 남으면 오류에 나온 `.publish.lock/owner`의 호스트와 PID를 확인하고 해당 프로세스가 종료된 경우에만 잠금 디렉터리를 제거하세요.
다른 NAS 사용자의 활성 잠금을 지우지 마세요.

## 테스트 / 배포

```powershell
.\windows\test.ps1
.\windows\test.ps1 -RealBuild -Gui
.\windows\package.ps1 -IncludeTeX
.\windows\test.ps1 -Package
```

PyInstaller는 Python과 GUI 의존성을 포함한 `windows/dist/WeeklyReport/WeeklyReport.exe`와 명령용 `WeeklyReportCLI.exe`를 만듭니다. **전체 폴더**를 배포해야 합니다. `package.ps1 -IncludeTeX`는 준비된 `.runtime/TinyTeX`까지 `tex` 폴더에 포함하여 오프라인 실행이 가능한 배포 폴더를 만듭니다. 앱은 이 폴더의 도구를 자동 탐색합니다. 기본 패키지는 앱에서 LaTeX 도구 준비 버튼을 사용하거나 별도 설치가 필요합니다. 설치 마법사는 아래 명령으로 별도 생성합니다.

일반 자동 테스트는 실제 PDF 파일의 검사·병합과 업무 규칙을 검증하며, LaTeX 실행은 대체합니다. 실제 출력 검증은 별도로 `python windows/tests/real_build.py`를 실행합니다. `self-test --output <절대경로.json>`은 배포 EXE의 GUI 생성·리소스·PDF 라이브러리 로딩을 숨김 상태로 검사합니다. 기존 POSIX 셸 테스트는 native Windows에서 명시적으로 건너뛰고, Slack 공통 테스트는 실행합니다. Linux 동작은 POSIX 환경에서 별도 검증해야 합니다.

## 설치 파일 만들기

정식 배포는 릴리스 준비가 끝난 `vMAJOR.MINOR.PATCH` 태그를 푸시하면 GitHub Actions에서 자동으로 수행합니다.
Linux/macOS 테스트와 Windows의 실제 PDF·포터블 EXE·설치·제거 검사가 모두 성공해야 GitHub Release에 설치 EXE와 SHA256이 게시됩니다.
`-beta`와 `-rc` 태그는 사전 릴리스로 게시하며, 이미 공개된 자산은 덮어쓰지 않습니다.
태그 준비와 실패 후 재실행 절차는 [기여 가이드](../CONTRIBUTING.md#tag-driven-ci-and-windows-releases)를 따르세요.
릴리스 없이 검증하려면 GitHub Actions의 **Test and release &rightarrow; Run workflow**에서 브랜치를 선택하세요.
수동 실행도 같은 테스트와 설치 파일 빌드를 수행하고, EXE와 SHA256을 실행 페이지의 `windows-installer` 아티팩트로 7일간 보관합니다.
버전은 기존 Git 태그와 개발 커밋에서 파생되며, GitHub Release는 발행하지 않습니다.
CI는 패키지 설치와 포맷 생성이 끝난 TinyTeX를 캐시하고, 일치하는 캐시가 있으면 준비 단계를 생략합니다.
캐시를 복원해도 실제 PDF 생성과 설치 파일 검사는 매번 수행합니다.
캐시 갱신과 브랜치 간 공유 조건은 [기여 가이드](../CONTRIBUTING.md#tag-driven-ci-and-windows-releases)를 참고하세요.
아래 명령은 같은 패키징 경로를 로컬에서 실행할 때 사용합니다.

Inno Setup 6과 Python 빌드 환경, `.runtime/TinyTeX`가 필요합니다.

```powershell
.\windows\build-installer.ps1
```

`-Compiler`로 ISCC.exe 경로를 지정할 수 있습니다. 검증된 최신 오프라인 배포 폴더가 이미 있으면 `-SkipPackage`로 포장만 수행합니다.
결과는 `windows/dist/installer/WeeklyReport-<버전>-Setup.exe`와 SHA256 파일입니다.
소스 코드는 Git에 커밋하고, 설치 파일과 SHA256 파일은 GitHub Releases에 첨부합니다. `windows/dist`는 Git 추적에서 제외됩니다.

설치 파일 생성 전 `sanitize-bundle.py`가 배포 폴더에서 개발 PC의 TeX 로그·글꼴 캐시를 제거하고, 생성된 설정의 경로를 정리합니다. `-SkipPackage` 사용 시에도 `-Python`에 빌드용 Python 경로를 지정할 수 있습니다.

패키징 시 버전은 저장소 Git 태그와 체크아웃 상태에서 파생되어 번들의 `_internal/VERSION`에 저장됩니다.
개발 커밋과 미커밋 변경은 버전 접미사로 구분되며 설치 프로그램도 같은 버전을 사용합니다.
`-Version`으로 별도 앱 버전을 지정하지 않습니다.
`-SkipPackage`는 현재 소스가 아니라 기존 번들의 버전을 사용하므로 해당 번들을 먼저 검증하세요.
테스트·패키징·설치 프로그램 빌드에는 `-Python`으로 Windows Python 실행 파일을 지정할 수 있습니다.
`-Package` 검증은 개발 Python/TeX를 PATH에서 제외하고 번들 템플릿을 실제 빌드하며 환경 변수는 종료 시 복원합니다.
