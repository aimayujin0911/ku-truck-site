/**
 * LP（adblue.html）のフォーム送信を受ける doPost。
 * 既存の submitSurvey(data) をそのまま呼ぶだけなので、スプレッドシートへの記録・通知は
 * アンケート画面（/exec）からの送信と同じ挙動になる。
 *
 * 追加手順:
 *  1. GASエディタで、このコードを既存スクリプト（submitSurvey がある .gs）の末尾に貼り付ける
 *  2. 「デプロイ > デプロイを管理 > 編集(鉛筆) > バージョン: 新バージョン」で再デプロイ
 *     （アクセスできるユーザー: 全員 のまま。URL は変わらない）
 *  3. LPから送信テスト → シートに source = "LP adblue.html" の行が入れば成功
 *     ※2026-10 迷惑送信対策を追加。LP（adblue.html）側に website / subscribe_newsletter / _t の
 *       隠し項目が入った版をアップしてから、このコードで再デプロイすること（逆順だと全件が弾かれる）
 */
function doPost(e) {
  var p = (e && e.parameter) || {};
  // 迷惑送信対策（2026-10）: 人間に起こり得ない痕跡があれば記録せず OK だけ返す（ボットに悟らせない）
  //  - 見えない入力欄 website に値がある / 見えないチェックボックス subscribe_newsletter がチェック済み
  //  - _t（画面のJSが入れるページ表示時刻ms）が無い・数値でない＝画面を通らない直接送信
  //  ※「3秒未満」の判定は画面側のみ（お客様PCの時計ずれで本物を弾かないよう、ここでは時刻比較しない）
  var t = Number(p._t || 0);
  if (p.website || p.subscribe_newsletter || !t || isNaN(t)) {
    return HtmlService.createHtmlOutput('<!doctype html><meta charset="utf-8"><p>OK</p>');
  }
  var data = {
    company: p.company || '', kana: p.kana || '', name: p.name || '',
    tel: p.tel || '', email: p.email || '', zip: p.zip || '', addr: p.addr || '',
    vendor: p.vendor || '', volume: p.volume || '',
    large: p.large || '', mid: p.mid || '', small: p.small || '', other: p.other || '',
    price: p.price || '', contact: p.contact || 'メール',
    source: 'LP adblue.html'
  };
  var ok = true, msg = '';
  try { submitSurvey(data); } catch (err) { ok = false; msg = String(err); }
  // LP側は非表示iframeにPOSTして応答は読まないため、最小限のHTMLを返せばよい
  return HtmlService.createHtmlOutput(
    '<!doctype html><meta charset="utf-8"><p>' + (ok ? 'OK' : 'ERROR: ' + msg) + '</p>'
  );
}
