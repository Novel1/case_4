"""
Сборка Sulpak Notes в один самодостаточный index.html (без внешних запросов):
CSS, движок sql.js (SQLite -> WebAssembly) и логика приложения инлайнятся
прямо в файл, wasm-бинарник встраивается как base64 data URI.

Запуск:
    python build.py
Результат:
    index.html — открывается двойным кликом в любом браузере,
    либо публикуется как есть (одностраничное веб-приложение / PWA).
"""
import base64
import json
import pathlib

ROOT = pathlib.Path(__file__).parent
SQLJS_DIST = ROOT / "node_modules" / "sql.js" / "dist"

css = (ROOT / "style.css").read_text(encoding="utf-8")
app_js = (ROOT / "app_logic.js").read_text(encoding="utf-8")
sqljs_glue = (SQLJS_DIST / "sql-wasm.js").read_text(encoding="utf-8")
wasm_b64 = base64.b64encode((SQLJS_DIST / "sql-wasm.wasm").read_bytes()).decode("ascii")

manifest = {
    "name": "Sulpak Notes",
    "short_name": "Sulpak Notes",
    "start_url": ".",
    "display": "standalone",
    "background_color": "#f4f5f7",
    "theme_color": "#e0592a",
}
manifest_data_uri = "data:application/manifest+json," + json.dumps(manifest).replace('"', '%22').replace(" ", "%20")

html = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8" />
<title>Sulpak Notes</title>
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
<meta name="theme-color" content="#e0592a" />
<meta name="mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="Sulpak Notes" />
<link rel="manifest" href="__MANIFEST__" />
<style>
__CSS__
</style>
</head>
<body>
<div class="app">
  <header class="topbar">
    <h1><span class="logo">S</span> Sulpak Notes</h1>
    <div class="search">
      <span>🔎</span>
      <input id="searchInput" type="text" placeholder="Поиск по заголовку, тексту, дате…" />
    </div>
  </header>

  <nav class="tabs">
    <button id="tabDb" class="active">База данных (SQLite)</button>
    <button id="tabFiles">Файлы устройства</button>
  </nav>

  <main id="main"></main>

  <button class="fab" id="fab" title="Новая заметка">+</button>

  <div class="overlay hidden" id="overlay">
    <div class="sheet">
      <h2 id="sheetHeading">Новая заметка</h2>
      <div class="field">
        <label>Заголовок</label>
        <input id="sheetTitleInput" type="text" placeholder="Например: Совещание по продажам" />
      </div>
      <div class="field">
        <label>Содержание</label>
        <textarea id="sheetContentInput" placeholder="Текст заметки…"></textarea>
      </div>
      <div class="sheet-actions">
        <button class="btn ghost" id="sheetCancel">Отмена</button>
        <button class="btn primary" id="sheetSave">Сохранить</button>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>
  <footer class="status" id="statusLine">Загрузка SQLite…</footer>
</div>

<script>
// ---- sql.js (SQLite, скомпилированный в WebAssembly) — встроен целиком, без внешних запросов ----
__SQLJS_GLUE__
</script>
<script>
// ---- wasm-бинарник sql.js, встроенный как base64 data URI (офлайн, без CDN) ----
var SQLJS_WASM_BASE64 = "__WASM_B64__";
function base64ToBlobUrl(b64, mime){
  var binary = atob(b64);
  var bytes = new Uint8Array(binary.length);
  for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return URL.createObjectURL(new Blob([bytes], {type: mime}));
}
var SQLJS_WASM_URL = base64ToBlobUrl(SQLJS_WASM_BASE64, "application/wasm");

initSqlJs({ locateFile: function () { return SQLJS_WASM_URL; } }).then(function (SQL) {
  window.SulpakNotesApp.start(SQL);
}).catch(function (err) {
  document.getElementById("main").innerHTML =
    '<p class="empty">Не удалось загрузить SQLite (sql.js): ' + err + '</p>';
});
</script>
<script>
__APP_JS__
</script>
</body>
</html>
"""

html = (html
        .replace("__CSS__", css)
        .replace("__SQLJS_GLUE__", sqljs_glue)
        .replace("__WASM_B64__", wasm_b64)
        .replace("__APP_JS__", app_js)
        .replace("__MANIFEST__", manifest_data_uri))

out_path = ROOT / "index.html"
out_path.write_text(html, encoding="utf-8")
print("Собрано:", out_path, "-", round(out_path.stat().st_size / 1024), "KB")
