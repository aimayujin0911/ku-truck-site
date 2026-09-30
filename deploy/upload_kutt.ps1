# shinko-ghd.jp/kutt へ dist/ を FTPS でアップロードする
# 使い方（PowerShell）:  $env:KUTT_FTP_PASS = Read-Host -AsSecureString | ConvertFrom-SecureString -AsPlainText ; .\deploy\upload_kutt.ps1
#   もしくは  $env:KUTT_FTP_PASS="<パスワード>"; .\deploy\upload_kutt.ps1   （履歴に残るので前者推奨）
$ErrorActionPreference = "Stop"
$Host_ = "sv14321.xserver.jp"; $User = "kutt@shinko-ghd.jp"; $Remote = "/"   # FTPユーザーのホームが /kutt 相当
$Pass = $env:KUTT_FTP_PASS; if (-not $Pass) { throw "環境変数 KUTT_FTP_PASS にFTPパスワードを入れてください" }
$root = Join-Path (Split-Path $PSScriptRoot -Parent) "dist"
if (-not (Test-Path "$root\index.html")) { throw "dist/index.html がありません。先に dist を作成してください" }
$files = Get-ChildItem -Path $root -Recurse -File
$i = 0
foreach ($f in $files) {
  $rel = $f.FullName.Substring($root.Length + 1).Replace("\", "/")
  $url = "ftp://$Host_$Remote$rel"
  $i++; Write-Host ("[{0}/{1}] {2}" -f $i, $files.Count, $rel)
  & curl.exe --silent --show-error --fail --ssl-reqd --ftp-create-dirs -u "${User}:${Pass}" -T $f.FullName $url
  if ($LASTEXITCODE -ne 0) { throw "upload failed: $rel" }
}
Write-Host "done. https://shinko-ghd.jp/kutt/"
