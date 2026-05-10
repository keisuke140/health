"""
ChatGPT健康管理プロジェクトのチャットをhealthレポに保存するスクリプト

手順:
1. ブラウザが開きます
2. プロジェクトページに自動で移動します
3. 「ログイン」ボタンをクリックしてログインしてください
4. ログイン後にプロジェクトのチャット一覧が表示されたら自動で取得します
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

PROJECT_URL = "https://chatgpt.com/g/g-p-6990afe76d6881919add95f35002df31"
HEALTH_REPO = Path("/Users/keisuke140/Documents/Projects/health")
OUTPUT_DIR = HEALTH_REPO / "chatgpt_logs"


async def debug_page(page, label=""):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shot = OUTPUT_DIR / f"debug_{label}.png"
    html = OUTPUT_DIR / f"debug_{label}.html"
    await page.screenshot(path=str(shot), full_page=True)
    html.write_text(await page.content(), encoding="utf-8")
    print(f"  [DEBUG] {shot.name}")


async def wait_until_logged_in_on_project(page, timeout=300000):
    """
    プロジェクトページでログイン済み状態になるまで待つ。
    ログイン済み = ログインボタンがなく、チャット入力欄またはサイドバーが表示されている
    """
    print("ブラウザのプロジェクトページで「ログイン」ボタンをクリックしてログインしてください。")
    print("ログイン完了後、自動で取得を開始します（最大5分待機）...")

    await page.wait_for_function(
        """() => {
            // ログインボタンが画面にある = まだログインしていない
            const text = document.body?.innerText || '';
            const hasLoginPrompt = text.includes('自分に合った回答を得る') ||
                                   text.includes('Get answers tailored');
            if (hasLoginPrompt) return false;

            // ログイン・サインアップのボタンが目立つ位置にある
            const bigBtns = Array.from(document.querySelectorAll('a[href*="auth/login"], a[href*="auth/signup"]'));
            if (bigBtns.some(b => b.offsetParent !== null)) return false;

            // Cloudflareチャレンジ中
            if (document.title === 'Just a moment...') return false;

            // チャットUIが表示されている
            return !!(
                document.querySelector('#prompt-textarea') ||
                document.querySelector('[data-testid="send-button"]') ||
                document.querySelector('textarea')
            );
        }""",
        timeout=timeout
    )
    await page.wait_for_timeout(2000)


async def get_conversation_links(page):
    """サイドバーの会話リンクを取得"""
    await page.wait_for_timeout(2000)
    links = await page.evaluate("""() => {
        return Array.from(document.querySelectorAll('a[href]'))
            .filter(a => a.href.match(/\\/c\\/[a-z0-9-]+/))
            .map(a => ({ href: a.href, text: a.innerText.trim() }));
    }""")
    return links


async def get_messages(page):
    """ページのメッセージを取得"""
    await page.wait_for_timeout(2000)
    try:
        result = await page.evaluate("""() => {
            // パターン1: data-testid
            const turns = document.querySelectorAll('[data-testid^="conversation-turn"]');
            if (turns.length > 0) {
                return Array.from(turns).map(el => {
                    const roleEl = el.querySelector('[data-message-author-role]');
                    return {
                        role: roleEl?.getAttribute('data-message-author-role') || 'unknown',
                        text: el.innerText.trim()
                    };
                }).filter(m => m.text);
            }

            // パターン2: role属性直接
            const roleEls = document.querySelectorAll('[data-message-author-role]');
            if (roleEls.length > 0) {
                return Array.from(roleEls).map(el => ({
                    role: el.getAttribute('data-message-author-role'),
                    text: el.innerText.trim()
                })).filter(m => m.text);
            }

            // パターン3: article
            const articles = document.querySelectorAll('article');
            if (articles.length > 0) {
                return Array.from(articles).map((el, i) => ({
                    role: i % 2 === 0 ? 'user' : 'assistant',
                    text: el.innerText.trim()
                })).filter(m => m.text);
            }
            return [];
        }""")
        return result
    except Exception as e:
        print(f"  メッセージ取得エラー: {e}")
        return []


def save_md(title, messages, path):
    lines = [
        f"# {title}",
        f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    for msg in messages:
        label = "**ユーザー**" if msg["role"] == "user" else "**ChatGPT**"
        lines += [f"## {label}", msg["text"], ""]
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  保存: {path.name}")


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        # プロジェクトページを直接開く
        print(f"プロジェクトページを開いています...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # ログイン待機
        try:
            await wait_until_logged_in_on_project(page, timeout=300000)
        except Exception as e:
            print(f"タイムアウトまたはエラー: {e}")
            await debug_page(page, "login_timeout")
            await browser.close()
            return

        print("\nログイン確認。データを取得します...")
        await debug_page(page, "after_login")

        # 会話リストを取得
        print("会話リストを確認中...")
        conversations = await get_conversation_links(page)

        if not conversations:
            print("会話リストが見つかりません。現在のページからメッセージを取得します。")
            messages = await get_messages(page)
            if messages:
                save_md("健康管理チャット", messages, OUTPUT_DIR / "health_chat.md")
                print(f"\n完了。{len(messages)}件のメッセージを保存しました。")
            else:
                print("メッセージが取得できませんでした。デバッグファイルを確認してください。")
        else:
            print(f"{len(conversations)}件の会話を発見。取得開始...")
            saved = []
            for i, conv in enumerate(conversations):
                href = conv["href"]
                raw_title = conv["text"].split("\n")[0] or f"conversation_{i+1}"
                safe_title = re.sub(r'[\\/*?:"<>|]', "", raw_title)[:50]
                print(f"\n[{i+1}/{len(conversations)}] {safe_title}")

                try:
                    await page.goto(href, wait_until="domcontentloaded")
                    await page.wait_for_timeout(3000)
                    messages = await get_messages(page)
                except Exception as e:
                    print(f"  エラー: {e}")
                    messages = []

                if messages:
                    fname = f"{i+1:02d}_{safe_title}.md"
                    save_md(raw_title, messages, OUTPUT_DIR / fname)
                    saved.append((fname, raw_title))
                else:
                    print("  メッセージ取得不可（スキップ）")

            # インデックス作成
            idx = [
                "# ChatGPT健康管理チャットログ",
                f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"合計: {len(saved)}件", "",
                "## ファイル一覧",
            ]
            for fname, title in saved:
                idx.append(f"- [{title}]({fname})")
            (OUTPUT_DIR / "README.md").write_text("\n".join(idx), encoding="utf-8")
            print(f"\n完了。{len(saved)}件の会話を保存しました。")

        print(f"保存先: {OUTPUT_DIR}")
        await page.wait_for_timeout(3000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
