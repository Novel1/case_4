/* Sulpak Notes — заметки для сотрудников (совещания, встречи, конференции).
 * Хранение: (1) база данных SQLite (через sql.js, персистится в localStorage)
 *           (2) файловая система устройства (экспорт/импорт каждой заметки файлом)
 * Функции: создание / редактирование / удаление / поиск заметок.
 */
(function () {
  "use strict";

  var DB_STORAGE_KEY = "sulpak_notes_sqlite_v1";
  var db = null;
  var editingId = null;
  var currentTab = "db"; // "db" | "files"

  var els = {};

  function $(sel) { return document.querySelector(sel); }

  function toast(msg) {
    var t = els.toast;
    t.textContent = msg;
    t.classList.add("show");
    clearTimeout(toast._h);
    toast._h = setTimeout(function () { t.classList.remove("show"); }, 1800);
  }

  // ---------- Персистентность SQLite (localStorage) ----------
  function saveDbToStorage() {
    try {
      var data = db.export(); // Uint8Array
      var binary = "";
      for (var i = 0; i < data.length; i++) binary += String.fromCharCode(data[i]);
      localStorage.setItem(DB_STORAGE_KEY, btoa(binary));
    } catch (e) {
      console.error("Не удалось сохранить БД в localStorage:", e);
    }
  }

  function loadDbFromStorage(SQL) {
    var b64 = localStorage.getItem(DB_STORAGE_KEY);
    if (!b64) return new SQL.Database();
    try {
      var binary = atob(b64);
      var bytes = new Uint8Array(binary.length);
      for (var i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
      return new SQL.Database(bytes);
    } catch (e) {
      console.error("Повреждённая БД в localStorage, создаю новую:", e);
      return new SQL.Database();
    }
  }

  function ensureSchema() {
    db.run(
      "CREATE TABLE IF NOT EXISTS notes (" +
      " id INTEGER PRIMARY KEY AUTOINCREMENT," +
      " title TEXT NOT NULL," +
      " content TEXT NOT NULL DEFAULT ''," +
      " created_at TEXT NOT NULL," +
      " updated_at TEXT NOT NULL" +
      ")"
    );
  }

  // ---------- CRUD ----------
  function nowIso() {
    return new Date().toISOString();
  }

  function addNote(title, content) {
    var ts = nowIso();
    db.run("INSERT INTO notes (title, content, created_at, updated_at) VALUES (?, ?, ?, ?)",
      [title, content, ts, ts]);
    saveDbToStorage();
  }

  function updateNote(id, title, content) {
    db.run("UPDATE notes SET title=?, content=?, updated_at=? WHERE id=?",
      [title, content, nowIso(), id]);
    saveDbToStorage();
  }

  function deleteNote(id) {
    db.run("DELETE FROM notes WHERE id=?", [id]);
    saveDbToStorage();
  }

  function queryNotes(search) {
    var sql, params;
    if (search && search.trim()) {
      var like = "%" + search.trim().toLowerCase() + "%";
      sql = "SELECT * FROM notes WHERE lower(title) LIKE ? OR lower(content) LIKE ? OR created_at LIKE ? " +
            "ORDER BY updated_at DESC";
      params = [like, like, like];
    } else {
      sql = "SELECT * FROM notes ORDER BY updated_at DESC";
      params = [];
    }
    var stmt = db.prepare(sql);
    stmt.bind(params);
    var rows = [];
    while (stmt.step()) rows.push(stmt.getAsObject());
    stmt.free();
    return rows;
  }

  function getNote(id) {
    var stmt = db.prepare("SELECT * FROM notes WHERE id=?");
    stmt.bind([id]);
    var row = stmt.step() ? stmt.getAsObject() : null;
    stmt.free();
    return row;
  }

  // ---------- Рендеринг ----------
  function fmtDate(iso) {
    var d = new Date(iso);
    return d.toLocaleDateString("ru-RU") + " " + d.toLocaleTimeString("ru-RU", {hour:"2-digit", minute:"2-digit"});
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function (c) {
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];
    });
  }

  function renderList() {
    var search = els.search.value;
    var rows = queryNotes(search);
    if (rows.length === 0) {
      els.main.innerHTML = '<p class="empty">' +
        (search ? "Ничего не найдено по запросу «" + escapeHtml(search) + "»." :
                  "Пока нет заметок.<br>Нажмите «+», чтобы создать первую.") +
        "</p>";
      return;
    }
    var html = "";
    rows.forEach(function (n) {
      html += '<div class="note-card" data-id="' + n.id + '">' +
        '<div class="row"><h3>' + escapeHtml(n.title) + '</h3>' +
        '<div class="note-actions">' +
        '<button class="icon-btn" data-act="edit" data-id="' + n.id + '" title="Редактировать">✎</button>' +
        '<button class="icon-btn danger" data-act="del" data-id="' + n.id + '" title="Удалить">🗑</button>' +
        '</div></div>' +
        '<time>' + fmtDate(n.updated_at) + '</time>' +
        '<p>' + escapeHtml(n.content) + '</p>' +
        '</div>';
    });
    els.main.innerHTML = html;
  }

  function renderFilesTab() {
    var rows = queryNotes("");
    var html = '<div class="filepanel">' +
      '<p class="hint">Каждую заметку можно сохранить как отдельный файл на устройстве ' +
      '(<code>.txt</code>) — второй способ хранения данных, независимый от базы SQLite. ' +
      'Файл можно передать коллеге или загрузить обратно в приложение.</p>';
    if (rows.length === 0) {
      html += '<p class="empty">Нет заметок для экспорта.</p>';
    } else {
      rows.forEach(function (n) {
        html += '<div class="file-row"><span>' + escapeHtml(n.title) + '</span>' +
          '<button class="icon-btn" data-act="export" data-id="' + n.id + '" title="Сохранить как файл">⬇</button></div>';
      });
    }
    html += '<div class="import-drop">Импортировать заметку из файла (.txt)' +
      '<input type="file" id="importFile" accept=".txt,.json" /></div>' +
      '</div>';
    els.main.innerHTML = html;
  }

  function render() {
    if (currentTab === "db") renderList(); else renderFilesTab();
  }

  // ---------- Файловое хранилище (экспорт/импорт одной заметки файлом) ----------
  function exportNoteAsFile(id) {
    var n = getNote(id);
    if (!n) return;
    var body = n.title + "\n" + fmtDate(n.created_at) + "\n\n" + n.content;
    var blob = new Blob([body], {type: "text/plain;charset=utf-8"});
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    var safeName = n.title.replace(/[\\/:*?"<>|]/g, "_").slice(0, 40) || "note";
    a.href = url;
    a.download = safeName + ".txt";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 2000);
    toast("Заметка сохранена как файл " + a.download);
  }

  function importNoteFromFile(file) {
    var reader = new FileReader();
    reader.onload = function () {
      var text = String(reader.result);
      var lines = text.split("\n");
      var title = (lines[0] || file.name.replace(/\.[^.]+$/, "")).trim() || "Импортированная заметка";
      var content = lines.slice(2).join("\n").trim() || text.trim();
      addNote(title, content);
      toast("Заметка импортирована из файла");
      renderFilesTab();
    };
    reader.readAsText(file, "utf-8");
  }

  // ---------- Форма создания/редактирования (bottom sheet) ----------
  function openSheet(id) {
    editingId = id || null;
    if (id) {
      var n = getNote(id);
      els.sheetTitleInput.value = n.title;
      els.sheetContentInput.value = n.content;
      els.sheetHeading.textContent = "Редактировать заметку";
    } else {
      els.sheetTitleInput.value = "";
      els.sheetContentInput.value = "";
      els.sheetHeading.textContent = "Новая заметка";
    }
    els.overlay.classList.remove("hidden");
    els.sheetTitleInput.focus();
  }

  function closeSheet() {
    els.overlay.classList.add("hidden");
    editingId = null;
  }

  function saveSheet() {
    var title = els.sheetTitleInput.value.trim();
    var content = els.sheetContentInput.value.trim();
    if (!title) { toast("Введите заголовок заметки"); return; }
    if (editingId) updateNote(editingId, title, content);
    else addNote(title, content);
    closeSheet();
    render();
    toast(editingId ? "Заметка обновлена" : "Заметка создана");
  }

  // ---------- Инициализация ----------
  function bindEvents() {
    els.tabDb.addEventListener("click", function () {
      currentTab = "db";
      els.tabDb.classList.add("active");
      els.tabFiles.classList.remove("active");
      els.search.parentElement.style.display = "flex";
      render();
    });
    els.tabFiles.addEventListener("click", function () {
      currentTab = "files";
      els.tabFiles.classList.add("active");
      els.tabDb.classList.remove("active");
      els.search.parentElement.style.display = "none";
      render();
    });
    els.search.addEventListener("input", function () { if (currentTab === "db") renderList(); });
    els.fab.addEventListener("click", function () { openSheet(null); });
    els.sheetCancel.addEventListener("click", closeSheet);
    els.sheetSave.addEventListener("click", saveSheet);
    els.overlay.addEventListener("click", function (e) { if (e.target === els.overlay) closeSheet(); });

    els.main.addEventListener("click", function (e) {
      var btn = e.target.closest("button[data-act]");
      if (!btn) return;
      var id = Number(btn.getAttribute("data-id"));
      var act = btn.getAttribute("data-act");
      if (act === "edit") openSheet(id);
      else if (act === "del") {
        if (confirm("Удалить заметку?")) { deleteNote(id); render(); toast("Заметка удалена"); }
      } else if (act === "export") exportNoteAsFile(id);
    });

    els.main.addEventListener("change", function (e) {
      if (e.target && e.target.id === "importFile" && e.target.files[0]) {
        importNoteFromFile(e.target.files[0]);
      }
    });
  }

  function cacheEls() {
    els.main = $("#main");
    els.search = $("#searchInput");
    els.fab = $("#fab");
    els.tabDb = $("#tabDb");
    els.tabFiles = $("#tabFiles");
    els.overlay = $("#overlay");
    els.sheetHeading = $("#sheetHeading");
    els.sheetTitleInput = $("#sheetTitleInput");
    els.sheetContentInput = $("#sheetContentInput");
    els.sheetCancel = $("#sheetCancel");
    els.sheetSave = $("#sheetSave");
    els.toast = $("#toast");
    els.status = $("#statusLine");
  }

  window.SulpakNotesApp = {
    start: function (SQL) {
      cacheEls();
      db = loadDbFromStorage(SQL);
      ensureSchema();
      bindEvents();
      render();
      els.status.textContent = "SQLite (sql.js) готов · заметок: " + queryNotes("").length;
    }
  };
})();
