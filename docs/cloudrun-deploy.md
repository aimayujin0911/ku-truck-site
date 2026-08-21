# Cloud Run へのデプロイ（ロジコム様HPと同じ環境）

静的サイトの配信と**お問い合わせフォームの受信**を1つのコンテナで行う。
サーバー側で受けられるので **外部フォームサービス（FormSubmit等）は不要**。

- 構成: `Dockerfile` + `server/app.py`（FastAPI）+ リポジトリ直下の静的ファイル
- 環境: GCP `picker-405518` / asia-northeast1（ロジコム様の `hakopro-site-logicom` と同じ）
- ステージング: Cloud Run サービス **`ku-truck-site-staging`**

## エンドポイント

| メソッド | パス | 内容 |
|---|---|---|
| GET | `/` `/{page}.html` | サイト本体（index/transport/maintenance/parts/message/thanks のみ許可、他は404） |
| GET | `/styles.css` `/svc.css` `/app.js` `/assets/*` | 静的アセット |
| POST | `/contact` | フォーム受信 → 検証 → 通知 → `/thanks.html` へ303 |
| GET | `/health` | 稼働確認（通知の有効/無効も表示） |

`GET` でHTMLを返すときに、GitHub Pages用に書かれているフォームの
`action="https://formsubmit.co/contact-ku@shinko-ghd.jp"` を `action="/contact"` に置換する。
**1つのHTMLをPages（外部サービス）とCloud Run（自前API）の両方で使い回せる。**

## フォーム受信の仕様

- 必須: お名前 / メールアドレス（形式チェック）/ お問い合わせ内容（5文字以上）→ 不足は400
- スパム対策: 隠しフィールド `_honey` に入力があれば**記録せず**サンクスへ（ボットには成功に見せる）
- レート制限: 同一IPから既定5件/10分（`RATE_LIMIT_PER_10MIN`）。**入力ミスの400はカウントしない**
- **通知が全部失敗しても、内容は必ず構造化ログ（jsonPayload `event=contact_submission`）に残す**
  → ロジコム様HPで起きた「どこにも記録が残らない」事故の再発防止
- 受信内容には氏名・連絡先が含まれる。Cloud Logging の既定保持は30日（必要なら保持期間・
  ログルーティングを別途設計する）

### 通知の有効化（環境変数）

| 変数 | 用途 |
|---|---|
| `CONTACT_TO` | 通知先メール（カンマ区切り可） |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASS` / `SMTP_FROM` | 送信経路（SES SMTP等）。Cloud Runは25番不可なので587/465を使う |
| `SLACK_WEBHOOK_URL` | Slack通知（メールと併用可） |
| `RATE_LIMIT_PER_10MIN` | 既定5 |

未設定なら通知はスキップされ、ログにだけ残る（`/health` に `mail=off slack=off` と出る）。

## ローカル起動

```bash
cd ku-truck-site
SITE_DIR=$(pwd) python -m uvicorn server.app:app --host 127.0.0.1 --port 8099
```

## ビルドとデプロイ

`gcloud` の認証が切れている場合は ADC トークンを使う:

```bash
export CLOUDSDK_AUTH_ACCESS_TOKEN=$(gcloud auth application-default print-access-token)
```

```bash
gcloud builds submit --tag gcr.io/picker-405518/ku-truck-site:v1 --project=picker-405518
```

```bash
gcloud run deploy ku-truck-site-staging \
  --image=gcr.io/picker-405518/ku-truck-site:v1 \
  --project=picker-405518 --region=asia-northeast1 --allow-unauthenticated \
  --memory=512Mi --cpu=1 --min-instances=0 --max-instances=3
```

通知を有効にする場合（例）:

```bash
gcloud run services update ku-truck-site-staging --project=picker-405518 --region=asia-northeast1 \
  --set-env-vars=CONTACT_TO=contact-ku@shinko-ghd.jp,SMTP_HOST=email-smtp.ap-northeast-1.amazonaws.com,SMTP_PORT=587,SMTP_FROM=no-reply@li-go.jp \
  --set-secrets=SMTP_USER=ku-smtp-user:latest,SMTP_PASS=ku-smtp-pass:latest
```

## 受信内容の確認（メールが止まっても失われない）

```bash
gcloud logging read 'resource.type="cloud_run_revision"
  AND resource.labels.service_name="ku-truck-site-staging"
  AND jsonPayload.event="contact_submission"' --project=picker-405518 --limit=20 --format=json
```

## 本番切替時の残作業

1. **独自ドメイン**（例 ku-truck.co.jp）の取得とCloud Runへのマッピング — 未着手
2. 通知先（メール or Slack）の確定と認証情報のSecret Manager登録
3. GitHub Pages を残すか停止するかの判断（残す場合はフォームの二重運用を避けるため、
   Pages側のフォームは非表示にするのが安全）
