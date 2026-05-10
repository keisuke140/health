# Changelog

## 2026-05-11

### やったこと
- Playwright + playwright-stealth をインストール（Python 3.9環境）
- ChatGPT健康管理プロジェクト（`g-p-6990afe76d6881919add95f35002df31`）からチャットを取得するスクリプトを作成
  - `scripts/fetch_chatgpt.py`
  - ブラウザを表示状態で起動し、手動ログイン後に自動でチャットを取得する方式
  - ステルスモード（Cloudflare対策）を適用
  - ログイン検出・Cloudflare通過待機・会話一覧取得・メッセージ抽出・Markdown保存の機能を実装

### GitHub セットアップ
- `keisuke140/health` リポジトリをGitHub上に作成
- Fine-grained Personal Access Token を `.env` に保存（`.gitignore` 除外済み）
  - 必要な権限：Administration: Read & write ＋ Contents: Read & write ＋ Metadata: Read-only
  - `All repositories` アクセスで設定
- リモート追加・初回プッシュ完了

### 未完了（明日へ持ち越し）
- ChatGPTへのログインが完了できなかった（本人が就寝のため）
- 実際のチャットデータはまだ取得できていない
