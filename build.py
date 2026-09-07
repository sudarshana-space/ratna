#!/usr/bin/env python3
"""把 src/*.md 轉成 GitHub Pages 用的靜態 HTML。"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
SITE = "https://ratna.tw"

INDEX_TITLE = "Ratna・瑯納｜雲川水月礦石旗艦系列"
INDEX_DESC = (
    "Ratna 是梵文「珍寶」，音譯作瑯納——雲川水月打造的礦石旗艦系列。"
    "依循印度占星的生命藍圖，在對的時候做對的選擇，再以礦石的能量自我祝福；"
    "每一條礦石手鍊，都搭配 Ratna App。"
)

PAGES = [
    ("privacy.md", "privacy.html", "隱私權政策"),
    ("terms.md", "terms.html", "服務條款"),
]

CSS = """
:root{color-scheme:light dark;--bg:#fbfaf8;--fg:#232025;--muted:#6b6570;--rule:#e5e0da;--accent:#7a5c3e;--card:#fff}
@media (prefers-color-scheme:dark){:root{--bg:#16151a;--fg:#e8e4de;--muted:#a09aa6;--rule:#312e37;--accent:#c9a67a;--card:#1d1c22}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang TC","Noto Sans TC","Microsoft JhengHei",sans-serif;
  font-size:16px;line-height:1.9;-webkit-text-size-adjust:100%}
.wrap{max-width:760px;margin:0 auto;padding:48px 20px 96px}
nav{font-size:14px;margin-bottom:36px}
nav a{color:var(--muted);text-decoration:none;margin-right:16px}
nav a:hover,nav a.on{color:var(--accent)}
h1{font-size:28px;line-height:1.4;margin:0 0 8px;letter-spacing:.02em}
h2{font-size:20px;margin:44px 0 14px;padding-top:20px;border-top:1px solid var(--rule);letter-spacing:.02em}
h3{font-size:16px;margin:28px 0 10px;color:var(--accent)}
p{margin:0 0 16px}
.meta{color:var(--muted);font-size:14px;margin:0 0 32px}
ul,ol{margin:0 0 16px;padding-left:1.4em}
li{margin-bottom:6px}
a{color:var(--accent);word-break:break-all}
.tw{overflow-x:auto;margin:0 0 20px;-webkit-overflow-scrolling:touch}
table{border-collapse:collapse;width:100%;min-width:420px;font-size:14.5px;background:var(--card)}
th,td{border:1px solid var(--rule);padding:10px 12px;text-align:left;vertical-align:top;line-height:1.7}
th{background:color-mix(in srgb,var(--accent) 10%,transparent);font-weight:600;white-space:nowrap}
footer{margin-top:64px;padding-top:20px;border-top:1px solid var(--rule);color:var(--muted);font-size:13px}
"""

def inline(t):
    """行內語法轉換。

    已產生的 <a> 會先換成預留位置，避免後續的裸網址／email 正則
    再去掃它的 href 屬性而產生巢狀錨點。
    """
    t = html.escape(t)
    slots = []

    def stash(markup):
        slots.append(markup)
        return "\x00{}\x00".format(len(slots) - 1)

    # markdown 連結 [文字](網址)
    t = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: stash('<a href="{}">{}</a>'.format(m.group(2), m.group(1))),
        t,
    )
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    # 裸網址
    t = re.sub(
        r"(?<![\w@.\-/])(https?://[^\s<）,，。、]+)",
        lambda m: stash('<a href="{}">{}</a>'.format(m.group(1), m.group(1))),
        t,
    )
    # 裸 email
    t = re.sub(
        r"(?<![\w.\-/@])([\w.+-]+@[\w-]+\.[\w.-]+[\w])",
        lambda m: stash('<a href="mailto:{}">{}</a>'.format(m.group(1), m.group(1))),
        t,
    )
    return re.sub(r"\x00(\d+)\x00", lambda m: slots[int(m.group(1))], t)

def row(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]

def convert(md):
    lines = md.split("\n")
    out, i = [], 0
    while i < len(lines):
        s = lines[i].rstrip()
        if not s.strip():
            i += 1
            continue
        # table
        if s.startswith("|") and i + 1 < len(lines) and re.match(r"^\|[\s:|-]+\|$", lines[i + 1].strip()):
            head = row(s)
            i += 2
            body = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                body.append(row(lines[i]))
                i += 1
            t = ['<div class="tw"><table><thead><tr>']
            t += [f"<th>{inline(c)}</th>" for c in head]
            t.append("</tr></thead><tbody>")
            for r in body:
                t.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        # heading
        m = re.match(r"^(#{1,4})\s+(.*)$", s)
        if m:
            lv = len(m.group(1))
            out.append(f"<h{lv}>{inline(m.group(2).strip('*').strip())}</h{lv}>")
            i += 1
            continue
        # list
        if re.match(r"^\s*[-*]\s+", s) or re.match(r"^\s*\d+\.\s+", s):
            ordered = bool(re.match(r"^\s*\d+\.\s+", s))
            tag = "ol" if ordered else "ul"
            items = []
            while i < len(lines) and (re.match(r"^\s*[-*]\s+", lines[i]) or re.match(r"^\s*\d+\.\s+", lines[i])):
                items.append(re.sub(r"^\s*(?:[-*]|\d+\.)\s+", "", lines[i].rstrip()))
                i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(x)}</li>" for x in items) + f"</{tag}>")
            continue
        out.append(f"<p>{inline(s)}</p>")
        i += 1
    return "\n".join(out)

def page(title, body, current, head_title=None, description=None, url=None):
    head_title = head_title or f"{title}｜Ratna・瑯納"
    description = description or f"Ratna・瑯納 行動應用程式{title}"
    url = url or f"{SITE}/{current}"
    parts = []
    for _, h, t in PAGES:
        cls = ' class="on"' if h == current else ''
        parts.append('<a href="' + h + '"' + cls + '>' + t + '</a>')
    nav = "".join(parts)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{head_title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="Ratna・瑯納">
<meta property="og:locale" content="zh_TW">
<meta property="og:title" content="{head_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Ratna・瑯納　雲川水月礦石旗艦系列">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="{SITE}/og.png">
<link rel="icon" href="favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="16x16" href="favicon-16.png">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="icon" type="image/png" sizes="64x64" href="favicon-64.png">
<link rel="apple-touch-icon" sizes="180x180" href="apple-touch-icon.png">
<meta name="theme-color" content="#1d3b54">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<nav><a href="./">Ratna・瑯納</a>{nav}</nav>
{body}
<footer>典鴻國際股份有限公司　DH-International<br>臺北市松山區富錦街118號一樓　·　info.dh.tw@gmail.com</footer>
</div>
</body>
</html>
"""

def main():
    for src, dest, title in PAGES:
        md = (SRC / src).read_text(encoding="utf-8")
        body = convert(md)
        # 首行 h1 之後那段視為 meta
        body = body.replace("<p>適用產品", '<p class="meta">適用產品', 1)
        (ROOT / dest).write_text(page(title, body, dest), encoding="utf-8")
        print("built", dest)

    index = """<h1>Ratna・瑯納</h1>
<p class="meta">典鴻國際股份有限公司</p>
<p>Ratna 是梵文，意為「珍寶」；音譯作「瑯納」——瑯，是純淨；納，是收藏天地的精華。</p>
<p>「Ratna・瑯納」是雲川水月所打造的礦石旗艦系列；雲川水月，是華人世界最具影響力的全方位個人療癒體驗品牌。</p>
<p>我們依循印度占星的世界觀：古印度的聖者相信，天上星辰的運行，正是每個人身、心、靈的生命藍圖。讀懂自己的藍圖，在對的時候做對的選擇，再以礦石的能量自我祝福——路，就會走得順一些。</p>
<p>每一條礦石手鍊，都搭配 Ratna App。它陪著你，在生命的每一刻，找到自己的節奏，安下心來，慢慢把自己填滿。</p>
<h2>法律文件</h2>
<ul>
<li><a href="privacy.html">隱私權政策</a>（v1.2｜生效日 2026年9月1日）</li>
<li><a href="terms.html">服務條款</a>（v1.2｜生效日 2026年9月1日）</li>
</ul>
<p>如有任何疑問，請來信 info.dh.tw@gmail.com。</p>"""
    (ROOT / "index.html").write_text(
        page(
            "法律文件",
            index,
            "index.html",
            head_title=INDEX_TITLE,
            description=INDEX_DESC,
            url=SITE + "/",
        ),
        encoding="utf-8",
    )
    print("built index.html")

main()
