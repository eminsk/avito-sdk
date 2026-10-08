# avito-sdk

[ 🇬🇧 English Documentation ](https://github.com/eminsk/avito-sdk/blob/main/README.md) | [ 🇷🇺 Документация на русском ]


[![PyPI Version](https://img.shields.io/pypi/v/avito-sdk.svg?color=blue)](https://pypi.org/project/avito-sdk/)
[![Python Versions](https://img.shields.io/pypi/pyversions/avito-sdk.svg)](https://pypi.org/project/avito-sdk/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/avito-sdk.svg?style=flat)](https://anaconda.org/conda-forge/avito-sdk)
[![eminsk PPA](https://img.shields.io/badge/APT%20PPA-python3--avito--sdk-blueviolet.svg)](https://eminsk.github.io/ppa/)
[![Free-Threaded No-GIL](https://img.shields.io/badge/No--GIL-3.13t%20--%203.16t-brightgreen)](https://peps.python.org/pep-0703/)
[![MCP Server](https://img.shields.io/badge/MCP-Native_Stdio_Server-00a67e.svg)](#встроенный-mcp-сервер-model-context-protocol)
[![CI](https://github.com/eminsk/avito-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/eminsk/avito-sdk/actions)

> **Высокопроизводительная библиотека и SDK для работы с Avito без GUI.**  
> Разработана ключевым контрибьютором [`Duff89/parser_avito`](https://github.com/Duff89/parser_avito).

---

## 🚀 Возможности

- 🚀 **100% Headless и легкий вес**: Никаких оконных библиотек (Tkinter, CustomTkinter, Flet, PyInstaller). Работает прямо в Linux, Docker, AWS, Raspberry Pi, macOS и Windows.
- ⚡ **Asyncio и Синхронный режим**: `AsyncAvitoClient` для высоконагруженных Telegram-ботов (Aiogram 3, Telethon), FastAPI, и `AvitoClient` для простых скриптов.
- 📉 **Отслеживание изменения цен (PR #334 / Issue #214)**: Автоматическая фиксация старой цены, вычисление снижения цены (`price_drop`) и ведение истории в SQLite.
- 👤 **Извлечение данных продавца (PR #334 / Issue #333)**: Сбор имени продавца (`seller_name`) и slug/ID профиля/магазина (`seller_id`).
- 📋 **Глубокий сбор характеристик (PR #337 / Issue #335)**: Извлечение всех параметров («О помещении», площадь, этаж, тех. характеристики авто и электроники) из Beduin-сценариев и Mobile API.
- 📝 **Полный текст описания (PR #329 / Issue #305)**: Извлечение многострочного описания из микроразметки Schema.org и сценариев Avito.
- 🛡️ **Обход TLS-fingerprinting**: Имитация сетевого отпечатка Chrome/Safari через `curl_cffi` с автоматическим фолбэком на стандартный HTTP-транспорт.
- 📊 **Экспорт данных**: В Excel (`.xlsx` со стилями), CSV, JSON, JSONL, а также в Pandas и Polars DataFrame.
- 💻 **Консольная утилита (CLI)**: Быстрый поиск прямо из терминала через `avito-sdk search` или `avito-parser`.
- 🌐 **Мультиплатформенность**: Поддержка Python 3.8 – 3.16+, Free-Threaded No-GIL (3.13t–3.15t) и PyPy.

---

## 📦 Установка

```bash
# Базовая установка через PyPI
pip install avito-sdk

# С поддержкой обхода анти-бот защиты (рекомендуется)
pip install "avito-sdk[tls]"

# Полная установка (Excel, TLS, Async, DataFrames)
pip install "avito-sdk[all]"
```

### Через Debian / Ubuntu APT (eminsk PPA)
```bash
curl -sS https://eminsk.github.io/ppa/setup.sh | sudo bash
sudo apt install python3-avito-sdk
```

Или через Conda / Mamba:
```bash
conda install -c conda-forge avito-sdk
```

---

## ⚡ Быстрый старт

### 1. Синхронный поиск объявлений

```python
from avito_sdk import AvitoClient

client = AvitoClient()

# Поиск ноутбуков в Москве до 80 000 ₽
for item in client.search("ноутбук thinkpad", region="Москва", max_price=80000, limit=10):
    print(f"[{item.id}] {item.title} — {item.price:,} ₽ | Продавец: {item.seller_name}")
    if item.has_price_changed:
        print(f"  🔥 Цена изменилась! Старая: {item.old_price:,} ₽ (Снижение: {item.price_drop:,} ₽)")
```

---

### 2. Асинхронный стриминг (для Telegram-ботов и FastAPI)

```python
import asyncio
from avito_sdk import AsyncAvitoClient

async def main():
    async with AsyncAvitoClient() as client:
        async for item in client.search("rtx 4070", region="Санкт-Петербург", limit=20):
            print(f"Найдено: {item.title} ({item.price:,} ₽) -> {item.url}")

asyncio.run(main())
```

---

### 3. Получение полных параметров и характеристик (PR #337)

```python
from avito_sdk import AvitoClient

client = AvitoClient()

# Получаем карточку объявления со всеми характеристиками
item = client.get_item(1234567890)

print("Название:", item.title)
print("Цена:", item.price)
print("Продавец:", item.seller_name)
print("Просмотры:", f"{item.total_views} всего, {item.today_views} сегодня")

print("\nХарактеристики (PR #337):")
for param_name, param_val in item.params.items():
    print(f"  • {param_name}: {param_val}")

print("\nОписание (PR #329):")
print(item.description)
```

---

### 4. Отслеживание падения цен (PR #334)

```python
from avito_sdk import AvitoClient, PriceTracker

client = AvitoClient(tracker_db="prices.db")

# Запускаем сбор и авто-трекинг
items = list(client.search("iPhone 15 Pro", region="Москва", limit=50))

# Получаем список объявлений, у которых цена упала:
tracker = client.tracker
drops = tracker.get_price_drops()
for drop in drops:
    diff = drop["initial_price"] - drop["current_price"]
    print(f"📉 Скидка! {drop['title']}: {drop['initial_price']:,} -> {drop['current_price']:,} ₽ (-{diff:,} ₽)")
```

---

### 5. Экспорт в Excel / JSON / Pandas

```python
from avito_sdk import AvitoClient, to_excel, to_json, to_dataframe

client = AvitoClient()
items = list(client.search("PlayStation 5", limit=30, enrich_details=True))

# 1. Красивый Excel с автошириной колонок и форматированием
to_excel(items, "ps5_listings.xlsx")

# 2. JSON Lines для ML и потоковой обработки
to_json(items, "ps5_listings.json")

# 3. Pandas DataFrame
df = to_dataframe(items)
print(df[["id", "title", "price", "seller_name"]].head())
```

---

### 6. 🌐 Мобильные прокси и многопоточность (Обязательно при потоковом сборе)

> [!IMPORTANT]
> **Использование мобильных прокси (`proxy` + `proxy_change_url`) обязательно при включении многопоточности (`max_workers > 1`), асинхронного режима (`concurrency > 1`) или глубокого сбора характеристик карточек (`enrich_details=True`)!**  
> Антифрод-система Авито мгновенно банит (`403 Forbidden` / `429 Too Many Requests`) обычные серверные или домашние IP при частых параллельных запросах к карточкам. При передаче мобильного прокси и ссылки для смены IP (`proxy_change_url`) библиотека `avito-sdk` автоматически меняет IP-адрес оператора при любом ограничении и продолжает сбор без потери объявлений.

```python
from avito_sdk import AvitoClient

# Инициализация клиента с мобильным прокси и ссылкой автосмены IP
client = AvitoClient(
    proxy="http://username:password@proxy.example.com:8000",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ",
)

# Многопоточный сбор характеристик карточек (8 потоков параллельно)
items = list(
    client.search(
        query="коммерческая недвижимость",
        region="moskva",
        enrich_details=True,  # Забирает блок «О помещении», все параметры, просмотры и описание
        max_workers=8,        # Многопоточность (обязателен мобильный прокси!)
        limit=100,
    )
)
```

---

### 7. 🎭 Сбор Cookies через Playwright + Живой Прогресс-бар и Выгрузка Excel в Telegram

Установите библиотеку с поддержкой Playwright и Excel (`pip install "avito-sdk[all]"`):

```python
from avito_sdk import AvitoClient

client = AvitoClient(
    proxy="http://user:pass@ip:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ",
    use_playwright_cookies=True,  # Автосбор куки 'ft' через headless Chromium + stealth JS
    tg_token="123456:ABC-DEF_ТОКЕН_БОТА",
    tg_chat_id="-1001234567890",  # ID Telegram-канала или чата
)

# Парсит через мобильный прокси, обновляет живой прогресс-бар в Telegram,
# отправляет карточки со старой/новой ценой (📉 50 000 ₽ ➔ 45 000 ₽),
# сохраняет красивый .xlsx и автоматически загружает Excel-файл прямо в Telegram!
items = list(
    client.search(
        query="аренда склада",
        region="moskva",
        enrich_details=True,
        max_workers=4,
        limit=50,
        notify_telegram=True,
        telegram_progress=True,
        show_progress=True,
        excel_path="warehouses.xlsx",
    )
)
```

Пример живого прогресс-бара в Telegram во время работы:
```text
⏳ Парсинг Авито: аренда склада
🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50% (25/50)
🌐 Мобильный прокси: Активен (ротаций IP: 2)
🧵 Потоков: 4  |  📉 Снижений цен: 3
```

---

### 8. 🤖 Интерактивное управление через Telegram-бота (`AvitoTelegramBot`)

Полное управление парсером прямо из Telegram (как в `parser_avito`): отправляйте боту поисковый запрос или ссылку Авито, меняйте мобильный прокси (`/proxy`), число потоков (`/workers`), режим Playwright (`/playwright`), наблюдайте за живым прогресс-баром (`🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50%`) и получайте готовый `.xlsx` файл отчёта прямо в чат:

```python
from avito_sdk import AvitoTelegramBot

bot = AvitoTelegramBot(
    bot_token="123456:ABC-DEF_ТОКЕН_БОТА",
    proxy="http://user:pass@ip:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ",
    workers=4,
    use_playwright_cookies=True,
)
bot.run_polling()
```

---

## 🖥️ Использование из консоли (CLI)

Библиотека включает встроенную консольную команду `avito-sdk` (или `avito-parser`):

```bash
# Поиск с выводом на экран и сохранением в Excel:
avito-sdk search "MacBook M2" --region moskva --max-price 90000 --output macbooks.xlsx

# Многопоточный сбор характеристик («О помещении») через мобильный прокси + Playwright + выгрузка .xlsx в Telegram:
avito-sdk search "помещение" --region moskva --enrich --workers 5 \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --playwright \
  --tg-token "123456:ABC..." --tg-chat-id "-1001234567890" \
  --output premises.xlsx

# Запуск интерактивного Telegram-бота для управления парсингом и получения Excel-отчётов:
avito-sdk bot --tg-token "123456:ABC..." \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --playwright --workers 4

# Просмотр детальной карточки объявления:
avito-sdk item 3854129841

# Просмотр всех зафиксированных снижений цен:
avito-sdk drops --db prices.db
```

---

## 🛠️ Сравнение: `parser_avito` (GUI) vs `avito-sdk` (Библиотека)

| Функция | Duff89/parser_avito | **avito-sdk** |
| :--- | :---: | :---: |
| Назначение | Десктопное приложение для пользователей | Автономная Python-библиотека & SDK |
| Графический интерфейс | ✅ Есть (CustomTkinter / GUI) | ❌ Отсутствует (100% Headless) |
| Запуск на сервере / Docker / VPS | Требует виртуальный дисплей (xvfb) | ✅ Из коробки без зависимостей |
| Асинхронный API (`asyncio`) | ❌ Нет | ✅ `AsyncAvitoClient` |
| Использование в Telegram-ботах | Сложно | ✅ `pip install avito-sdk` |
| Отслеживание цен (PR #334) | ✅ Есть | ✅ Встроенный `PriceTracker` |
| Характеристики товара (PR #337) | ✅ Есть | ✅ Глубокий парсер Beduin & Mobile |
| Поддержка Python 3.8 – 3.16+ | 3.11 – 3.13 | ✅ 3.8 – 3.16, No-GIL, PyPy |

---

## 📄 Лицензия

Распространяется под свободной лицензией **MIT**.  
Автор: **eminsk** ([M_N_N@tut.by](mailto:M_N_N@tut.by))
