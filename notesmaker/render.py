"""Markdown notes -> styled HTML (with KaTeX maths) -> PDF via headless Edge/Chrome."""

import html
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from markdown_it import MarkdownIt
from mdit_py_plugins.dollarmath import dollarmath_plugin
from mdit_py_plugins.footnote import footnote_plugin

BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
]

KATEX = "https://cdn.jsdelivr.net/npm/katex@0.16.22/dist"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="{katex}/katex.min.css">
<script src="{katex}/katex.min.js"></script>
<style>
  @page {{ size: A4; margin: 18mm 16mm 20mm; }}
  body {{ font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; font-size: 10.5pt;
         line-height: 1.55; color: #1c1c1c; max-width: 900px; margin: 0 auto; }}
  h1 {{ font-size: 21pt; color: #12355b; border-bottom: 3px solid #12355b; padding-bottom: 6px;
        margin: 0 0 4px; }}
  h1 + p em {{ color: #555; }}
  h2 {{ font-size: 15pt; color: #12355b; border-bottom: 1px solid #c9d3df; padding-bottom: 3px;
        margin-top: 26px; break-after: avoid; }}
  h3 {{ font-size: 12.5pt; color: #1f4e79; margin-top: 18px; break-after: avoid; }}
  h4 {{ font-size: 11pt; color: #333; break-after: avoid; }}
  p, li {{ orphans: 3; widows: 3; }}
  strong {{ color: #0d2a4a; }}
  blockquote {{ margin: 12px 0; padding: 8px 14px; background: #fff8e1;
                border-left: 4px solid #f2a900; border-radius: 3px; break-inside: avoid; }}
  blockquote p {{ margin: 4px 0; }}
  table {{ border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9.5pt;
           break-inside: avoid; }}
  th, td {{ border: 1px solid #c9d3df; padding: 5px 8px; text-align: left; vertical-align: top; }}
  th {{ background: #e8eef5; }}
  tr:nth-child(even) td {{ background: #f7f9fb; }}
  code {{ font-family: Consolas, "Courier New", monospace; font-size: 9.5pt;
          background: #f1f3f5; padding: 1px 4px; border-radius: 3px; }}
  pre {{ background: #f6f8fa; border: 1px solid #dde3ea; padding: 10px 12px; border-radius: 4px;
         white-space: pre-wrap; word-wrap: break-word; break-inside: avoid; }}
  pre code {{ background: none; padding: 0; }}
  .math.block {{ margin: 10px 0; overflow-x: auto; }}
  hr {{ border: none; border-top: 1px solid #c9d3df; margin: 20px 0; }}
  .footer {{ margin-top: 30px; font-size: 8.5pt; color: #888; text-align: center; }}
</style>
</head>
<body>
{body}
<div class="footer">{footer}</div>
<script>
  document.querySelectorAll(".math").forEach(function (el) {{
    if (!window.katex) return;
    var display = el.classList.contains("block");
    try {{ katex.render(el.textContent, el, {{displayMode: display, throwOnError: false}}); }}
    catch (e) {{}}
  }});
</script>
</body>
</html>
"""


def markdown_to_html(markdown, title, footer=""):
    md = (
        MarkdownIt("commonmark", {"html": False, "linkify": False})
        .enable("table")
        .enable("strikethrough")
        .use(dollarmath_plugin, double_inline=True)
        .use(footnote_plugin)
    )
    return TEMPLATE.format(
        title=html.escape(title), katex=KATEX, body=md.render(markdown), footer=html.escape(footer)
    )


def find_browser():
    for path in BROWSER_CANDIDATES:
        if os.path.exists(path):
            return path
    for name in ("msedge", "google-chrome", "chromium", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


def html_to_pdf(html_path, pdf_path):
    browser = find_browser()
    if not browser:
        raise RuntimeError("Microsoft Edge or Google Chrome is needed to create the PDF.")
    html_path, pdf_path = Path(html_path).resolve(), Path(pdf_path).resolve()
    if pdf_path.exists():
        pdf_path.unlink()
    # A separate profile stops the job being handed to an already-open browser window.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as profile:
        subprocess.run(
            [
                browser,
                "--headless=new",
                "--disable-gpu",
                "--no-first-run",
                f"--user-data-dir={profile}",
                "--no-pdf-header-footer",
                "--virtual-time-budget=20000",
                f"--print-to-pdf={pdf_path}",
                html_path.as_uri(),
            ],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=180,
        )
        deadline = time.time() + 60
        while not pdf_path.exists() and time.time() < deadline:
            time.sleep(0.5)
        time.sleep(1)  # let the browser finish writing and release the profile
    if not pdf_path.exists():
        raise RuntimeError(f"The browser did not produce a PDF. The HTML version is at {html_path}")
    return pdf_path
