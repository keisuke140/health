"""
ChatGPT健康管理プロジェクトのチャットをhealthレポに保存するスクリプト

手順:
1. ブラウザが開きます
2. プロジェクトページに自動で移動します
3. 「ログイン」ボタンをクリックしてログインしてください
4. ログイン後にプロジェクトのチャット一覧が自動で取得されます
"""

import asyncio
import re
from datetime import datetime
from pathlib import Path
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

PROJECT_URL = "https://chatgpt.com/g/g-p-6990afe76d6881919add95f35002df31-jian-kang-guan-li/project"
HEALTH_REPO = Path("/Users/keisuke140/Documents/Projects/health")
OUTPUT_DIR = HEALTH_REPO / "chatgpt_logs"


async def debug_page(page, label=""):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    shot = OUTPUT_DIR / f"debug_{label}.png"
    html = OUTPUT_DIR / f"debug_{label}.html"
    await page.screenshot(path=str(shot), full_page=True)
    html.write_text(await page.content(), encoding="utf-8")
    print(f"  [DEBUG] {shot.name}")


async def wait_for_login(page, timeout=300000):
    print("ブラウザでChatGPTにログインしてください。")
    print("ログイン完了後、自動で取得を開始します（最大5分待機）...")
    await page.wait_for_function(
        """() => {
            // Cloudflareチャレンジ中
            if (document.title === 'Just a moment...') return false;
            // ログインページ
            if (document.title.includes('開始する') || document.title.includes('Get started')) return false;
            // URLがauth系ならまだ
            if (location.pathname.startsWith('/auth')) return false;
            // ログインボタンが見えている
            const authBtns = Array.from(document.querySelectorAll('a[href*="auth/login"], a[href*="auth/signup"], button'));
            const loginBtn = authBtns.find(b => b.offsetParent !== null && (b.innerText.includes('Log in') || b.innerText.includes('ログイン')));
            if (loginBtn) return false;
            // サイドバーに会話履歴っぽい要素がある（ログイン済みの証拠）
            const hasSidebar = !!(
                document.querySelector('[data-testid="history-item"]') ||
                document.querySelector('nav a[href^="/c/"]') ||
                document.querySelector('nav a[href^="/g/"]') ||
                document.querySelector('[class*="sidebar"] a[href]') ||
                document.querySelector('#prompt-textarea') ||
                document.querySelector('textarea[placeholder]')
            );
            return hasSidebar;
        }""",
        timeout=timeout
    )
    await page.wait_for_timeout(4000)


async def get_project_conversation_links(page):
    """プロジェクト内の会話リンクを取得（プロジェクトセクションのみ）"""
    await page.wait_for_timeout(2000)

    # ページのHTML全体から会話リンクを収集し、プロジェクトに属するものを返す
    links = await page.evaluate("""() => {
        const seen = new Set();
        const results = [];

        // すべての /c/ リンクを探す
        const allLinks = Array.from(document.querySelectorAll('a[href]'))
            .filter(a => /\\/c\\/[a-zA-Z0-9-]+/.test(a.href));

        for (const a of allLinks) {
            if (seen.has(a.href)) continue;
            seen.add(a.href);

            // このリンクが「プロジェクト」セクションの下にあるか確認
            let el = a.parentElement;
            let inProject = false;
            let depth = 0;
            while (el && depth < 15) {
                const text = el.innerText || '';
                const ariaLabel = el.getAttribute('aria-label') || '';
                if (
                    text.includes('健康') || text.includes('health') ||
                    ariaLabel.includes('健康') || ariaLabel.includes('health') ||
                    el.dataset?.testid?.includes('project') ||
                    el.className?.includes?.('project')
                ) {
                    inProject = true;
                    break;
                }
                el = el.parentElement;
                depth++;
            }

            results.push({
                href: a.href,
                text: a.innerText.trim(),
                inProject
            });
        }
        return results;
    }""")

    # プロジェクト内のものを優先、なければ全件返す
    project_links = [l for l in links if l["inProject"]]
    print(f"  全会話リンク: {len(links)}件、プロジェクト内: {len(project_links)}件")

    if project_links:
        return project_links
    # プロジェクト判定できなければ全件（前回の動作を維持）
    return links


async def get_messages(page):
    await page.wait_for_timeout(2000)
    try:
        result = await page.evaluate("""() => {
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
            const roleEls = document.querySelectorAll('[data-message-author-role]');
            if (roleEls.length > 0) {
                return Array.from(roleEls).map(el => ({
                    role: el.getAttribute('data-message-author-role'),
                    text: el.innerText.trim()
                })).filter(m => m.text);
            }
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
    lines = [f"# {title}", f"取得日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ""]
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
            viewport={"width": 1280, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            locale="ja-JP",
        )
        page = await context.new_page()
        await Stealth().apply_stealth_async(page)

        print("プロジェクトページを開いています...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        try:
            await wait_for_login(page)
        except Exception as e:
            print(f"タイムアウトまたはエラー: {e}")
            try:
                await debug_page(page, "login_timeout")
            except Exception:
                pass
            await browser.close()
            return

        print("\nログイン確認。プロジェクトページに移動します...")
        await page.goto(PROJECT_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(5000)
        await debug_page(page, "after_login")

        print("会話リストを確認中...")
        conversations = await get_project_conversation_links(page)

        if not conversations:
            print("会話が見つかりませんでした。デバッグファイルを確認してください。")
            await browser.close()
            return

        print(f"{len(conversations)}件の会話を取得開始...")
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
        await page.wait_for_timeout(2000)
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
