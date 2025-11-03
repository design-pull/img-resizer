# ImgResizer — ダウンロード

[![Release](https://img.shields.io/github/v/release/design-pull/img-resizer)](https://github.com/design-pull/img-resizer/releases/latest)

**最新リリース:** v0.1.0

---

## ダウンロード
- ZIP（実行ファイル＋インストーラ同梱）: [ImgResizer-distribution-with-installer.zip](https://raw.githubusercontent.com/design-pull/img-resizer/main/dist/ImgResizer-distribution-with-installer.zip)  
- （代替）リリースページ: https://github.com/design-pull/img-resizer/releases/latest

---

## インストール方法
- ZIP 配布
  1. 上の ZIP をダウンロードして展開  
  2. 展開先フォルダ内の `ImgResizer.exe` をダブルクリックして実行（Python は不要）
- インストーラ配布（同梱している場合）
  1. `ImgResizer_Installer.exe` を実行  
  2. インストーラの指示に従ってインストール

---

## チェックサム（署名未実施のため推奨）
- SHA256 (ImgResizer-distribution-with-installer.zip): `PUT_SHA256_HASH_HERE`

PowerShell でハッシュを生成するコマンド:
```powershell
Get-FileHash .\dist\ImgResizer-distribution-with-installer.zip -Algorithm SHA256 | Format-List
```

ダウンロード後は上のハッシュと一致するか確認してください。

---

## 動作環境
- OS: Windows 10 / Windows 11（x64 推奨）  
- Python 不要（PyInstaller でバンドル済み）  
- インストーラを使う場合は管理者権限が必要になることがあります

---

## 使い方（簡潔）
1. アプリを起動する  
2. 画像をドラッグ＆ドロップ、または「開く」で読み込み  
3. プレビューでアスペクト比・サイズを確認  
4. 出力設定（幅/高さ、画質）を指定して保存またはエクスポート

---

## 注意事項と既知の問題
- 現バージョンは未署名の初回リリースです。SmartScreen による警告が出る場合があります。  
- SVG の読み込みは追加ライブラリ（Cairo 系）が必要になる場合があります。SVG が正しく読み込めない場合は Issue を作成してください。  
- ZIP 配布の場合は不要な開発ファイルを含めないようにしていますが、万一不要ファイルが含まれていたら報告してください。  
- ファイル名やパスに特殊文字や長いパスが含まれる環境では入出力で問題が出ることがあります。

---

## トラブルシューティング
- 起動しない／クラッシュする  
  - 管理者として実行してみる。  
  - 別の PC（クリーン環境）での再現を確認してログや画面を Issue に添付してください。
- アイコンが古く表示される  
  - エクスプローラーのキャッシュが影響するので、エクスプローラー再起動やサインアウト/サインインを試してください。
- ダウンロードが途中で失敗する  
  - ブラウザのキャッシュをクリアして再試行、あるいは別ブラウザで試してください。

---

## リリースノート（サマリ）
- v0.1.0 — 初回リリース: 単体実行ファイルと基本的なリサイズ・プレビュー・エクスポート機能を提供

---

## サポート
- バグ報告・要望は GitHub Issues でお願いします: https://github.com/design-pull/img-resizer/issues  
- Issue を作成する際の推奨テンプレート:
  - 発生手順（再現手順）  
  - 期待される挙動と実際の挙動  
  - OS バージョン、使用ファイル（可能なら添付）、スクリーンショットやログ

---

## 将来的な予定
- 署名済みビルドの公開（SmartScreen の誤検出を低減）  
- GitHub Actions を使った自動ビルド・自動リリースおよび docs 自動更新

---
