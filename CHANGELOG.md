# Changelog

## 2026-05-13

### やったこと
- `scripts/fetch_chatgpt.py` を実行し、ChatGPTの会話30件を取得
  - 取得データは `chatgpt_logs/` に Markdown 形式で保存（01〜30）
  - 内容：育児・料理・妊娠・旅行（オーストラリア）・健康など日常的なチャット履歴

## 2026-05-11

### やったこと
- Playwright + playwright-stealth をインストール（Python 3.9環境）
- ChatGPT健康管理プロジェクト（`g-p-6990afe76d6881919add95f35002df31`）からチャットを取得するスクリプトを作成
  - `scripts/fetch_chatgpt.py`
  - ブラウザを表示状態で起動し、手動ログイン後に自動でチャットを取得する方式
  - ステルスモード（Cloudflare対策）を適用
  - ログイン検出・Cloudflare通過待機・会話一覧取得・メッセージ抽出・Markdown保存の機能を実装

### GitHub セットアップ
- `keisuke140/health` リポジトリをGitHub上に作成（`keisuke140` アカウント）
- Fine-grained Personal Access Token を発行し `.env` に `GITHUB_TOKEN=...` として保存
  - `.env` は `.gitignore` で除外済み（コミットされない）
  - `.env.example` をテンプレートとしてコミット済み
  - **Token の権限設定（GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens）**
    - Repository access: `All repositories`
    - Administration: `Read and write`（リポジトリ作成に必要）
    - Contents: `Read and write`（コードのプッシュに必要）
    - Metadata: `Read-only`（自動付与・必須）
- git remote に `https://TOKEN@github.com/keisuke140/health.git` を設定
- `main` ブランチを初回プッシュ完了

### 未完了（明日へ持ち越し）
- ChatGPTへのログインが完了できなかった（本人が就寝のため）
- 実際のチャットデータはまだ取得できていない
