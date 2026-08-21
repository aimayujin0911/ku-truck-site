# KU TRUCK ＆ TYRE SERVICE — 静的サイト配信 + お問い合わせ受信API（Cloud Run）
FROM python:3.12-slim
WORKDIR /srv
COPY server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# サイト本体（HTML/CSS/JS/assets）とサーバー
COPY *.html styles.css svc.css app.js ./
COPY assets ./assets
COPY server ./server
ENV PORT=8080 SITE_DIR=/srv PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1
CMD exec uvicorn server.app:app --host 0.0.0.0 --port ${PORT}
