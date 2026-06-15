# 株式会社KU TRUCK ＆ TYRE SERVICE — コーポレートサイト

埼玉・三郷のトラック総合会社「株式会社KU TRUCK ＆ TYRE SERVICE」（SINCE 1981）の
コーポレートサイト。**運送・整備・タイヤ＆用品販売**をワンストップで案内します。

Claude Design のハンドオフ（案C「Street Crew」/ 正式採用）を、本番用の
静的サイト（HTML / CSS / JS）として実装したものです。

## 構成

| ファイル | 内容 |
|---|---|
| `index.html` | トップページ（ヒーロー → 事業内容 → 車両構成 → 会社概要 → 採用 → お問合せ） |
| `transport.html` | 事業詳細：運送 |
| `maintenance.html` | 事業詳細：トラック整備（自社認証工場 第4-7114号） |
| `parts.html` | 事業詳細：トラック用品販売（輸入タイヤ / AdBlue / オイル） |
| `styles.css` | 共通ベース＋トップページ用スタイル（白×黒×水色 / レスポンシブ対応） |
| `svc.css` | 事業詳細ページ用スタイル |
| `app.js` | ローダー・スクロール演出（追従ナビ／パララックス）・モバイルメニュー |
| `assets/` | 写真素材（Web表示用に最適化済み） |

## デザイン

- パレット：白 `#ffffff` × 黒 `#0d0d0d` × 水色 `#40b8d0`
- 書体：Anton / Archivo Black / Space Grotesk / Zen Kaku Gothic New（Google Fonts）
- ステッカー／極太見出しの「ストリートクルー」トーン

## プロトタイプからの本番化で加えた点

- JS で後挿入していたセクションを HTML に直接インライン化（描画の安定化・SEO）
- 巨大な見出しを `clamp()` で流体化し、**スマホ〜デスクトップで破綻しないレスポンシブ**を追加
- モバイル用ハンバーガーメニュー（ドロワー＋スクリム）を新規実装
- 電話番号を `tel:` リンク化（スマホからタップ発信）
- 画像を Web 表示用に最適化（`fleet-line.jpg` 7.7MB → 約330KB など）
- `prefers-reduced-motion` への配慮、メタタグ（description / OGP）整備

## ローカルプレビュー

```bash
# このディレクトリで
python -m http.server 5189
# → http://localhost:5189
```

## 公開

GitHub Pages で配信。`main` ブランチのルートを公開ソースに設定（`.nojekyll` 同梱）。

## 今後の検討事項（未確定）

- **お問い合わせフォーム**：現状フォーム送信先（メール / フォームサービス）が未定のため、
  問い合わせ導線はすべて電話（`tel:`）に集約。フォーム化する場合は要相談。
- 独自ドメイン（例：`ku-truck.co.jp`）の割り当て。
- ヒーローは白基調。水色基調にしたい場合は `<body>` に `class="hero-cy"` を付与で切替可。

---
© 1981 — 2026 KU TRUCK ＆ TYRE SERVICE
