# Windows implementation validation

## PowerShell 리팩토링 검증 (2026-09-15)

현재 리팩토링의 검증 결과이며, 아래의 이전 구현 기록과 구분합니다.
환경: Windows 11 x64, Windows PowerShell 5.1, CPython 3.13.7, pypdf 6.18.0, PyInstaller 6.21.0.

- Windows 테스트 57개 통과: 업무 로직 55개와 실제 PowerShell 프로세스 테스트 2개.
- 공통 Slack 테스트 9개 통과, POSIX 전용 클래스와 모듈은 Windows에서 명시적으로 건너뜀.
- WSL Ubuntu 24.04에서 공통/POSIX 테스트 85개 통과. Windows Git의 링크 대체 파일 대신 Git 모드에 맞춘 심볼릭 링크와 실행 권한을 보존한 동일 소스 사본을 사용.
- PowerShell: 별도 작업 폴더, 한글·공백·대괄호·앰퍼샌드 경로, 반복 설치, 비 Windows 가상환경 보존, 빈 인수·따옴표·끝 백슬래시·UNC 문자열 전달, `WR_CONFIG`와 종료 코드 보존 확인.
- 설정 사전 검증과 잘못된 저장 경로 복구, 스킬 별칭 중복 제거와 동시 사용자 수정 보호, 발행 잠금·대기 후 원본 재검증·PDF/기록 사이 중단 감지 확인.
- 기존 `C:\texlive\2026` 설치로 영문 템플릿 2페이지, 한글 폼 1페이지, 관리자 초안/확정 합본 실제 빌드. 템플릿 두 페이지, 한글 폼, 합본 표지를 PNG로 렌더링해 확인.
- Windows Docker의 `danteev/texlive:latest`에서도 같은 템플릿·스타일과 메타데이터를 사용해 A4 2페이지 빌드 확인. 네트워크 차단, 소스 읽기 전용 마운트와 임시 작업 공간을 사용.
- 숨김 Tk GUI의 입력·저장 검사, GUI/CLI EXE 패키징과 EXE 자체 검사, 번들 버전 파일 확인.

이번에는 프로젝트용 TinyTeX와 Inno Setup이 준비되지 않아 TinyTeX 신규 설치, `-IncludeTeX` 오프라인 실행, 설치 프로그램 생성·설치·제거를 재검증하지 않았습니다.
Python 자체에 TinyTeX가 포함되는 것은 아니며, 오프라인 설치본은 별도로 준비한 TinyTeX를 패키징할 때 함께 포함합니다.
PowerShell 7, 실제 UNC/NAS 접근·ACL, macOS, 외부 AI 서비스의 링크 탐색과 실제 Slack 발송은 검증하지 않았습니다.
WSL 배포판의 Docker Desktop 통합이 꺼져 있어 해당 배포판에서 실제 Docker 빌드는 실행되지 않았습니다.

## 이전 구현의 검증 기록

검증 환경: Windows 11 x64, Python 3.14.7 (MinGW), PyInstaller 6.21.0, pypdf 6.18.0, Windows TinyTeX/TeX Live 2026.

## 확인한 범위

- Windows 공통 모듈 자동 테스트: 월/연도 경계 주차 계산, 일반 문장 특수문자 처리와 `$...$`/`$$...$$` 수식 보존, PDF 검사·암호화 거절, 경로 범위, 일련번호, 실패 시 출력 보존, 구성원 설정, 후보 선택, 전체 페이지·크기 보존, 이력 해시 검증, 초안과 최종 출력 분리, 원본 내용/수정 시각 변경 시 승인 무효화, 저장 위치 충돌, 스킬 등록 충돌/롤백, Slack 중복 방지.
- 기존 Slack 공통 테스트 8개 통과. 실발송 없이 전송 모듈을 대체하여 검증.
- 기존 POSIX 셸 테스트 26개는 Windows에서 건너뜀. 기존 셸 구현 자체는 변경하지 않았으며 Linux/macOS 실행 검증을 대신하지 않음.
- Tk 작성 화면 생성·한글 입력·작성 파일 저장 검증.
- PyInstaller GUI/CLI 실행 파일 생성 및 EXE의 숨김 GUI·PDF 라이브러리·템플릿 로딩 자체 검사.
- 개발용 Python, MSYS, 기존 TeX를 `PATH`에서 제외한 상태에서 오프라인 배포 폴더의 `WeeklyReportCLI.exe`와 포함된 `tex` 폴더만으로 실행 환경 검사와 한글 PDF 생성.
- 기존 영문 `template.tex`의 실제 Windows XeLaTeX 빌드: 2페이지.
- 폼에서 생성한 한글·특수문자·표·PNG 그림 보고서의 실제 빌드: 1페이지.
- 실제 관리자 표지 + 원본 PDF 취합, 이전 주 이력과 이번 주 누락 상태 표시, 초안 → 검토 기록 → 최종 생성.
- 위 PDF의 페이지를 PNG로 렌더링하여 글자, 표, 그림과 합본 표지 확인.

## 별도 환경에서 확인할 범위

- 실제 NAS의 연결·ACL·동시 사용자 접근.
- 실제 Slack 채널 발송 및 외부 AI 서비스의 스킬 자동 탐색.
- 다른 Windows PC/Windows ARM 및 코드 서명.
- 임의의 사용자 LaTeX 확장, BibTeX/Biber·사용자 latexmk 설정에 의존하는 별도 빌드 단계.

로컬 네이티브 빌드는 임시 사본과 shell escape 차단을 사용하지만 Docker의 OS·네트워크 격리와 동일하지 않습니다. Docker 실행 경로는 유지합니다. 기존 스킬의 근거 판단·작성 정책을 유지하며 앱 내부 AI API는 추가하지 않았습니다.

실제 빌드 검증 코드는 `tests/real_build.py`, 시각 검증 보조 코드는 `tests/render_qa.py`입니다. 생성된 검증용 보고서는 실제 연구 결과가 아닌 명시적인 테스트 자료입니다.

## 설치 패키지 검증 (2026-09-14)

- Inno Setup 6.7.3으로 `WeeklyReport-0.1.0-Setup.exe` 생성: 527,593,901 bytes. SHA256 파일도 생성.
- 현재 소스로 PyInstaller 배포본 재생성. Windows 단위 테스트 46개 통과.
- 현재 사용자 계정에 설치 성공. 바탕화면 바로가기 대상 경로, 시작 메뉴 바로가기, 제거 프로그램 및 Windows 제거 등록 확인.
- 설치된 EXE의 자체 검사로 GUI 생성, PDF 라이브러리, 템플릿 리소스 로딩 확인.
- 개발용 Python/TeX를 PATH에서 제외하고 설치된 EXE와 번들 TinyTeX로 실제 PDF 생성 성공.
- 설치본은 이 PC에 유지. 다른 PC 검증, 제거 실행 및 코드 서명은 수행하지 않음.
