# -*- coding: utf-8 -*-
"""KU TRUCK ＆ TYRE SERVICE サイト配信 + お問い合わせ受信（Cloud Run）。

- 静的サイト（リポジトリ直下のHTML/CSS/JS/assets）をそのまま配信する
- `POST /contact` でフォームを自前で受け取る（外部フォームサービス不要）
  受信 → 検証（必須/形式/ハニーポット/レート制限） → 通知 → /thanks.html へリダイレクト

通知は環境変数で有効化する。**どの通知が失敗しても必ず構造化ログに残す**ので、
問い合わせが「どこにも記録されない」状態を作らない（ロジコム様HPで起きた事故の再発防止）。

| 環境変数 | 用途 |
|---|---|
| CONTACT_TO | 通知先メール（カンマ区切り可） |
| SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / SMTP_FROM | メール送信経路（SES SMTP等） |
| SLACK_WEBHOOK_URL | Slack通知（任意・メールと併用可） |
| RATE_LIMIT_PER_10MIN | 同一IPからの上限（既定5） |
"""
import json
import os
import re
import smtplib
import ssl
import threading
import time
from collections import defaultdict, deque
from email.message import EmailMessage
from email.utils import formataddr

import sys

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

SITE_DIR = os.environ.get("SITE_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
CONTACT_TO = [a.strip() for a in os.environ.get("CONTACT_TO", "").split(",") if a.strip()]
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "no-reply@li-go.jp")
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "")
RATE_LIMIT = int(os.environ.get("RATE_LIMIT_PER_10MIN", "5"))

PAGES = {"index", "transport", "maintenance", "parts", "message", "thanks", "adblue"}
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# ログは常にUTF-8で出す（Windowsローカル実行でcp932に落ちて壊れるのを防ぐ）
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

app = FastAPI(title="ku-truck-site")
_hits: dict = defaultdict(deque)
_lock = threading.Lock()


def _log(event: str, **kw) -> None:
    """Cloud Logging に残る構造化ログ（jsonPayload）。通知が全部失敗しても内容は残る。"""
    print(json.dumps({"event": event, **kw}, ensure_ascii=False), flush=True)


def _rate_limited(ip: str) -> bool:
    now = time.time()
    with _lock:
        q = _hits[ip]
        while q and now - q[0] > 600:
            q.popleft()
        if len(q) >= RATE_LIMIT:
            return True
        q.append(now)
        return False


def _send_mail(subject: str, body: str, reply_to: str) -> str:
    if not (SMTP_HOST and CONTACT_TO):
        return "skipped(no smtp/to)"
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = formataddr(("KU公式サイト", SMTP_FROM))
    msg["To"] = ", ".join(CONTACT_TO)
    if reply_to:
        msg["Reply-To"] = reply_to
    msg.set_content(body)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
            s.starttls(context=ssl.create_default_context())
            if SMTP_USER:
                s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        return "sent"
    except Exception as e:  # 送信失敗でも受付は成功させる（内容はログに残る）
        return f"error:{type(e).__name__}:{e}"


def _notify_slack(text: str) -> str:
    if not SLACK_WEBHOOK_URL:
        return "skipped(no webhook)"
    try:
        r = httpx.post(SLACK_WEBHOOK_URL, json={"text": text}, timeout=10)
        return f"status:{r.status_code}"
    except Exception as e:
        return f"error:{type(e).__name__}"


@app.post("/contact")
async def contact(request: Request):
    """フォームのフィールド名は日本語（メール本文の見出しになる）。
    pydanticの命名制約を避けるため、生のフォームデータから直接読む。"""
    form = await request.form()
    g = lambda k: (form.get(k) or "").strip()
    name, company, tel = g("お名前"), g("会社名"), g("電話番号")
    email, kind, message = g("メールアドレス"), g("お問い合わせ種別"), g("お問い合わせ内容")
    honey = g("_honey")

    ip = (request.headers.get("x-forwarded-for", "") or (request.client.host if request.client else "")).split(",")[0].strip()
    ua = request.headers.get("user-agent", "")[:200]

    if honey:  # ボットのみが埋める隠しフィールド
        _log("contact_rejected", reason="honeypot", ip=ip, ua=ua)
        return RedirectResponse("/thanks.html", status_code=303)
    errors = []
    if not name:
        errors.append("お名前")
    if not EMAIL_RE.match(email):
        errors.append("メールアドレス")
    if len(message) < 5:
        errors.append("お問い合わせ内容")
    if errors:
        _log("contact_invalid", fields=errors, ip=ip)
        return HTMLResponse(
            "<meta charset='utf-8'><p>入力内容をご確認ください（"
            + " / ".join(errors)
            + "）。<a href='/index.html#contact'>フォームに戻る</a></p>",
            status_code=400,
        )

    # 入力ミス(400)は数えず、検証を通った送信だけを制限対象にする
    if _rate_limited(ip):
        _log("contact_rejected", reason="rate_limit", ip=ip, ua=ua)
        return PlainTextResponse("しばらく時間をおいて再度お試しください。", status_code=429)

    payload = {"name": name, "company": company, "tel": tel, "email": email,
               "type": kind, "message": message, "ip": ip, "ua": ua}
    lines = [
        "KU公式サイトのお問い合わせフォームから送信がありました。", "",
        f"■ 種別: {kind}",
        f"■ お名前: {name}",
        f"■ 会社名: {company}",
        f"■ 電話番号: {tel}",
        f"■ メール: {email}",
        "", "■ 内容:", message, "", "---", f"送信元IP: {ip}",
    ]
    body = chr(10).join(lines)
    mail = _send_mail(f"【KU公式サイト】お問い合わせ（{kind or '種別なし'}）", body, email)
    slack = _notify_slack("*KU公式サイト お問い合わせ*" + chr(10) + body)
    # 通知の成否に関わらず内容をログに残す＝取りこぼしゼロ
    _log("contact_submission", mail=mail, slack=slack, **payload)
    return RedirectResponse("/thanks.html", status_code=303)


@app.get("/health", response_class=PlainTextResponse)
def health():
    return f"ok site={SITE_DIR} mail={'on' if (SMTP_HOST and CONTACT_TO) else 'off'} slack={'on' if SLACK_WEBHOOK_URL else 'off'}"


def _html(name: str) -> HTMLResponse:
    path = os.path.join(SITE_DIR, f"{name}.html")
    with open(path, encoding="utf-8") as f:
        html = f.read()
    # 静的ホスティング用の外部フォームサービス指定を、この環境の自前エンドポイントに差し替える
    html = html.replace("https://formsubmit.co/contact-ku@shinko-ghd.jp", "/contact")
    # 外部サービスを経由しない環境なので、その注記も落とす
    html = html.replace("フォーム送信には外部サービス（FormSubmit）を利用します。", "")
    return HTMLResponse(html, headers={"Cache-Control": "public, max-age=60"})


@app.get("/", response_class=HTMLResponse)
def home():
    return _html("index")


@app.get("/{page}.html", response_class=HTMLResponse)
def page(page: str):
    if page not in PAGES:
        return PlainTextResponse("not found", status_code=404)
    return _html(page)


for _f, _mt in (("styles.css", "text/css"), ("svc.css", "text/css"), ("app.js", "text/javascript")):
    def _make(fname=_f, mime=_mt):
        def _serve():
            return FileResponse(os.path.join(SITE_DIR, fname), media_type=mime,
                                headers={"Cache-Control": "public, max-age=300"})
        return _serve
    app.add_api_route(f"/{_f}", _make(), methods=["GET"])

app.mount("/assets", StaticFiles(directory=os.path.join(SITE_DIR, "assets")), name="assets")
