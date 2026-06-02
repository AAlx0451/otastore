import os
import re
import urllib.parse
import time
import sys
import html

BASE_URL = "https://aalx0451.github.io/otastore"
DB_FILE = "apps.dbapps"

GENRE_MAP = {
    "Games": "Игры", "Simulation": "Симуляторы", "Arcade": "Аркады", "Action": "Экшен",
    "Puzzle": "Головоломки", "Role Playing": "Ролевые", "Strategy": "Стратегии", "Racing": "Гонки",
    "Utilities": "Утилиты", "Productivity": "Производительность", "Social Networking": "Соцсети",
    "Photo & Video": "Фото и видео", "Entertainment": "Развлечения", "Education": "Образование"
}

CSS = """
:root{--bg:#fff;--txt:#000;--sec:#8e8e93;--acc:#007aff;--brd:#c8c7cc;--nav:#f8f8f8;--srch:#e4e4e5}
body{font-family:-apple-system,sans-serif;background:var(--bg);color:var(--txt);margin:0;padding-top:env(safe-area-inset-top);-webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
.navbar{background:var(--nav);border-bottom:.5px solid var(--brd);height:44px;display:flex;align-items:center;justify-content:center;position:sticky;top:env(safe-area-inset-top);z-index:20}
.back-btn{position:absolute;left:8px;color:var(--acc);text-decoration:none;font-size:17px}
.title{font-weight:600;font-size:17px}
.container{max-width:640px;margin:0 auto;padding-bottom:40px}
.btn-get{border:1px solid var(--acc);color:var(--acc);background:0 0;padding:4px 14px;border-radius:4px;text-decoration:none;font-size:13px;font-weight:600;text-transform:uppercase;transition:background-color .1s,color .1s,border-color .1s}
.btn-get:active{background-color:var(--acc)!important;color:#fff!important}
.btn-get.state-install{border-color:#4cd964!important;color:#4cd964!important;background:0 0!important}
.btn-get.state-install:active{background-color:#4cd964!important;color:#fff!important}
.btn-get.state-open{border-color:#8e8e93!important;color:#8e8e93!important;background:0 0!important}
.btn-get.state-open:active{background-color:#8e8e93!important;color:#fff!important}
.app-list{list-style:none;margin:0;padding:0 0 0 16px}
.app-item{display:flex;align-items:center;padding:12px 16px 12px 0;border-bottom:.5px solid var(--brd)}
.app-link{display:flex;align-items:center;text-decoration:none;color:inherit;flex-grow:1}
.app-link:active{opacity:.5}
.app-icon{width:60px;height:60px;border-radius:13px;border:.5px solid rgba(0,0,0,.1);margin-right:12px;object-fit:cover}
.app-info{display:flex;flex-direction:column}
.app-name{font-size:16px;font-weight:500;margin-bottom:4px}
.app-cat{font-size:12px;color:var(--sec)}
.ctrl-box{padding:10px 16px;border-bottom:.5px solid var(--brd);background:var(--bg);position:sticky;top:calc(env(safe-area-inset-top) + 44px);z-index:10;display:flex;flex-direction:column;gap:10px}
.input-box{width:100%;padding:8px 12px;border-radius:10px;border:none;background:var(--srch);font-size:16px;box-sizing:border-box;-webkit-appearance:none;font-family:inherit}
.input-box:focus{outline:0}
.select-wrap{position:relative;width:100%}
.select-wrap::after{content:'▼';font-size:10px;color:var(--sec);position:absolute;right:14px;top:50%;transform:translateY(-50%);pointer-events:none}
.det-head{display:flex;padding:20px 16px;border-bottom:.5px solid var(--brd)}
.det-icon{width:100px;height:100px;border-radius:22px;margin-right:16px;object-fit:cover;border:.5px solid rgba(0,0,0,.1)}
.det-meta{display:flex;flex-direction:column;flex-grow:1}
.det-title{font-size:20px;font-weight:500;margin:0 0 4px 0}
.det-act{margin-top:auto;margin-bottom:4px}
.section{padding:16px;border-bottom:.5px solid var(--brd)}
.sec-title{font-size:15px;text-transform:uppercase;color:var(--sec);margin:0 0 10px 0;font-weight:500}
.desc{font-size:14px;line-height:1.4;white-space:pre-wrap;user-select:text;-webkit-user-select:text;margin:0}
.row{display:flex;justify-content:space-between;padding:12px 0;border-bottom:.5px solid var(--brd);font-size:14px}
.row:last-child{border-bottom:none;padding-bottom:0}
.lbl{color:var(--sec)}
.val{text-align:right;max-width:60%}
"""

