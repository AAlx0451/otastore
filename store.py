import os
import re
import urllib.parse

BASE_URL = "https://aalx0451.github.io/otastore"
DB_FILE = "apps.dbapps"

GENRE_MAP = {
    "Games": "Игры", "Simulation": "Симуляторы", "Arcade": "Аркады", "Action": "Экшен",
    "Puzzle": "Головоломки", "Role Playing": "Ролевые", "Strategy": "Стратегии", "Racing": "Гонки",
    "Utilities": "Утилиты", "Productivity": "Производительность", "Social Networking": "Соцсети",
    "Photo & Video": "Фото и видео", "Entertainment": "Развлечения", "Education": "Образование"
}

CSS = """
:root { --bg: #fff; --txt: #000; --sec: #8e8e93; --acc: #007aff; --brd: #c8c7cc; --nav: #f8f8f8; --srch: #e4e4e5; }
body { font-family: -apple-system, sans-serif; background: var(--bg); color: var(--txt); margin: 0; padding-top: env(safe-area-inset-top); -webkit-user-select: none; user-select: none; -webkit-tap-highlight-color: transparent; }
.navbar { background: var(--nav); border-bottom: 0.5px solid var(--brd); height: 44px; display: flex; align-items: center; justify-content: center; position: sticky; top: env(safe-area-inset-top); z-index: 20; }
.back-btn { position: absolute; left: 8px; color: var(--acc); text-decoration: none; font-size: 17px; }
.title { font-weight: 600; font-size: 17px; }
.container { max-width: 640px; margin: 0 auto; padding-bottom: 40px; }
.btn-get { border: 1px solid var(--acc); color: var(--acc); padding: 4px 14px; border-radius: 4px; text-decoration: none; font-size: 13px; font-weight: 600; text-transform: uppercase; }
.btn-get:active { background: var(--acc); color: #fff; }
.app-list { list-style: none; margin: 0; padding: 0 0 0 16px; }
.app-item { display: flex; align-items: center; padding: 12px 16px 12px 0; border-bottom: 0.5px solid var(--brd); }
.app-link { display: flex; align-items: center; text-decoration: none; color: inherit; flex-grow: 1; }
.app-link:active { opacity: 0.5; }
.app-icon { width: 60px; height: 60px; border-radius: 13px; border: 0.5px solid rgba(0,0,0,0.1); margin-right: 12px; object-fit: cover; }
.app-info { display: flex; flex-direction: column; }
.app-name { font-size: 16px; font-weight: 500; margin-bottom: 4px; }
.app-cat { font-size: 12px; color: var(--sec); }
.ctrl-box { padding: 10px 16px; border-bottom: 0.5px solid var(--brd); background: var(--bg); position: sticky; top: calc(env(safe-area-inset-top) + 44px); z-index: 10; display: flex; flex-direction: column; gap: 10px; }
.input-box { width: 100%; padding: 8px 12px; border-radius: 10px; border: none; background: var(--srch); font-size: 16px; box-sizing: border-box; -webkit-appearance: none; font-family: inherit; }
.input-box:focus { outline: none; }
.select-wrap { position: relative; width: 100%; }
.select-wrap::after { content: '▼'; font-size: 10px; color: var(--sec); position: absolute; right: 14px; top: 50%; transform: translateY(-50%); pointer-events: none; }
.det-head { display: flex; padding: 20px 16px; border-bottom: 0.5px solid var(--brd); }
.det-icon { width: 100px; height: 100px; border-radius: 22px; margin-right: 16px; object-fit: cover; border: 0.5px solid rgba(0,0,0,0.1); }
.det-meta { display: flex; flex-direction: column; flex-grow: 1; }
.det-title { font-size: 20px; font-weight: 500; margin: 0 0 4px 0; }
.det-act { margin-top: auto; margin-bottom: 4px; }
.section { padding: 16px; border-bottom: 0.5px solid var(--brd); }
.sec-title { font-size: 15px; text-transform: uppercase; color: var(--sec); margin: 0 0 10px 0; font-weight: 500; }
.desc { font-size: 14px; line-height: 1.4; white-space: pre-wrap; user-select: text; -webkit-user-select: text; margin: 0; }
.row { display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 0.5px solid var(--brd); font-size: 14px; }
.row:last-child { border-bottom: none; padding-bottom: 0; }
.lbl { color: var(--sec); }
.val { text-align: right; max-width: 60%; }
"""

