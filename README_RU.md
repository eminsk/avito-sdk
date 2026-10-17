# avito-sdk

[ 🇬🇧 English Documentation ](https://github.com/eminsk/avito-sdk/blob/main/README.md) | [ 🇷🇺 Документация на русском ]


[![Release Version](https://img.shields.io/badge/релиз-v0.3.4-0969da.svg?style=flat&logo=github)](https://github.com/eminsk/avito-sdk/releases/tag/v0.3.4)
[![PyPI Version](https://img.shields.io/pypi/v/avito-sdk.svg?style=flat&logo=pypi&color=blue)](https://pypi.org/project/avito-sdk/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/avito-sdk.svg?style=flat&logo=pypi)](https://pypi.org/project/avito-sdk/)
[![Python Versions](https://img.shields.io/badge/python-3.8_--_3.16+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://pypi.org/project/avito-sdk/)
[![Free-Threaded No-GIL](https://img.shields.io/badge/No--GIL-3.13t%20--%203.16t-brightgreen?style=flat)](https://peps.python.org/pep-0703/)
[![PyPy](https://img.shields.io/badge/PyPy-3.11_%7C_3.12-yellow.svg?style=flat&logo=pypy)](https://pypy.org/)
[![Tests](https://img.shields.io/badge/тесты-78%20passed-2ea44f.svg?style=flat&logo=pytest&logoColor=white)](https://github.com/eminsk/avito-sdk)
[![Telegram Bot](https://img.shields.io/badge/Telegram_Бот-@eminsk__avito__bot-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://t.me/eminsk_avito_bot)
[![Mobile Proxy](https://img.shields.io/badge/Мобильный_Прокси-Auto--Failover-ff6b6b.svg?style=flat)](https://mobileproxy.space/)
[![MCP Server](https://img.shields.io/badge/MCP-Встроенный_Сервер-00a67e.svg?style=flat)](#встроенный-mcp-сервер-model-context-protocol)
[![Excel Export](https://img.shields.io/badge/Экспорт-.xlsx_Гиперссылки-217346?style=flat&logo=microsoftexcel&logoColor=white)](https://github.com/eminsk/avito-sdk)
[![CI](https://github.com/eminsk/avito-sdk/actions/workflows/ci.yml/badge.svg)](https://github.com/eminsk/avito-sdk/actions)
[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/avito-sdk.svg?style=flat&logo=condaforge)](https://anaconda.org/conda-forge/avito-sdk)
[![eminsk PPA](https://img.shields.io/badge/APT%20PPA-python3--avito--sdk-blueviolet.svg?style=flat)](https://eminsk.github.io/ppa/)
[![GitHub Stars](https://img.shields.io/github/stars/eminsk/avito-sdk?style=flat&logo=github)](https://github.com/eminsk/avito-sdk/stargazers)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](https://opensource.org/licenses/MIT)
[![Donate USDT](https://img.shields.io/badge/Donate-USDT_(TRC20)-26A17B?style=flat&logo=tether&logoColor=white)](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P)

> **Высокопроизводительная библиотека и SDK для работы с Avito без GUI.**  
> Разработана ключевым контрибьютором [`Duff89/parser_avito`](https://github.com/Duff89/parser_avito).

> ### 🤝 Сообщество, поддержка и обратная связь
> - 🐛 **Нашли ошибку или изменилась вёрстка Авито?** [Откройте Issue (тикет)](https://github.com/eminsk/avito-sdk/issues) — баги и правки парсера выходят в приоритетном порядке!
> - 💬 **Вопросы, настройка прокси или предложения?** Загляните в [GitHub Discussions (Обсуждения)](https://github.com/eminsk/avito-sdk/discussions).
> - ⭐ **Полезен SDK?** Поставьте звезду репозиторию на GitHub — это помогает проекту развиваться!
> - ☕ **Поддержать разработку (USDT TRC-20):** `TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P` ([Проверить в TronScan](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P))

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

## 🌟 Что нового в версии 0.2.2

- 🔗 **Пакетный сбор по нескольким ссылкам (Multi-Link Scraping):** Отправляйте сразу 2, 3, 4 или более ссылок в одном сообщении Telegram-боту `@eminsk_avito_bot`. Бот последовательно собирает каждую ссылку с заданным лимитом (до 1000+ объявлений) и присылает отдельные файлы Excel.
- 🚀 **Параллельные потоки Fast и Turbo (до 8–16 воркеров):** Ускорение сбора в 2–4 раза благодаря адаптивному микро-сглаживанию задержек между запросами.
- 🌐 **Строгий аудит мобильного прокси (`[ProxyAudit]`):** Автоматическая верификация купленного мобильного 4G/LTE прокси с ротацией IP при каждом запуске.
- 📝 **Постоянное файловое логирование (`storage/logs/avito_bot.log`):** Автоматическая ротация (10 МБ × 5 файлов). Логи полностью исключены из Git (`.gitignore`).
- 🔒 **Конфиденциальность на лету (`PrivacyFilter`):** Учётные данные прокси и токены ботов маскируются в логах.
- 🧹 **Гарантированное закрытие ресурсов (Zero Socket Leaks):** Все HTTP-сессии, сокеты и соединения всегда гарантированно закрываются.

---

## 🌐 Требования к мобильным прокси и регламент поддержки

> [!IMPORTANT]
> **Обязательное условие стабильной работы и официальный регламент поддержки:**
> 1. Для стабильного сбора данных с Авито (особенно от 100 до 1000+ объявлений, сбора характеристик и работы в 4–8 потоков) **критически необходим качественный купленный мобильный 4G/LTE прокси с автоматической ротацией внешнего IP** (например, через [MobileProxy.space](https://mobileproxy.space/?p=32111)).
> 2. **Аудит в логах:** Система при каждом запуске и каждом запросе фиксирует статус прокси с меткой `[ProxyAudit]`.
> 3. ⛔ **Регламент обращений:** **Если сбор данных запускается БЕЗ купленного мобильного 4G-прокси с ротацией IP (через прямой серверный/домашний IP или статические датацентр-прокси), любые проблемы с блокировками Avito WAF, капчей SmartCaptcha, ошибками 429 Too Many Requests и 439 НЕ РАССМАТРИВАЮТСЯ И ТЕХПОДДЕРЖКЕ НЕ ПОДЛЕЖАТ.**
> 4. **Логирование:** Полная история работы сохраняется в `storage/logs/avito_bot.log` (ротация 10 МБ × 5 файлов). Логи не попадают в Git, а логины и пароли маскируются через `PrivacyFilter`.
> 5. **Чистое завершение:** Все сетевые соединения и сессии всегда гарантированно закрываются.

---

## ⚡ Быстрый старт (всего 3 строки кода, без лишнего boilerplate)

### 1. Установка:
```bash
uv add avito-sdk
# или: pip install avito-sdk
```

### 2. Сбор данных (без main-функций и без сложных обёрток):
```python
from avito_sdk import AvitoClient

# Подключение (подставьте свои данные мобильного прокси)
client = AvitoClient(
    proxy="http://login:password@host:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=...",
    modems_count=1,
)

# 1. Поиск по запросу (или прямой ссылке Авито)
for item in client.search("RTX 4090", limit=10, show_progress=True):
    print(f"{item.title} | {item.price:,} ₽ | {item.url}")
    print(f"  Продавец: {item.seller_name} | Просмотров: {item.total_views}")

# 2. Либо выгрузка по ссылке сразу в Excel (.xlsx) с кликабельными ссылками
client.scrape_url(
    url="https://www.avito.ru/moskva/noutbuki?cd=1",
    limit=30,
    enrich_details=True,
    excel_path="noutbuki.xlsx",
)
```

---

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

### 6. 🌐 Мобильные прокси и многопоточность: интеграция с MobileProxy.space

> [!IMPORTANT]
> **Использование мобильных прокси (`proxy` + `proxy_change_url` / `mobileproxy_key`) обязательно при включении многопоточности (`max_workers > 1`), асинхронного режима (`concurrency > 1`) или глубокого сбора характеристик карточек (`enrich_details=True`)!**  
> Антифрод-система Авито мгновенно блокирует (`403 Forbidden` / `429 Too Many Requests`) обычные серверные или датацентр-IP при частых запросах. Реальные 4G/LTE SIM-карты делят IP-адреса с миллионами мобильных абонентов, поэтому Авито не может забанить мобильную подсеть оператора.

> 📱 **Рекомендуемый сервис**: [MobileProxy.space](https://mobileproxy.space/?p=279117) *(доступен [бесплатный тест на 3 часа](https://mobileproxy.space/user.html?free&p=279117))*  
> Быстрые приватные мобильные прокси на реальных SIM-картах (МТС, Мегафон, Билайн, Tele2) с мгновенной сменой IP по URL или API.

#### Вариант А: Быстрое подключение по ключу `mobileproxy_key`
```python
from avito_sdk import AvitoClient

# Достаточно указать прокси и ключ ротации из кабинета MobileProxy.space
client = AvitoClient(
    proxy="http://login:password@proxy-domain.space:port",
    mobileproxy_key="ВАШ_КЛЮЧ_РОТАЦИИ",  # avito-sdk сам соберет changeip.mobileproxy.space
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

#### Вариант Б: Прямое управление ротацией через `MobileProxySpace`
```python
from avito_sdk import MobileProxySpace

mps = MobileProxySpace.from_key("ВАШ_КЛЮЧ_РОТАЦИИ")
res = mps.rotate_ip(wait_reconnect=True)
print("Новый внешний IP:", res.get("new_ip"))
```

#### Вариант В: Через CLI терминал
```bash
avito-sdk search "iPhone 15" --proxy "http://login:pass@host:port" --mobileproxy-key "ВАШ_КЛЮЧ" --enrich --workers 4
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

# Запуск Model Context Protocol (MCP) сервера через stdio:
avito-mcp --proxy "http://user:pass@ip:port" --proxy-change-url "https://..."
```

---

## 🤖 Встроенный MCP (Model Context Protocol) Сервер

В **avito-sdk** встроен сервер открытого стандарта [Model Context Protocol (MCP)](https://modelcontextprotocol.io) (`avito-mcp` или `avito-sdk mcp`), работающий по протоколу JSON-RPC 2.0 через `stdio`.

Это позволяет искусственному интеллекту в **Google Antigravity**, **Claude Code & Claude Desktop**, **Cursor IDE**, **OpenAI Codex** и **Windsurf** напрямую взаимодействовать с Авито: искать товары, извлекать глубокие характеристики («О помещении», авто и т.д.) и отслеживать снижение цен.

### 🛠️ Доступные MCP-инструменты

| Инструмент | Описание | Основные параметры |
| :--- | :--- | :--- |
| `avito_search` | Поиск на Авито с фильтрами, диапазоном цен, ключевыми словами и экспортом в Excel | `query`, `region`, `min_price`, `max_price`, `limit`, `enrich_details`, `excel_path` |
| `avito_get_item` | Полный сбор карточки товара (характеристики, описание, продавец, просмотры) | `item_id` |
| `avito_price_drops` | Получение списка товаров со сниженной ценой или полной истории изменения цены | `item_id` (опционально) |

---

### 🚀 Руководства по подключению к AI IDE и Агентам

#### 1. 🪐 Google Antigravity (IDE & CLI)

**Через консоль Antigravity CLI:**
```bash
agy mcp add avito -- avito-mcp --workers 2
```

**Либо в конфигурационном файле `~/.gemini/config/mcp_config.json`:**
```json
{
  "mcpServers": {
    "avito": {
      "command": "avito-mcp",
      "args": ["--db", "avito_prices.db", "--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ"
      }
    }
  }
}
```

---

#### 2. ⚡ Anthropic Claude Code & Claude Desktop

**Для консольного Claude Code:**
```bash
claude mcp add avito avito-mcp -- --workers 2
```

**Для десктопного Claude Desktop (`claude_desktop_config.json`):**
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "avito": {
      "command": "avito-mcp",
      "args": ["--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ"
      }
    }
  }
}
```

---

#### 3. 🖱️ Cursor IDE

Создайте файл `.cursor/mcp.json` в корне вашего проекта (или откройте **Cursor Settings > Features > MCP > Add New MCP Server**):

```json
{
  "mcpServers": {
    "avito": {
      "command": "avito-mcp",
      "args": ["--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ"
      }
    }
  }
}
```

---

#### 4. 🧠 OpenAI Codex / ChatGPT / Windsurf / Roo Code

Для **Windsurf** (`~/.codeium/windsurf/mcp_config.json`) или плагина **Roo Code / Continue.dev** в VS Code:

```json
{
  "mcpServers": {
    "avito": {
      "command": "avito-mcp",
      "args": ["--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ"
      }
    }
  }
}
```

---

### 💬 Примеры запросов для нейросети (Prompts)

После подключения вы можете общаться с нейросетью на обычном русском языке:
- *«Найди на Авито 5 объявлений по аренде складов в Москве до 300 000 руб и сохрани их в таблицу warehouses.xlsx»*
- *«Открой объявление 4176185210, извлеки все характеристики помещения и покажи контакты продавца»*
- *«Проверь локальную базу данных на предмет снижения цен на видеокарты и покажи самые выгодные скидки»*

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

## ☕ Поддержка, сообщество и донаты

Если проект оказался для вас полезным или у вас появились предложения/проблемы:

* ⭐ **Поставьте звезду репозиторию**: Это помогает развитию проекта и позволяет другим разработчикам быстрее находить SDK!
* 🐛 **Сообщить об ошибке или проблеме**: Если что-то не работает, изменилась вёрстка Авито или возникла ошибка — [откройте Issue (запрос на исправление)](https://github.com/eminsk/avito-sdk/issues)!
* 💬 **Обсуждения (Discussions)**: Есть идеи новых функций, вопросы или хотите поделиться опытом? Присоединяйтесь к [GitHub Discussions](https://github.com/eminsk/avito-sdk/discussions)!
* ☕ **Поддержать разработку (USDT TRC-20)**:  
  `TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P`  
  *(Сеть: TRON / TRC-20 | [Проверить в TronScan](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P))*

[![GitHub Repo stars](https://img.shields.io/github/stars/eminsk/avito-sdk?style=social)](https://github.com/eminsk/avito-sdk)
[![GitHub Issues](https://img.shields.io/github/issues/eminsk/avito-sdk?color=red&style=flat-square)](https://github.com/eminsk/avito-sdk/issues)
[![GitHub Discussions](https://img.shields.io/badge/Discussions-Join_Community-blue?logo=github&style=flat-square)](https://github.com/eminsk/avito-sdk/discussions)
[![Donate USDT](https://img.shields.io/badge/Donate-USDT_(TRC20)-26A17B?style=flat-square&logo=tether&logoColor=white)](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P)

---

## 📄 Лицензия

Распространяется под свободной лицензией **MIT**.  
Автор: **eminsk** ([M_N_Nik@yahoo.com](mailto:M_N_Nik@yahoo.com))
