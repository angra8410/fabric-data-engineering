import re
import html
from pathlib import Path
import subprocess

md_path = Path(r"C:\Users\antoi\Downloads\All_Files\projects\proyectos-data-engineering\scog-growth-report\technical_options_scoping_document.md")
html_path = Path(r"C:\Users\antoi\Downloads\All_Files\projects\proyectos-data-engineering\scog-growth-report\technical_options_scoping_document.html")
pdf_path = Path(r"C:\Users\antoi\Downloads\All_Files\projects\proyectos-data-engineering\scog-growth-report\Technical_Options_Scoping_Document_SCOG.pdf")

content = md_path.read_text(encoding="utf-8")

def parse_markdown_to_html(md_text):
    lines = md_text.splitlines()
    html_lines = []
    in_code_block = False
    code_lang = ""
    code_content = []
    in_table = False
    table_rows = []
    in_blockquote = False
    blockquote_lines = []
    blockquote_type = ""
    in_list = False
    list_type = "ul"

    def inline_format(text):
        # Escape html chars
        # But handle formatting first or safely
        # bold
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        # italic
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        # inline code
        text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
        # links
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2" target="_blank">\1</a>', text)
        return text

    def close_table():
        nonlocal in_table, table_rows
        if not in_table:
            return ""
        in_table = False
        res = ["<div class=\"table-wrapper\"><table>"]
        for i, row in enumerate(table_rows):
            res.append("  <tr>")
            tag = "th" if i == 0 else "td"
            for cell in row:
                res.append(f"    <{tag}>{inline_format(cell.strip())}</{tag}>")
            res.append("  </tr>")
        res.append("</table></div>")
        table_rows = []
        return "\n".join(res)

    def close_blockquote():
        nonlocal in_blockquote, blockquote_lines, blockquote_type
        if not in_blockquote:
            return ""
        in_blockquote = False
        alert_class = f"alert alert-{blockquote_type.lower()}" if blockquote_type else "blockquote"
        body = "<br>".join(inline_format(line) for line in blockquote_lines)
        blockquote_lines = []
        blockquote_type = ""
        return f'<div class="{alert_class}"><div class="alert-icon"></div><div class="alert-content">{body}</div></div>'

    def close_list():
        nonlocal in_list, list_type
        if not in_list:
            return ""
        in_list = False
        return f"</{list_type}>"

    i = 0
    while i < len(lines):
        line = lines[i]

        # Check code fence
        if line.strip().startswith("```"):
            if in_code_block:
                in_code_block = False
                escaped_code = html.escape("\n".join(code_content))
                html_lines.append(f'<pre><code class="language-{code_lang}">{escaped_code}</code></pre>')
                code_content = []
                code_lang = ""
            else:
                if in_table:
                    html_lines.append(close_table())
                if in_blockquote:
                    html_lines.append(close_blockquote())
                if in_list:
                    html_lines.append(close_list())
                in_code_block = True
                code_lang = line.strip()[3:].strip()
            i += 1
            continue

        if in_code_block:
            code_content.append(line)
            i += 1
            continue

        # Check table row
        if line.strip().startswith("|") and line.strip().endswith("|"):
            if in_list:
                html_lines.append(close_list())
            if in_blockquote:
                html_lines.append(close_blockquote())
            # check if it's separator row | :--- | :--- |
            if re.match(r'^\|(\s*:?-+:?\s*\|)+$', line.strip()):
                # separator row, skip
                i += 1
                continue
            cells = [c for c in line.strip()[1:-1].split("|")]
            table_rows.append(cells)
            in_table = True
            i += 1
            continue
        elif in_table:
            html_lines.append(close_table())

        # Check blockquote / alert
        if line.strip().startswith(">"):
            if in_list:
                html_lines.append(close_list())
            quote_text = line.strip()[1:].strip()
            alert_match = re.match(r'^\[!(NOTE|IMPORTANT|TIP|WARNING|CAUTION)\]', quote_text)
            if alert_match:
                blockquote_type = alert_match.group(1)
                in_blockquote = True
            else:
                in_blockquote = True
                blockquote_lines.append(quote_text)
            i += 1
            continue
        elif in_blockquote:
            html_lines.append(close_blockquote())

        # Check horizontal rule
        if line.strip() in ("---", "___", "***"):
            if in_list:
                html_lines.append(close_list())
            html_lines.append("<hr>")
            i += 1
            continue

        # Check headings
        h_match = re.match(r'^(#{1,6})\s+(.*)$', line)
        if h_match:
            if in_list:
                html_lines.append(close_list())
            level = len(h_match.group(1))
            heading_text = inline_format(h_match.group(2))
            html_lines.append(f"<h{level}>{heading_text}</h{level}>")
            i += 1
            continue

        # Check list item
        ul_match = re.match(r'^\s*[-*]\s+(.*)$', line)
        ol_match = re.match(r'^\s*(\d+)\.\s+(.*)$', line)
        if ul_match or ol_match:
            new_list_type = "ol" if ol_match else "ul"
            item_text = (ol_match or ul_match).group(1) if not ol_match else ol_match.group(2)
            if not in_list or list_type != new_list_type:
                if in_list:
                    html_lines.append(close_list())
                html_lines.append(f"<{new_list_type}>")
                in_list = True
                list_type = new_list_type
            html_lines.append(f"  <li>{inline_format(item_text)}</li>")
            i += 1
            continue
        elif in_list and line.strip() == "":
            pass # allow loose list or close on next block
        elif in_list and not (line.startswith("  ") or line.startswith("\t")):
            html_lines.append(close_list())

        # Empty line
        if not line.strip():
            i += 1
            continue

        # Paragraph
        html_lines.append(f"<p>{inline_format(line.strip())}</p>")
        i += 1

    if in_table:
        html_lines.append(close_table())
    if in_blockquote:
        html_lines.append(close_blockquote())
    if in_list:
        html_lines.append(close_list())

    return "\n".join(html_lines)

