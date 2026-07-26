
# Word Capture Bot

Open-source Python-бот для автоматического прохождения typing-мини-игры **«Атака Автоматонов»**.

Скрипт захватывает выбранную область экрана, распознаёт слова через OCR (Tesseract) и автоматически вводит их с клавиатуры.
<img width="971" height="970" alt="Screenshot_1" src="https://github.com/user-attachments/assets/7e54649d-e415-4108-a38e-cd2aa4c2dd7b" />

---

# 🚀 Быстрая установка

## 1. Скачать проект

Скачайте или клонируйте папку **WordCaptureBot** в любое место на компьютере.

## 2. Установить Tesseract OCR

Скачайте и установите Tesseract OCR:

https://github.com/UB-Mannheim/tesseract/releases/tag/v5.4.0.20240606

Во время установки оставьте путь по умолчанию:

## 3. Установить программу

Запустите двойным щелчком **install.bat** Затем запустите **run.bat**

Скрипт автоматически:

- создаст виртуальное окружение (`.venv`);
- установит все необходимые зависимости;
- создаст ярлык **Word Capture Bot** на рабочем столе;
- проверит наличие Tesseract OCR.

После установки просто запускайте программу через ярлык **Word Capture Bot** или файл **run.bat**.

---

# 🎮 Использование

1. Нажмите **«Выбрать область»** (`Ctrl + Shift + R`).
2. Выделите область экрана, где появляются слова.
3. Нажмите **«Старт»** (`F8`).
4. После окончания мини-игры нажмите **«Стоп»** (`F9`).
<img width="519" height="593" alt="Screenshot_2" src="https://github.com/user-attachments/assets/2cbb430f-e2d2-46c8-a1f3-69494fb19063" />

---

# ✨ Возможности

- Выбор любой области экрана.
- OCR через Tesseract.
- Автоматический ввод слов и фраз.
- Горячие клавиши управления.
- Самообучающийся словарь.
- Встроенная база героев и предметов.
- Адаптивная скорость OCR.
- Открытый исходный код (Open Source).

---

# 📂 Структура проекта

| Файл | Назначение |
|------|------------|
| `capture_bot.py` | Основной скрипт |
| `requirements.txt` | Python-зависимости |
| `install.bat` | Установка |
| `run.bat` | Запуск |
| `uninstall.bat` | Удаление |
| `learned_words.json` | Самообучающийся словарь |

---

# 🗑 Удаление

Запустите **uninstall.bat**.

Скрипт:

- удалит ярлык с рабочего стола;
- удалит виртуальное окружение `.venv`;
- предложит удалить или сохранить `learned_words.json`.

После этого можно просто удалить папку проекта.

---

# ⚙️ Требования

- Windows 10/11
- Python 3.10+
- Tesseract OCR

---

# 📖 О проекте

Word Capture Bot — полностью открытый проект на Python для автоматизации набора слов в мини-игре **«Атака Автоматонов»**.

Бот:

- захватывает выбранную область экрана;
- распознаёт слова с помощью OCR (Tesseract);
- отслеживает уже введённые буквы по их цвету;
- автоматически вводит оставшуюся часть слова;
- запоминает новые слова и использует их в дальнейшем.

Исходный код полностью открыт — вы можете свободно изучать, изменять и распространять проект.

---

# 🔍 GitHub Topics / Keywords

Dota 2, Dota2, Атака Автоматонов, Attack Automatons, typing game, OCR, Tesseract OCR, Python, automation, auto typer, auto typing, keyboard automation, screen capture, computer vision, OpenCV, image recognition, game bot, typing bot, word bot, desktop automation, Windows, open source, hero names, item names, mini game, OCR bot, OCR automation, text recognition, keyboard input, gaming tools, Python OCR, Tesseract Python, desktop bot, capture bot, auto keyboard, typing automation.
