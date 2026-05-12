# health

健康管理プロジェクト。日次の記録・ChatGPTとの健康管理ログを一元管理する。

## 構成

```
health/
├── logs/
│   ├── daily.md             # 日次ヘルスログ（就寝・起床・コンディション）
│   └── chatgpt/             # ChatGPTから取得した会話ログ
├── reports/
│   └── health_project_report.md  # プロジェクト内容のまとめレポート
├── scripts/
│   └── fetch_chatgpt.py     # ChatGPTログ取得スクリプト
├── CHANGELOG.md
└── TODO.md
```

## 日次記録

`logs/daily.md` に日付ごとに以下を記録：

- 就寝時刻
- 起床時刻
- 起床時コンディション（1〜10）

ChatGPT健康管理プロジェクトで「おはよう」「おやすみ」と声をかけるだけで自動記録される。

## ChatGPTログ取得

```bash
cd /Users/keisuke140/Documents/Projects/health
python3 scripts/fetch_chatgpt.py
```

1. ブラウザが開くので ChatGPT にログイン
2. ログイン完了後、自動でチャットを取得して `logs/chatgpt/` に保存

### セットアップ（初回のみ）

```bash
pip3 install playwright playwright-stealth
/Users/keisuke140/Library/Python/3.9/bin/playwright install chromium
```