html_body = parse_markdown_to_html(content)

full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SCOG - Technical Options Scoping Document</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  :root {{
    --primary: #005A9C;
    --primary-dark: #003B66;
    --secondary: #2B7A78;
    --text: #1E293B;
    --text-muted: #64748B;
    --bg: #FFFFFF;
    --bg-alt: #F8FAFC;
    --border: #E2E8F0;
    --card-bg: #FFFFFF;
    --accent: #2563EB;
  }}

  * {{
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }}

  body {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    line-height: 1.65;
    color: var(--text);
    background-color: var(--bg-alt);
    padding: 40px 20px;
    font-size: 15px;
  }}

  .container {{
    max-width: 960px;
    margin: 0 auto;
    background: var(--card-bg);
    padding: 60px 70px;
    border-radius: 12px;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
    border: 1px solid var(--border);
  }}

  h1 {{
    font-size: 28px;
    font-weight: 700;
    color: var(--primary-dark);
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 3px solid var(--primary);
    letter-spacing: -0.5px;
  }}

  h2 {{
    font-size: 20px;
    font-weight: 700;
    color: var(--primary-dark);
    margin-top: 36px;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
  }}

  h3 {{
    font-size: 16px;
    font-weight: 600;
    color: #334155;
    margin-top: 24px;
    margin-bottom: 12px;
  }}

  h4 {{
    font-size: 14px;
    font-weight: 600;
    color: #475569;
    margin-top: 18px;
    margin-bottom: 8px;
  }}

  p {{
    margin-bottom: 14px;
    color: #334155;
  }}

  strong {{
    font-weight: 600;
    color: #0F172A;
  }}

  ul, ol {{
    margin: 12px 0 16px 24px;
    color: #334155;
  }}

  li {{
    margin-bottom: 6px;
  }}

  hr {{
    border: 0;
    border-top: 1px solid var(--border);
    margin: 32px 0;
  }}

  .table-wrapper {{
    width: 100%;
    overflow-x: auto;
    margin: 20px 0;
    border: 1px solid var(--border);
    border-radius: 8px;
  }}

  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 13.5px;
    background: #fff;
  }}

  th {{
    background-color: #F1F5F9;
    color: #1E293B;
    font-weight: 600;
    text-align: left;
    padding: 12px 14px;
    border-bottom: 2px solid var(--border);
  }}

  td {{
    padding: 10px 14px;
    border-bottom: 1px solid var(--border);
    color: #334155;
    vertical-align: top;
  }}

  tr:last-child td {{
    border-bottom: none;
  }}

  tr:nth-child(even) td {{
    background-color: #F8FAFC;
  }}

  pre {{
    background-color: #0F172A;
    color: #E2E8F0;
    padding: 16px 20px;
    border-radius: 8px;
    overflow-x: auto;
    font-family: 'JetBrains Mono', Consolas, Monaco, monospace;
    font-size: 13px;
    line-height: 1.5;
    margin: 18px 0;
  }}

  code {{
    font-family: 'JetBrains Mono', Consolas, monospace;
    font-size: 13px;
    background-color: #F1F5F9;
    color: #0F172A;
    padding: 2px 6px;
    border-radius: 4px;
  }}

  pre code {{
    background-color: transparent;
    color: inherit;
    padding: 0;
  }}

  .alert {{
    border-radius: 8px;
    padding: 16px 20px;
    margin: 20px 0;
    display: flex;
    gap: 14px;
    border-left: 4px solid;
  }}

  .alert-important {{
    background-color: #EFF6FF;
    border-color: #2563EB;
    color: #1E40AF;
  }}

  .alert-note {{
    background-color: #F0FDF4;
    border-color: #16A34A;
    color: #166534;
  }}

  .alert-warning {{
    background-color: #FFFBEB;
    border-color: #D97706;
    color: #92400E;
  }}

  .alert-content {{
    font-size: 13.5px;
    line-height: 1.55;
  }}

  a {{
    color: var(--accent);
    text-decoration: none;
  }}
  a:hover {{
    text-decoration: underline;
  }}

  /* Print & PDF optimization */
  @media print {{
    body {{
      background: #fff;
      padding: 0;
      font-size: 11pt;
    }}
    .container {{
      max-width: 100%;
      box-shadow: none;
      border: none;
      padding: 0;
    }}
    h1 {{
      font-size: 20pt;
      margin-top: 0;
    }}
    h2 {{
      font-size: 14pt;
      page-break-after: avoid;
      margin-top: 24pt;
    }}
    h3 {{
      font-size: 12pt;
      page-break-after: avoid;
    }}
    table {{
      page-break-inside: avoid;
      font-size: 9.5pt;
    }}
    tr {{
      page-break-inside: avoid;
    }}
    pre {{
      page-break-inside: avoid;
      font-size: 8.5pt;
      padding: 10pt;
    }}
    .alert {{
      page-break-inside: avoid;
    }}
    hr {{
      margin: 16pt 0;
    }}
  }}
</style>
</head>
<body>
<div class="container">
{html_body}
</div>
</body>
</html>
"""

html_path.write_text(full_html, encoding="utf-8")
print(f"Generated HTML: {html_path}")

# Run edge headless to export PDF
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
cmd = [
    edge_path,
    "--headless",
    "--disable-gpu",
    f"--print-to-pdf={pdf_path}",
    str(html_path)
]
res = subprocess.run(cmd, capture_output=True, text=True)
if res.returncode == 0 and pdf_path.exists():
    print(f"Successfully generated PDF: {pdf_path} (Size: {pdf_path.stat().st_size} bytes)")
else:
    print(f"PDF generation output: {res.stderr}")