GLOBAL_JS = """<script>
document.addEventListener('click', function (event) {
    var anchor = event.target.closest('a');
    if (!anchor) return;
    
    if (window.navigator.standalone && anchor.href && anchor.href.indexOf('http') === 0 && anchor.href.indexOf(location.host) !== -1) {
        event.preventDefault();
        location.href = anchor.href;
        return;
    }

    if (anchor.classList.contains('btn-get')) {
        if (!anchor.classList.contains('state-install') && !anchor.classList.contains('state-open')) {
            event.preventDefault();
            anchor.textContent = 'УСТАНОВИТЬ';
            anchor.classList.add('state-install');
        } else if (anchor.classList.contains('state-install')) {
            setTimeout(function () {
                anchor.textContent = 'ОТКРЫТЬ';
                anchor.classList.remove('state-install');
                anchor.classList.add('state-open');
            }, 400);
        }
    }
});

document.addEventListener('error', function (event) {
    var element = event.target;
    if (element.tagName === 'IMG' && (element.classList.contains('app-icon') || element.classList.contains('det-icon'))) {
        var replacement = document.createElement('div');
        replacement.className = element.className;
        replacement.style.background = '#eee';
        element.parentNode.replaceChild(replacement, element);
    }
}, true);
</script>"""

INDEX_JS = """<script>
(function () {
    var searchInput = document.getElementById('search');
    var categorySelect = document.getElementById('cat');
    var noResults = document.getElementById('no-res');
    var listItems = document.querySelectorAll('.app-item');
    var cachedItems = [];

    for (var idx = 0; idx < listItems.length; idx++) {
        var element = listItems[idx];
        cachedItems.push({
            element: element,
            title: element.getAttribute('data-title') || '',
            category: element.getAttribute('data-cat') || ''
        });
    }

    function filter() {
        var query = searchInput.value.toLowerCase();
        var selectedCategory = categorySelect.value;
        var matchCount = 0;

        for (var idx = 0; idx < cachedItems.length; idx++) {
            var cached = cachedItems[idx];
            var isMatched = cached.title.indexOf(query) !== -1 && (selectedCategory === 'all' || cached.category === selectedCategory);
            cached.element.style.display = isMatched ? 'flex' : 'none';
            if (isMatched) matchCount++;
        }
        noResults.style.display = matchCount ? 'none' : 'block';
    }

    searchInput.addEventListener('input', filter);
    categorySelect.addEventListener('change', filter);
})();
</script>"""

HAS_ERRORS = False

def esc(text):
    return html.escape(str(text), quote=True)

def log_warning(file, line, col, message):
    print(f"\033[1m{file}:{line}:{col}:\033[0m \033[1;35mwarning:\033[0m \033[1m{message}\033[0m")

def log_error(file, line, col, message):
    global HAS_ERRORS
    HAS_ERRORS = True
    print(f"\033[1m{file}:{line}:{col}:\033[0m \033[1;31merror:\033[0m \033[1m{message}\033[0m")

def render_page(title, nav, body, icon_path, script=""):
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no, viewport-fit=cover">
    <title>{esc(title)}</title>
    <meta name="apple-mobile-web-app-capable" content="yes">
    <meta name="apple-mobile-web-app-status-bar-style" content="default">
    <link class="apple-touch-icon" rel="apple-touch-icon" href="{esc(icon_path)}">
    <style>{CSS}</style>
