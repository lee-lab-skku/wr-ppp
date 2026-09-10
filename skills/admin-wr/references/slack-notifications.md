# Slack 보류 알림

필수 보고서가 누락되어 **관리자가 취합 보류를 결정했을 때** 지정한 Slack 채널에 알립니다.
누락 발견, 초안 생성, 단순 승인 대기는 발송 조건이 아닙니다.
PDF 첨부나 로컬 경로 전송 없이 대상 주차, 보고 기간, 누락자 이름만 보냅니다.
이 기능은 Python 3가 필요하며, 추가 Python 패키지는 필요하지 않습니다.

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

레포 디렉터리의 터미널에서 실행합니다.

```bash
scripts/notify-held --configure
```

숨김 입력 프롬프트에 URL을 붙여 넣고 Enter를 누릅니다.
이 명령은 URL만 저장하고 메시지를 보내지 않습니다.
다시 실행하면 기존 URL을 교체할 수 있습니다.

`--admin-data`를 설정했다면 `<admin-data>/slack-webhook.url`, 생략했다면 `<repository>/.admin-wr/slack-webhook.url`에 저장합니다.
NAS에 저장할 때는 공유 권한으로 이 파일을 보호하세요.
실행 이력의 로컬 재탐색과 달리 Webhook 파일은 설정된 위치에서만 읽습니다.
설정 파일이 없을 때 다른 채널의 로컬 URL로 발송되는 것을 방지하기 위한 구분입니다.

## 보류 결정 후 사용하기

먼저 실제 취합 초안의 실행 TSV로 메시지를 미리 확인합니다.
다음 명령은 네트워크 요청을 하지 않습니다.

```bash
scripts/notify-held --manifest /tmp/admin-review/.manifests/2026-09-W2.manifest.tsv
```

알림 예시:

```text
주간보고 취합 보류 · 2026-09-W2
보고 기간: 2026-09-07 ~ 2026-09-13
필수 제출 누락: 2명
• 구성원 가
• 구성원 나
누락 보고서가 있어 관리자가 취합을 보류했습니다. 제출 후 관리자에게 알려 주세요.
```

관리자가 해당 채널에 대한 보류 알림을 허용하고 실제로 보류를 결정한 뒤 발송합니다.
한 번 허용한 알림 조건과 대상은 이후 작업에서도 유지하며 매번 다시 허락을 묻지 않습니다.
단, 개발용 모의 실행과 시험 메시지 발송은 별도로 명시적인 요청이 있어야 합니다.

```bash
scripts/notify-held --manifest /tmp/admin-review/.manifests/2026-09-W2.manifest.tsv --held --send
```

에이전트는 이 명령을 관리자 스킬 디렉터리의 같은 이름 링크로 실행해도 됩니다.
필수 누락자가 없는 TSV와 최종 발행 상태의 TSV는 거부합니다.
알림 결과를 관리자에게 보고하고 보류 상태를 유지합니다.
Slack 알림 성공은 취합본 발행 승인이 아닙니다.

## 중복과 실패 처리

같은 주차·누락자 ID 집합·Webhook으로 성공한 알림은 반복 발송하지 않습니다.
누락자가 달라지거나 다음 주차가 되면 새로운 알림으로 처리합니다.
발송 기록은 Webhook 파일 옆의 `notifications/`에 저장하며 URL 자체는 기록하지 않습니다.

전송 오류나 중단이 발생하면 자동 재시도하지 않고 잠금 디렉터리를 유지합니다.
이미 Slack에 도착했지만 응답만 받지 못했을 수 있으므로 먼저 채널을 확인합니다.
도착했다면 해당 `.lock`과 같은 이름의 `.sent` 파일에 `sent`를 기록한 뒤 잠금 디렉터리를 제거합니다.
도착하지 않았음을 확인했으면 잠금을 제거하고 명시적으로 다시 발송합니다.
실행 중인 전송의 잠금을 제거하지 마세요.
Webhook URL이 만료되거나 채널 설정이 바뀌었다면 Slack 설정에서 확인한 뒤 `--configure`로 갱신합니다.