INDEX_JS = """<script>
const qs = s => document.querySelector(s);
const filterApps = () => {
    const query = qs('#search').value.toLowerCase(), cat = qs('#cat').value;
    let count = 0;
    document.querySelectorAll('.app-item').forEach(el => {
        const match = el.dataset.title.includes(query) && (cat === 'all' || el.dataset.cat === cat);
        el.style.display = match ? 'flex' : 'none';
        if (match) count++;
    });
    qs('#no-res').style.display = count ? 'none' : 'block';
};
qs('#search').addEventListener('input', filterApps);
qs('#cat').addEventListener('change', filterApps);
</script>"""

def render_page(title, nav, body, script=""):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>{title}</title>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <script>
        if (window.navigator.standalone) {{
            document.addEventListener('click', e => {{
                let a = e.target.closest('a');
                if (a && a.href.startsWith('http') && a.href.includes(location.host)) {{
                    e.preventDefault(); location.href = a.href;
                }}
            }});
        }}
    </script>
    <style>{CSS}</style>
</head>
<body>
    <div class="navbar">{nav}</div>
    <div class="container">{body}</div>
    {script}
</body>
</html>"""

def make_plist(ipa_url, icon_url, bid, ver, title):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>items</key>
    <array>
        <dict>
            <key>assets</key>
            <array>
                <dict>
                    <key>kind</key>
                    <string>software-package</string>
                    <key>url</key>
                    <string>{ipa_url}</string>
                </dict>
                <dict>
                    <key>kind</key>
                    <string>display-image</string>
                    <key>needs-shine</key>
                    <true/>
                    <key>url</key>
                    <string>{icon_url}</string>
                </dict>
                <dict>
                    <key>kind</key>
                    <string>full-size-image</string>
                    <key>needs-shine</key>
                    <true/>
                    <key>url</key>
                    <string>{icon_url}</string>
                </dict>
            </array>
            <key>metadata</key>
            <dict>
                <key>bundle-identifier</key>
                <string>{bid}</string>
                <key>bundle-version</key>
                <string>{ver}</string>
                <key>kind</key>
                <string>software</string>
                <key>title</key>
                <string>{title}</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>"""

def parse_db(path):
    try:
        with open(path, 'r', encoding='utf-8') as f: content = f.read()
    except Exception:
        return []
    
    apps = []
    for block in content.split('---'):
        if 'skip;' in block or not block.strip(): continue
        
        desc_match = re.search(r'\$start\s*(.*?)\s*\$end', block, re.DOTALL)
        app = {'Description': desc_match.group(1).strip() if desc_match else 'Нет описания.'}
        block = re.sub(r'\$start.*?\$end', '', block, flags=re.DOTALL)
        
        for line in block.splitlines():
            if ':' in line and not line.strip().startswith('#'):
                k, v = line.split(':', 1)
                if k.strip() != 'Description':
                    app[k.strip()] = v.strip()
                
        if 'Package' in app: apps.append(app)
    return apps

def save_file(path, content):
    with open(path, "w", encoding="utf-8") as f: f.write(content)

