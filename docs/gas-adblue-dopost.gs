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
 */
function doPost(e) {
  var p = (e && e.parameter) || {};
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
