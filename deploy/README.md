# 本番（Xserver: https://shinko-ghd.jp/kutt/）への配置

1. `dist/` を最新化（GitHub Pages前提の絶対URLを置換済み・不要アセット除外済み）
2. PowerShell で（実行するとパスワードを伏せ字で聞く）:
   ```

   .\deploy\upload_kutt.ps1
   ```
   FTPS（明示的TLS）で `sv14321.xserver.jp` に `kutt@shinko-ghd.jp` としてアップロード。
   ※ FTPユーザーのホームディレクトリが `/kutt` 相当のはず。もし `https://shinko-ghd.jp/kutt/kutt/` に上がってしまう/403のままなら
     `$Remote` を `/kutt/` に変えて再実行。
3. 確認: https://shinko-ghd.jp/kutt/ と /adblue.html

DBは使わない（静的サイト＋GASフォーム）。phpMyAdmin のDBは空のままでよい。