def main():
    os.makedirs("manifests", exist_ok=True)
    os.makedirs("apps", exist_ok=True)
    
    apps = parse_db(DB_FILE)
    if not apps: return print("База пуста или файл отсутствует.")

    index_items, categories = [], set()

    for app in apps:
        title = app.get('Package', 'App')
        slug = re.sub(r'[^a-z0-9_-]', '_', title.lower()).strip('_')
        ver, os_ver = app.get('Version', '1.0'), app.get('OSRelVer', '7.0')
        icon, desc = app.get('IconRelPath', ''), app.get('Description', '')
        
        raw_size = app.get('FileSize', '0')
        size = f"{int(raw_size)/(1024*1024):.1f} МБ" if raw_size.isdigit() else "Неизвестно"
        
        parts = [GENRE_MAP.get(p.strip(), p.strip()) for p in app.get('Genre', '').split('::') if p.strip()] or ["Приложения"]
        cat_short = parts[0]
        cat_full = f"{parts[0]} ({parts[1]})" if len(parts) > 1 else parts[0]
        categories.add(cat_short)

        icon_abs = icon if icon.startswith(('http://', 'https://')) else f"{BASE_URL}/{icon}"

        plist_path = f"manifests/{slug}.plist"
        save_file(plist_path, make_plist(app.get('DirectFileLink', ''), icon_abs, f"com.ota.{slug}", ver, title))
        itms = f"itms-services://?action=download-manifest&url={urllib.parse.quote(f'{BASE_URL}/{plist_path}', safe='')}"
        
        icon_rel = f"../{icon}" if icon and not icon.startswith(('http://', 'https://')) else icon
        icon_err = "this.outerHTML='<div class=\\'app-icon\\' style=\\'background:#eee\\'></div>'"
        det_icon_err = "this.outerHTML='<div class=\\'det-icon\\' style=\\'background:#eee\\'></div>'"

        det_body = f"""
        <div class="det-head">
            <img class="det-icon" src="{icon_rel}" onerror="{det_icon_err}">
            <div class="det-meta">
                <h1 class="det-title">{title}</h1>
                <div class="app-cat">{cat_full}</div>
                <div class="det-act"><a href="{itms}" class="btn-get">Загрузить</a></div>
            </div>
        </div>
        <div class="section"><h2 class="sec-title">Описание</h2><div class="desc">{desc}</div></div>
        <div class="section"><h2 class="sec-title">Информация</h2>
            <div class="row"><span class="lbl">Размер</span><span class="val">{size}</span></div>
            <div class="row"><span class="lbl">Категория</span><span class="val">{cat_short}</span></div>
            <div class="row"><span class="lbl">ОС</span><span class="val">iOS {os_ver} или новее</span></div>
            <div class="row"><span class="lbl">Версия</span><span class="val">{ver}</span></div>
        </div>"""
        
        nav_back = '<a href="../index.html" class="back-btn">&#10094; OTAStore</a><span class="title">Описание</span>'
        save_file(f"apps/{slug}.html", render_page(title, nav_back, det_body))

        index_items.append(f"""
        <li class="app-item" data-title="{title.lower().replace('"', '')}" data-cat="{cat_short.replace('"', '')}">
            <a href="apps/{slug}.html" class="app-link">
                <img class="app-icon" src="{icon}" onerror="{icon_err}">
                <div class="app-info"><span class="app-name">{title}</span><span class="app-cat">{cat_full}</span></div>
            </a>
            <div class="action-container"><a href="{itms}" class="btn-get">Загрузить</a></div>
        </li>""")

    options_html = "".join(f'<option value="{c}">{c}</option>' for c in sorted(categories))
    
    index_body = f"""
    <h1 style="font-size:34px; font-weight:300; margin:16px 16px 8px 16px; border-bottom:0.5px solid var(--brd);">Игры и Приложения</h1>
    <div class="ctrl-box">
        <input type="search" id="search" class="input-box" placeholder="Поиск..." autocomplete="off">
        <div class="select-wrap">
            <select id="cat" class="input-box"><option value="all">Все категории</option>{options_html}</select>
        </div>
    </div>
    <ul class="app-list">{''.join(index_items)}</ul>
    <div id="no-res" style="text-align:center; padding:30px; color:var(--sec); font-size:15px; display:none;">Ничего не найдено</div>
    """
    
    save_file("index.html", render_page("OTAStore", '<span class="title">OTAStore</span>', index_body, INDEX_JS))
    print(f"Success. Processed apps: {len(apps)}. Categories: {len(categories)}")

if __name__ == "__main__":
    main()
