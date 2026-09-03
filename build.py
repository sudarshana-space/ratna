#!/usr/bin/env python3
"""把 src/*.md 轉成 GitHub Pages 用的靜態 HTML。"""
import html
import re
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"

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
    t = html.escape(t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![\w@.-])((?:https?://)[^\s<）,，。]+)", r'<a href="\1">\1</a>', t)
    t = re.sub(r"(?<![\w<\"/])([\w.+-]+@[\w-]+\.[\w.-]+)", r'<a href="mailto:\1">\1</a>', t)
    return t

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

def page(title, body, current):
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
<title>{title}｜Ratna・瑯納</title>
<meta name="description" content="Ratna・瑯納 行動應用程式{title}">
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
<p class="meta">典鴻國際股份有限公司　法律文件</p>
<ul>
<li><a href="privacy.html">隱私權政策</a>（v1.2｜生效日 2026年9月1日）</li>
<li><a href="terms.html">服務條款</a>（v1.2｜生效日 2026年9月1日）</li>
</ul>
<p>如有任何疑問，請來信 info.dh.tw@gmail.com。</p>"""
    (ROOT / "index.html").write_text(page("法律文件", index, "index.html"), encoding="utf-8")
    print("built index.html")

main()
