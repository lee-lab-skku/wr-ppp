# Slack 검토 문제 알림

검토 단계에서 확인한 문제를 **메시지별 관리자 승인 후** 지정한 Slack 채널에 알립니다.
취합 보류 결정은 필요하지 않으며, 알림 발송 승인은 취합본 발행 승인과 별개입니다.
대상은 필수 제출 누락, 최종본 후보 모호성, PDF 손상·암호화·검사 불가, 2페이지 초과, 내부 주차 불일치입니다.
검토 중인 초안 실행 TSV를 근거로 사용하며, 최종 발행 기록이나 선택 제출 누락·최초 실행·이력 문제만 있는 기록은 알림 대상이 아닙니다.
PDF 첨부나 로컬 경로 전송 없이 주차, 보고 기간, 구성원 이름, 문제 유형, 설명과 요청 조치를 보냅니다.
이 기능은 Python 3가 필요하며 추가 Python 패키지는 필요하지 않습니다.

## Slack에서 한 번 설정하기

Incoming Webhook은 프로그램이 특정 채널에 메시지를 보낼 수 있는 전용 URL입니다.
별도 수신 서버를 운영할 필요가 없습니다.

1. [Slack 앱 관리 페이지](https://api.slack.com/apps)에서 앱을 만들고 사용할 워크스페이스를 선택합니다.
1. 앱 설정의 **Incoming Webhooks**에서 **Activate Incoming Webhooks**를 켭니다.
1. **Add New Webhook to Workspace**를 누르고 알림을 받을 채널을 선택해 허용합니다.
1. 생성된 Webhook URL을 복사합니다.
   워크스페이스에서 앱 설치를 제한하면 워크스페이스 관리자의 승인이 필요할 수 있습니다.

버튼과 설정 흐름은 [Slack 공식 안내](https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks/)를 참고하세요.
Webhook URL은 해당 채널에 글을 쓸 수 있는 비밀값이므로 채팅에 붙여 넣거나 Git에 커밋하지 마세요.

## URL 저장하기

Windows에서는 스킬 진입점에서 확인한 `Start-Weekly-Report.ps1` 또는 `WeeklyReportCLI.exe`의 절대 경로에 `notify-issues --configure`를 전달합니다. 아래 `scripts/notify-issues` 예시는 Linux/macOS 전용입니다.

레포 디렉터리의 터미널에서 실행합니다.

```bash
scripts/notify-issues --configure
```

숨김 입력 프롬프트에 URL을 붙여 넣고 Enter를 누릅니다.
이 명령은 URL만 저장하고 메시지를 보내지 않습니다.
다시 실행하면 기존 URL을 교체할 수 있습니다.

`--admin-data`를 설정했다면 `<admin-data>/slack-webhook.url`, 생략했다면 `<repository>/.admin-wr/slack-webhook.url`에 저장합니다.
NAS에 저장할 때는 공유 권한으로 이 파일을 보호하세요.
실행 이력의 로컬 재탐색과 달리 Webhook 파일은 설정된 위치에서만 읽습니다.
설정 파일이 없을 때 다른 채널의 로컬 URL로 발송되는 것을 방지하기 위한 구분입니다.

## 메시지 작성과 승인 후 발송

Windows에서는 아래 `scripts/notify-issues` 호출을 확인한 Windows 런처의 `notify-issues` 하위 명령으로 바꾸고 Windows 절대 경로를 사용합니다.
먼저 실제 취합 초안의 실행 TSV로 기본 메시지를 확인합니다.
미리보기는 네트워크 요청을 하지 않으며 Webhook 설정도 읽지 않습니다.

```bash
scripts/notify-issues --manifest /tmp/admin-review/.manifests/2026-09-W2.manifest.tsv
```

미리보기 JSON의 `payload`가 전송할 메시지이며 `approval`은 해당 메시지를 식별하는 지문입니다.
알림 예시:

```text
주간보고 검토 중 확인된 문제 · 2026-09-W2
보고 기간: 2026-09-07 ~ 2026-09-13

검토 중 다음 문제가 확인되었습니다.

구성원 가
• 2페이지 초과 (3페이지)
  요청: 분량을 줄이거나 필수 내용 보존을 위한 예외 사유를 관리자와 확인해 주세요.
• 내부 주차 불일치
  요청: 보고서의 주차 표기를 확인해 주세요.

요청 사항을 확인하고 관리자에게 알려 주세요.
```

### 에이전트가 문구 작성하기

에이전트는 도입·마무리 문장과 문제별 설명·요청 조치를 자유롭게 작성할 수 있습니다.
주차·기간·이름·문제 유형과 페이지 수는 프로그램이 기록에서 확정합니다.
설명은 확인한 근거에 한정하고, 필요성 예외나 정상 대체본이 있다면 이를 반영한 조치를 요청합니다.
기본 문구 역시 검토하여 상황에 맞게 수정하세요.
원문 이슈 설명을 그대로 복사하지 말고, 경로·URL·비밀값·불필요한 내부 정보를 제외하세요.
프로그램은 URL과 일반적인 절대 경로 표기를 거부하지만, 자유 문구의 사실성과 정보 공개 범위는 에이전트와 관리자가 확인해야 합니다.

다음 JSON을 임시 파일에 저장하고 `--message /tmp/admin-message.json`을 전달합니다.
`items`에는 알림 대상인 모든 구성원·문제 조합을 정확히 한 번씩 넣습니다.

```json
{
  "introduction": "이번 주 보고서 검토 결과를 안내합니다.",
  "closing": "확인 후 관리자에게 알려 주세요.",
  "items": [
    {
      "member_id": "member-a",
      "code": "overlength-report",
      "description": "3페이지 보고서입니다. 필수 근거 보존을 위한 예외 사유를 확인하고 있습니다.",
      "action": "축약 가능 부분이나 분량 예외가 필요한 이유를 확인해 주세요."
    },
    {
      "member_id": "member-a",
      "code": "internal-week-mismatch",
      "description": "대상 기간의 보고서로 판단했으나 내부 주차 표기가 다릅니다.",
      "action": "주차 표기를 확인해 주세요."
    }
  ]
}
```

지원 코드는 `missing-report`, `ambiguous-report`, `unreadable-pdf`, `overlength-report`, `internal-week-mismatch`입니다.
필수 누락은 구성원 상태에서도 수집하며, 다른 유형은 실행 기록의 명시된 이슈를 사용합니다.
정상 대체 PDF를 선택했더라도 기록된 PDF 검사 실패는 안내할 수 있습니다.
선택 제출자의 실제 PDF 문제도 대상이지만, 선택 제출자의 단순 미제출은 제외합니다.
동일 구성원·유형의 중복 이슈는 한 항목으로 합칩니다.
알 수 없는 구성원, 누락·추가·중복된 메시지 항목, 근거와 맞지 않는 분량 초과는 거부합니다.

### 발송 승인

대상 채널과 미리보기의 **전체 메시지**를 관리자에게 제시하고 해당 메시지 발송에 대한 명시적인 승인을 받습니다.
채널 연결 승인이나 과거 알림 조건의 지속 승인은 이 메시지 발송 승인이 아닙니다.
승인한 미리보기의 `approval` 값을 사용합니다.

```bash
scripts/notify-issues --manifest /tmp/admin-review/.manifests/2026-09-W2.manifest.tsv --message /tmp/admin-message.json
scripts/notify-issues --manifest /tmp/admin-review/.manifests/2026-09-W2.manifest.tsv --message /tmp/admin-message.json --approved <approval-fingerprint> --send
```

`<approval-fingerprint>`는 실제 미리보기 값으로 교체하세요.
지문은 사람의 승인을 대신하지 않으며, 에이전트가 승인 없이 미리보기 값을 사용해서는 안 됩니다.
발송 시 메시지를 다시 생성하여 승인 지문과 비교하므로 이름·문제·문구가 달라지면 다시 검토하고 승인받아야 합니다.
구성원별 plain-text 블록으로 메시지를 표시하며, Slack 한도를 넘으면 내용을 생략하지 않고 오류를 냅니다.
알림 결과를 관리자에게 보고하고 기존 취합 검토 상태를 유지합니다.
개발용 모의 실행과 실제 시험 메시지 발송은 별도로 명시적인 요청이 있어야 합니다.

### 기존 보류 명령 호환

`notify-held`는 기존 사용법을 유지하는 호환 alias입니다.
`notify-held --manifest ...`로 미리보고 `notify-held --manifest ... --held --send`로 기존의 필수 제출 누락 보류 알림을 보냅니다.
이 경로는 실제 보류 결정과 기존 대상 채널·누락 보류 알림에 대한 권한을 요구하며, 추가 문제 유형을 발송할 권한으로 해석하지 않습니다.
기존 발송 기록과 Windows 보류 버튼도 계속 이 동작을 사용합니다.
새 검토 문제 알림에는 `notify-issues`를 사용하세요.

## 중복과 실패 처리

새 알림은 같은 주차·구성원별 문제 집합·최종 메시지·Webhook 목적지로 성공한 경우 반복 발송하지 않습니다.
문제나 전송 문구가 달라지면 새 메시지로 검토하고 승인받습니다.
이슈 기록 순서나 비전송 설명 변경만으로 재발송하지 않습니다.
기존 alias는 주차·필수 누락자 ID 집합·Webhook 기반의 기존 중복 방지 기록을 계속 사용합니다.
발송 기록은 Webhook 파일 옆의 `notifications/`에 저장하며 URL 자체는 기록하지 않습니다.

전송 오류나 중단이 발생하면 자동 재시도하지 않고 잠금 디렉터리를 유지합니다.
이미 Slack에 도착했지만 응답만 받지 못했을 수 있으므로 먼저 채널을 확인합니다.
도착했다면 해당 `.lock`과 같은 이름의 `.sent` 파일에 `sent`를 기록한 뒤 잠금 디렉터리를 제거합니다.
도착하지 않았음을 확인했으면 잠금을 제거하고 명시적으로 다시 발송합니다.
실행 중인 전송의 잠금을 제거하지 마세요.
Webhook URL이 만료되거나 채널 설정이 바뀌었다면 Slack 설정에서 확인한 뒤 `--configure`로 갱신합니다.
