import subprocess
import os
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
html_file = BASE_DIR / "alternative_design_v2_mockup.html"
html_content = html_file.read_text(encoding="utf-8")

# Path-neutral Chrome discovery
chrome_path = os.environ.get("CHROME_PATH")
if not chrome_path or not Path(chrome_path).exists():
    for candidate in [
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]:
        if candidate and Path(candidate).exists():
            chrome_path = candidate
            break

if not chrome_path:
    raise FileNotFoundError("Chrome executable not found on system.")

# Relative output directory
output_dir = BASE_DIR / "screenshots"
output_dir.mkdir(parents=True, exist_ok=True)

for p_num in range(1, 5):
    pid = f"p{p_num}"
    p_html = html_content
    # Deactivate all pages and activate target
    for other in ["p1", "p2", "p3", "p4"]:
        p_html = p_html.replace(f'id="{other}" class="report-page active"', f'id="{other}" class="report-page"')
    p_html = p_html.replace(f'id="{pid}" class="report-page"', f'id="{pid}" class="report-page active"')
    
    # Also activate the corresponding button in tabs
    p_html = p_html.replace('class="tab-btn active"', 'class="tab-btn"')
    p_html = p_html.replace(f'switchPage(\'{pid}\')"', f'switchPage(\'{pid}\')" class="tab-btn active"')
    
    # Force viewMode to 'actual' for crisp 1:1 render
    p_html = p_html.replace("let viewMode = 'fit';", "let viewMode = 'actual';")
    
    tmp_file = BASE_DIR / f"temp_{pid}.html"
    tmp_file.write_text(p_html, encoding="utf-8")
    
    out_img = output_dir / f"mockup_page_{p_num}.png"
    cmd = [
        chrome_path,
        "--headless",
        "--disable-gpu",
        "--window-size=1600,1020",
        "--hide-scrollbars",
        f"--screenshot={out_img}",
        str(tmp_file)
    ]
    subprocess.run(cmd, check=True)
    tmp_file.unlink()
    print(f"Captured Page {p_num} -> {out_img} (Size: {out_img.stat().st_size} bytes)")

print("ALL 4 SCREENSHOTS SUCCESSFULLY CAPTURED!")