</head>
<body>
    <div class="navbar">{nav}</div>
    <div class="container">{body}</div>
    {GLOBAL_JS}
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
                    <string>{esc(ipa_url)}</string>
                </dict>
                <dict>
                    <key>kind</key>
                    <string>display-image</string>
                    <key>url</key>
                    <string>{esc(icon_url)}</string>
                </dict>
                <dict>
                    <key>kind</key>
                    <string>full-size-image</string>
                    <key>url</key>
                    <string>{esc(icon_url)}</string>
                </dict>
            </array>
            <key>metadata</key>
            <dict>
                <key>bundle-identifier</key>
                <string>{esc(bid)}</string>
                <key>bundle-version</key>
                <string>{esc(ver)}</string>
                <key>kind</key>
                <string>software</string>
                <key>title</key>
                <string>{esc(title)}</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>"""

def validate_and_add(app, fields, file_path, apps, package_names):
    package_name = app.get("Package")
    if not package_name or "DirectFileLink" not in app:
        log_error(file_path, fields.get(next(iter(fields)), 1) if fields else 1, 1, "missing critical fields")
        return

    if package_name in package_names:
        log_error(file_path, fields.get("Package", 1), 1, f"duplicate package: '{package_name}'")
        return
    package_names.add(package_name)

    for field in ["Version", "OSRelVer", "FileSize", "IconRelPath", "Genre", "Description"]:
        if field not in app:
            log_warning(file_path, fields.get("Package", 1), 1, f"missing recommended field '{field}'")

    link = app.get("DirectFileLink", "")
    if link.startswith("http://"):
        log_warning(file_path, fields.get("DirectFileLink", 1), 1, "insecure URL scheme 'http://'")

    size = app.get("FileSize", "")
    if size:
        if not size.isdigit():
            log_error(file_path, fields.get("FileSize", 1), 1, f"non-integer FileSize '{size}'")
            return
        elif int(size) <= 0:
            log_warning(file_path, fields.get("FileSize", 1), 1, f"suspicious FileSize '{size}'")

    icon = app.get("IconRelPath", "")
    if icon:
        if icon.startswith("http://"):
            log_warning(file_path, fields.get("IconRelPath", 1), 1, "insecure URL scheme 'http://'")
        elif not icon.startswith("https://"):
            if not os.path.exists(icon):
                log_warning(file_path, fields.get("IconRelPath", 1), 1, f"missing icon file '{icon}'")
            elif not icon.lower().endswith(".png"):
                log_warning(file_path, fields.get("IconRelPath", 1), 1, f"format is not PNG '{icon}'")

    genre = app.get("Genre", "")
    if genre:
        for part in [p.strip() for p in genre.split("::") if p.strip()]:
            if part not in GENRE_MAP:
                log_warning(file_path, fields.get("Genre", 1), 1, f"unmapped genre '{part}'")

    os_ver = app.get("OSRelVer", "")
    if os_ver and not re.match(r"^\d+(\.\d+)*$", os_ver):
        log_warning(file_path, fields.get("OSRelVer", 1), 1, f"suspicious version '{os_ver}'")

    apps.append(app)

def parse_db(path):
    if not os.path.exists(path):
        log_error(path, 0, 0, "target database file is missing")
        return []

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    apps, current, fields, desc, package_names = [], {}, {}, [], set()
    in_desc, desc_start = False, 0

    for idx, line in enumerate(lines, 1):
        val = line.strip()
        if "$start" in val:
            if in_desc: log_error(path, idx, 1, "nested description")
            in_desc, desc_start = True, idx
        elif "$end" in val:
            if not in_desc: log_error(path, idx, 1, "unmatched end")
            in_desc = False
            current["Description"] = "\n".join(desc).strip()
            fields["Description"] = desc_start
            desc = []
        elif in_desc:
            desc.append(line.rstrip("\r\n"))
        elif not val or val.startswith("#") or "skip;" in val:
            continue
        elif val == "---":
            if current:
                validate_and_add(current, fields, path, apps, package_names)
            current, fields = {}, {}
        elif ":" in val:
            k, v = map(str.strip, val.split(":", 1))
            current[k], fields[k] = v, idx
        else:
            log_error(path, idx, 1, f"unparseable: '{val}'")

    if in_desc:
        log_error(path, desc_start, 1, "unclosed description")
    return apps

def save_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    start_time = time.perf_counter()
    print(f"\033[1;32m   Compiling\033[0m {DB_FILE}")

    if BASE_URL.endswith("/"):
        log_warning("build_store.py", 1, 1, "BASE_URL has a trailing slash, which might lead to malformed composite paths")

    os.makedirs("manifests", exist_ok=True)
    os.makedirs("apps", exist_ok=True)

    pillow_available = True
    try:
        from PIL import Image
    except ImportError:
        pillow_available = False
        log_warning("build_store.py", 1, 1, "PIL absent; automatic conversion disabled")

    apps = parse_db(DB_FILE)

    if HAS_ERRORS:
        print("\033[1;31mCompilation terminated: unresolved structural errors in db file.\033[0m")
        sys.exit(1)

    if not apps:
        log_warning(DB_FILE, 1, 1, "no applications compiled")
        sys.exit(0)

    index_items, categories = [], set()

    for app in apps:
        title = app.get("Package", "App")
        slug = re.sub(r"[^a-z0-9_-]", "_", title.lower()).strip("_")

        if not slug:
            log_error(DB_FILE, 1, 1, f"invalid slug for '{title}'")
            sys.exit(1)

        ver, os_ver = app.get("Version", "1.0"), app.get("OSRelVer", "7.0")
        icon, desc = app.get("IconRelPath", ""), app.get("Description", "")
        raw_size = app.get("FileSize", "0")
        size = f"{int(raw_size)/(1024*1024):.1f} МБ" if raw_size.isdigit() else "Неизвестно"

        parts = [GENRE_MAP.get(p.strip(), p.strip()) for p in app.get("Genre", "").split("::") if p.strip()] or ["Приложения"]
        cat_short = parts[0]
        cat_full = f"{parts[0]} ({parts[1]})" if len(parts) > 1 else parts[0]
        categories.add(cat_short)

        icon_png = icon
        if icon and not icon.startswith(("http://", "https://")):
            if not icon.lower().endswith(".png"):
                if not pillow_available:
                    log_error(DB_FILE, 1, 1, f"Pillow absent for converting '{icon}'")
                    sys.exit(1)
                base_path, _ = os.path.splitext(icon)
                icon_png = f"{base_path}.png"
                try:
                    if os.path.exists(icon):
                        with Image.open(icon) as img:
                            img.save(icon_png, "PNG")
                    else:
                        log_error(DB_FILE, 1, 1, f"missing file '{icon}'")
                        sys.exit(1)
                except Exception as e:
                    log_error(DB_FILE, 1, 1, f"icon build error '{icon}': {e}")
                    sys.exit(1)

        icon_abs = icon_png if icon_png.startswith(("http://", "https://")) else f"{BASE_URL}/{icon_png}"
        plist_path = f"manifests/{slug}.plist"
        save_file(plist_path, make_plist(app.get("DirectFileLink", ""), icon_abs, f"com.ota.{slug}", ver, title))
        itms = f"itms-services://?action=download-manifest&url={urllib.parse.quote(f'{BASE_URL}/{plist_path}', safe='')}"
        icon_rel = icon_png if icon_png.startswith(("http://", "https://")) else f"../{icon_png}"

        e = {
            "title": esc(title),
            "desc": esc(desc),
            "cat_full": esc(cat_full),
            "cat_short": esc(cat_short),
            "size": esc(size),
            "os_ver": esc(os_ver),
            "ver": esc(ver),
            "itms": esc(itms),
            "icon_rel": esc(icon_rel),
            "icon_png": esc(icon_png),
            "slug": esc(slug),
            "title_lower": esc(title.lower())
        }

        det_body = f"""
        <div class="det-head">
            <img class="det-icon" src="{e['icon_rel']}">
            <div class="det-meta">
                <h1 class="det-title">{e['title']}</h1>
                <div class="app-cat">{e['cat_full']}</div>
                <div class="det-act"><a href="{e['itms']}" class="btn-get">Загрузить</a></div>
            </div>
        </div>
        <div class="section"><h2 class="sec-title">Описание</h2><div class="desc">{e['desc']}</div></div>
        <div class="section"><h2 class="sec-title">Информация</h2>
            <div class="row"><span class="lbl">Размер</span><span class="val">{e['size']}</span></div>
            <div class="row"><span class="lbl">Категория</span><span class="val">{e['cat_short']}</span></div>
            <div class="row"><span class="lbl">ОС</span><span class="val">iOS {e['os_ver']} или новее</span></div>
            <div class="row"><span class="lbl">Версия</span><span class="val">{e['ver']}</span></div>
        </div>"""

        nav_back = '<a href="../index.html" class="back-btn">&#10094; OTAStore</a><span class="title">Описание</span>'
        save_file(f"apps/{slug}.html", render_page(title, nav_back, det_body, "../apple-touch-icon.png?v=3"))

        index_items.append(f"""
        <li class="app-item" data-title="{e['title_lower']}" data-cat="{e['cat_short']}">
            <a href="apps/{e['slug']}.html" class="app-link">
                <img class="app-icon" src="{e['icon_png']}">
                <div class="app-info"><span class="app-name">{e['title']}</span><span class="app-cat">{e['cat_full']}</span></div>
            </a>
            <div class="action-container"><a href="{e['itms']}" class="btn-get">Загрузить</a></div>
        </li>""")

    options_html = "".join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in sorted(categories))

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

    save_file("index.html", render_page("OTAStore", '<span class="title">OTAStore</span>', index_body, "apple-touch-icon.png?v=3", INDEX_JS))

    elapsed_time = time.perf_counter() - start_time
    print(f"\033[1;32m    Finished\033[0m build (index.html, apps/, manifests/) in {elapsed_time:.2f}s")

if __name__ == "__main__":
    main()
