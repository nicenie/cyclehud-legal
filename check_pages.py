#!/usr/bin/env python3
"""法务页自检：链接不漏、不自带外站依赖、四语言同构。

为什么需要它：这些页面**上线之后才被审核员和用户访问**，本地点错一个相对路径
（`../en/...` 写成 `en/...`）在 GitHub Pages 上就是 404，而 404 的隐私政策链接
在审核里等同于「没有隐私政策」。这种错误不该靠人眼在 8 个页面里逐个点。

用法：
    python3 check_pages.py          # 正向验收
    python3 check_pages.py --quiet  # 只输出结论
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
LOCALES = ("zh-Hans", "zh-Hant", "en", "ja")
PAGES = ("privacy-policy.html", "support.html")
CONTACT_EMAIL = "rankor@sina.com"

# App 名只在这里定义一次：改名（CycleHUD → VeloLume）时不必再翻 8 个 HTML。
APP_NAME = "VeloLume"

# 「生效日期」四种语言的写法；隐私政策页必须带上，否则无法判断条文何时开始适用。
EFFECTIVE_LABELS = ("生效日期", "生效日期", "Effective", "施行日")


class Collector(HTMLParser):
    """收集 href/src 与文本，供后续断言用。"""

    def __init__(self):
        super().__init__()
        self.refs = []
        self.text_parts = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.refs.append(value)

    def handle_data(self, data):
        self.text_parts.append(data)


def parse(path):
    collector = Collector()
    collector.feed(path.read_text(encoding="utf-8"))
    return collector


def check():
    failures = []

    for locale in LOCALES:
        for page in PAGES:
            path = ROOT / locale / page
            if not path.exists():
                failures.append(f"缺少 {locale}/{page}")
                continue

            parsed = parse(path)
            text = "".join(parsed.text_parts)

            # 1. 每个本地引用都必须落到真实文件上
            for ref in parsed.refs:
                if ref.startswith("mailto:"):
                    if ref.split(":", 1)[1].split("?", 1)[0].lower() != CONTACT_EMAIL:
                        failures.append(f"{locale}/{page} 的联系邮箱与约定不一致：{ref}")
                    continue
                parts = urlsplit(ref)
                if parts.scheme in ("http", "https"):
                    failures.append(
                        f"{locale}/{page} 引用了外站资源 {ref}：法务页必须自包含")
                    continue
                if ref.startswith("#"):
                    continue
                target = (path.parent / parts.path).resolve()
                if not target.exists():
                    failures.append(f"{locale}/{page} 的链接指向不存在的文件：{ref}")

            # 2. 语言切换条必须齐四种语言（否则某个语种的用户会走进死路）
            #    当前语言那一项指向自身，是不带 ../ 的裸文件名，所以要连它一起算：
            #    判据是「指向本页的链接恰好 4 条，且覆盖四个语种目录」。
            nav_refs = [r for r in parsed.refs if r.endswith(page)]
            if len(nav_refs) != len(LOCALES):
                failures.append(
                    f"{locale}/{page} 的语言切换条有 {len(nav_refs)} 条，应为 {len(LOCALES)} 条")
            locales_linked = {locale}
            for ref in nav_refs:
                parts = ref.split("/")
                if len(parts) >= 2 and parts[0] == "..":
                    locales_linked.add(parts[1])
            missing = set(LOCALES) - locales_linked
            if missing:
                failures.append(
                    f"{locale}/{page} 的语言切换条缺少 {sorted(missing)}")

            # 3. 隐私政策必须写明生效日期
            if page == "privacy-policy.html" and not any(
                label in text for label in EFFECTIVE_LABELS
            ):
                failures.append(f"{locale}/{page} 找不到生效日期")

            # 4. 页面必须自报 App 名，避免复制粘贴留下别的 App 名字
            if APP_NAME not in text:
                failures.append(f"{locale}/{page} 正文没有出现 {APP_NAME}")

    index = ROOT / "index.html"
    if not index.exists():
        failures.append("缺少 index.html")
    else:
        refs = parse(index).refs
        for locale in LOCALES:
            for page in PAGES:
                if f"{locale}/{page}" not in refs:
                    failures.append(f"index.html 没有链接到 {locale}/{page}")

    if not (ROOT / ".nojekyll").exists():
        failures.append("缺少 .nojekyll（GitHub Pages 会走 Jekyll，下划线开头的路径会被吞）")

    return failures


def main():
    quiet = "--quiet" in sys.argv
    failures = check()
    if not quiet:
        total = len(LOCALES) * len(PAGES) + 1
        print(f"  检查 {total} 个页面：{len(LOCALES)} 语言 × {len(PAGES)} 页 + index.html")
    if failures:
        print("\n验收 FAIL：")
        for item in failures:
            print("  - " + item)
    print("结果：", "全部通过" if not failures else "存在失败项")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
