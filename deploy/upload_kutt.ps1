# shinko-ghd.jp/kutt へ dist/ を FTPS でアップロードする
# 使い方: PowerShell で  .\deploy\upload_kutt.ps1   （実行するとパスワードを伏せ字で聞きます。履歴・ファイルには残りません）
$ErrorActionPreference = "Stop"
$FtpHost = "sv14321.xserver.jp"; $User = "kutt@shinko-ghd.jp"; $Remote = "/"   # FTPユーザーのホームが /kutt 相当のはず

$sec = Read-Host "FTP password for $User" -AsSecureString
$bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
try { $Pass = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
if (-not $Pass) { throw "パスワードが空です" }

# curl に認証情報を渡すときはコマンドラインに出さない（-K で設定を標準入力から渡す）
$cfg = "user = `"${User}:${Pass}`"`nssl-reqd`nsilent`nshow-error`nfail`n"

Write-Host "ログイン確認中..."
$list = $cfg | & curl.exe -K - --list-only "ftp://$FtpHost$Remote" 2>&1
if ($LASTEXITCODE -ne 0) {
  Write-Host "ログインに失敗しました: $list" -ForegroundColor Red
  Write-Host "確認: ①パスワードの再入力 ②Xserverサーバーパネル > FTP制限設定 で接続元IPが許可されているか ③ユーザー名が $User で正しいか"
  exit 1
}
Write-Host "ログインOK。現在のリモート一覧:"; $list | ForEach-Object { "  $_" }

$root = Join-Path (Split-Path $PSScriptRoot -Parent) "dist"
if (-not (Test-Path "$root\index.html")) { throw "dist/index.html がありません" }
$files = Get-ChildItem -Path $root -Recurse -File
$i = 0
foreach ($f in $files) {
  $rel = $f.FullName.Substring($root.Length + 1).Replace("\", "/")
  $i++; Write-Host ("[{0}/{1}] {2}" -f $i, $files.Count, $rel)
  $cfg | & curl.exe -K - --ftp-create-dirs -T $f.FullName "ftp://$FtpHost$Remote$rel"
  if ($LASTEXITCODE -ne 0) { throw "upload failed: $rel" }
}
$Pass = $null; $cfg = $null
Write-Host "done. https://shinko-ghd.jp/kutt/" -ForegroundColor Green
