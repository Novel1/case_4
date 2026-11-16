"""
Генерация иллюстраций-макетов экрана приложения (для руководства пользователя,
пункт кейс-задачи №4: "руководство с иллюстрациями"). Скриншот живого браузера
недоступен в текущей среде выполнения — вместо него нарисованы точные по
компоновке и цветам wireframe-макеты трёх экранов на основе реального CSS
приложения (style.css). Реальный скриншот с телефона/браузера можно
подставить вместо этих макетов при финальной сдаче отчёта.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 375, 812
ACCENT = (224, 89, 42)
BG = (244, 245, 247)
CARD = (255, 255, 255)
BORDER = (229, 231, 235)
TEXT = (28, 30, 33)
MUTED = (107, 114, 128)
DANGER = (217, 67, 46)


def font(size, bold=False):
    names = ["segoeuib.ttf", "arialbd.ttf"] if bold else ["segoeui.ttf", "arial.ttf"]
    for n in names:
        try:
            return ImageFont.truetype(n, size)
        except Exception:
            continue
    return ImageFont.load_default()


def base_canvas():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)
    return img, d


def header(d, title="Sulpak Notes", search_placeholder="Поиск по заголовку, тексту, дате…"):
    d.rectangle([0, 0, W, 96], fill=ACCENT)
    d.rounded_rectangle([16, 14, 16 + 26, 14 + 26], radius=7, fill=CARD)
    d.text((22, 18), "S", font=font(14, True), fill=ACCENT)
    d.text((50, 16), title, font=font(17, True), fill=(255, 255, 255))
    d.rounded_rectangle([16, 54, W - 16, 54 + 34], radius=10, fill=(255, 255, 255, 40), outline=None)
    d.text((28, 62), "🔎  " + search_placeholder, font=font(12), fill=(255, 240, 235))


def tabs(d, active="db"):
    d.rectangle([0, 96, W, 96 + 40], fill=CARD)
    d.line([0, 96 + 40, W, 96 + 40], fill=BORDER, width=1)
    labels = [("db", "База данных (SQLite)"), ("files", "Файлы устройства")]
    half = W // 2
    for i, (key, label) in enumerate(labels):
        cx = half // 2 + i * half
        color = ACCENT if key == active else MUTED
        d.text((cx - 60, 108), label, font=font(11, key == active), fill=color)
        if key == active:
            d.line([i * half + 20, 96 + 39, i * half + half - 20, 96 + 39], fill=ACCENT, width=2)


def note_card(d, y, title, date, preview):
    x0, x1 = 14, W - 14
    h = 96
    d.rounded_rectangle([x0, y, x1, y + h], radius=12, fill=CARD, outline=BORDER)
    d.text((x0 + 14, y + 12), title, font=font(14, True), fill=TEXT)
    d.text((x1 - 66, y + 14), "✎", font=font(13), fill=TEXT)
    d.text((x1 - 34, y + 14), "🗑", font=font(13), fill=DANGER)
    d.text((x0 + 14, y + 34), date, font=font(10), fill=MUTED)
    d.text((x0 + 14, y + 52), preview, font=font(11), fill=TEXT)
    return y + h + 10


def fab(d):
    cx, cy, r = W - 20 - 28, H - 24 - 28, 28
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=ACCENT)
    d.text((cx - 8, cy - 15), "+", font=font(26, True), fill=(255, 255, 255))


def screen_list():
    img, d = base_canvas()
    header(d)
    tabs(d, "db")
    y = 96 + 40 + 12
    y = note_card(d, y, "Совещание по продажам", "24.08.2026 10:15",
                  "Обсудили план продаж на квартал,")
    y = note_card(d, y, "Конференция по цифровизации", "23.08.2026 16:40",
                  "Обзор новых сервисов приложения Sulpak")
    y = note_card(d, y, "Встреча с поставщиком Xiaomi", "22.08.2026 09:00",
                  "Условия поставки на следующий квартал")
    fab(d)
    d.rectangle([0, H - 26, W, H], fill=CARD)
    d.line([0, H - 26, W, H - 26], fill=BORDER)
    d.text((70, H - 20), "SQLite (sql.js) готов · заметок: 3", font=font(10), fill=MUTED)
    img.save("mockup_1_list.png")


def screen_editor():
    img, d = base_canvas()
    header(d)
    tabs(d, "db")
    y = 96 + 40 + 12
    note_card(d, y, "Совещание по продажам", "24.08.2026 10:15", "Обсудили план продаж")

    # затемнение фона под модальным окном (как полупрозрачный overlay в приложении)
    dark = Image.new("RGB", (W, H), (0, 0, 0))
    img = Image.blend(img, dark, 0.35)
    d = ImageDraw.Draw(img)

    sheet_y = 230
    d.rounded_rectangle([0, sheet_y, W, H], radius=0, fill=CARD)
    d.rounded_rectangle([0, sheet_y, W, sheet_y + 16], radius=16, fill=CARD)
    d.text((18, sheet_y + 16), "Новая заметка", font=font(16, True), fill=TEXT)
    d.text((18, sheet_y + 56), "ЗАГОЛОВОК", font=font(10, True), fill=MUTED)
    d.rounded_rectangle([18, sheet_y + 72, W - 18, sheet_y + 104], radius=9, fill=BG, outline=BORDER)
    d.text((28, sheet_y + 80), "Например: Совещание по продажам", font=font(11), fill=MUTED)
    d.text((18, sheet_y + 118), "СОДЕРЖАНИЕ", font=font(10, True), fill=MUTED)
    d.rounded_rectangle([18, sheet_y + 134, W - 18, sheet_y + 240], radius=9, fill=BG, outline=BORDER)
    d.text((28, sheet_y + 142), "Текст заметки…", font=font(11), fill=MUTED)
    d.rounded_rectangle([18, sheet_y + 255, 18 + 160, sheet_y + 255 + 42], radius=10, fill=BG, outline=BORDER)
    d.text((18 + 55, sheet_y + 268), "Отмена", font=font(13, True), fill=MUTED)
    d.rounded_rectangle([18 + 170, sheet_y + 255, W - 18, sheet_y + 255 + 42], radius=10, fill=ACCENT)
    d.text((18 + 210, sheet_y + 268), "Сохранить", font=font(13, True), fill=(255, 255, 255))
    img.save("mockup_2_editor.png")


def screen_files():
    img, d = base_canvas()
    header(d)
    tabs(d, "files")
    y = 96 + 40 + 16
    d.multiline_text((18, y), "Каждую заметку можно сохранить как отдельный\n"
                              "файл на устройстве (.txt) — второй способ\n"
                              "хранения, независимый от базы SQLite.",
                      font=font(11), fill=MUTED, spacing=5)
    y += 70
    for title in ["Совещание по продажам", "Конференция по цифровизации", "Встреча с поставщиком Xiaomi"]:
        d.rounded_rectangle([14, y, W - 14, y + 44], radius=10, fill=CARD, outline=BORDER)
        d.text((26, y + 14), title, font=font(12), fill=TEXT)
        d.text((W - 46, y + 12), "⬇", font=font(16), fill=TEXT)
        y += 54
    y += 16
    d.rounded_rectangle([18, y, W - 18, y + 90], radius=12, outline=BORDER, width=2)
    d.text((60, y + 20), "Импортировать заметку из файла (.txt)", font=font(11), fill=MUTED)
    d.rounded_rectangle([100, y + 45, 100 + 90, y + 45 + 26], radius=6, fill=BG, outline=BORDER)
    d.text((115, y + 51), "Выбрать файл", font=font(9), fill=MUTED)
    img.save("mockup_3_files.png")


screen_list()
screen_editor()
screen_files()
print("Готово: mockup_1_list.png, mockup_2_editor.png, mockup_3_files.png")
