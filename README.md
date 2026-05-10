# health

健康管理プロジェクト。ChatGPTの健康管理チャットをログとして保存・整理する。

## 構成

```
health/
├── scripts/
│   └── fetch_chatgpt.py   # ChatGPTプロジェクトからチャットを取得するスクリプト
├── chatgpt_logs/          # 取得したチャットログ（未コミット）
├── CHANGELOG.md
├── TODO.md
└── README.md
```

## セットアップ

```bash
pip3 install playwright playwright-stealth
/Users/keisuke140/Library/Python/3.9/bin/playwright install chromium
```

## ChatGPTログ取得方法

```bash
cd /Users/keisuke140/Documents/Projects/health
python3 scripts/fetch_chatgpt.py
```

1. ブラウザが開くので「ログイン」をクリック
2. ChatGPTにログイン
3. ログイン完了後、自動でチャットを取得して `chatgpt_logs/` に保存
