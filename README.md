<p align="center">
  <img src="https://raw.githubusercontent.com/eminsk/avito-sdk/main/assets/logo.png" width="140" alt="Avito SDK Pro Logo">
</p>
<h1 align="center">Avito SDK Pro (`avito-sdk`)</h1>
<p align="center">
  <b>Высокопроизводительный парсер Avito, автономный Desktop GUI (Windows .exe), интерактивный Telegram-бот, мониторинг цен, CLI и MCP-сервер.</b>
</p>

[![Релиз](https://img.shields.io/badge/релиз-v0.4.6-0969da.svg?style=flat&logo=github)](https://github.com/eminsk/avito-sdk/releases/tag/v0.4.6)
[![Glama MCP Server](https://glama.ai/mcp/servers/eminsk/avito-sdk/badges/score.svg)](https://glama.ai/mcp/servers/eminsk/avito-sdk)
[![Бесплатный тест прокси 3 часа](https://img.shields.io/badge/Прокси_без_VPN-Тест_3_часа_бесплатно-00C853?style=flat&logo=cloudflare&logoColor=white)](https://mobileproxy.rent/user.html?free&p=279117)
[![PyPI](https://img.shields.io/pypi/v/avito-sdk.svg?style=flat&logo=pypi&color=blue)](https://pypi.org/project/avito-sdk/)
[![Скачивания PyPI](https://img.shields.io/pypi/dm/avito-sdk.svg?style=flat&logo=pypi)](https://pypi.org/project/avito-sdk/)
[![Python](https://img.shields.io/badge/python-3.8%20--%203.16+%20%7C%20PyPy%20%7C%20No--GIL-3776AB.svg?style=flat&logo=python&logoColor=white)](https://pypi.org/project/avito-sdk/)
[![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9.svg?style=flat)](https://github.com/astral-sh/uv)
[![Тесты](https://img.shields.io/badge/pytest-84%20passed-2ea44f.svg?style=flat&logo=pytest&logoColor=white)](https://github.com/eminsk/avito-sdk/tree/main/tests)
[![Desktop GUI](https://img.shields.io/badge/Desktop%20GUI-Windows%20.exe%20%7C%20CustomTkinter-blueviolet.svg?style=flat)](https://github.com/eminsk/avito-sdk#desktop-gui)
[![MCP](https://img.shields.io/badge/MCP-3%20инструмента%20JSON--RPC%202.0-00C853.svg?style=flat)](https://github.com/eminsk/avito-sdk#mcp-server-for-ai-agents)
[![Telegram Канал](https://img.shields.io/badge/Telegram_Канал-@avito__sdk__pro-26A5E4?style=flat&logo=telegram&logoColor=white)](https://t.me/avito_sdk_pro)
[![Telegram Бот](https://img.shields.io/badge/Telegram_Бот-@eminsk__avito__bot-2CA5E0?style=flat&logo=telegram&logoColor=white)](https://t.me/eminsk_avito_bot)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat)](https://opensource.org/licenses/MIT)

> **Автономный парсер и Python SDK для Авито (`avito-sdk`):** чистый нативный HTTP-транспорт с подменой TLS-отпечатка Chrome (`curl_cffi`, без тяжёлого Chromium), многопоточный и асинхронный сбор полных характеристик («О помещении», авто и др.), трекинг снижения цен в SQLite, **интерактивный Telegram-бот (`AvitoTelegramBot`)**, консольный интерфейс CLI, нативный **MCP-сервер (`avito-mcp`)**, современное настольное приложение на **CustomTkinter** и готовый автономный **Windows `.exe` (`AvitoSDK_Pro.exe`)**.

> ### 🤝 Сообщество, мобильные прокси и поддержка
> - 🌐 **Ошибка 429 / 403 при парсинге Авито?** Возьмите [бесплатный тест мобильного прокси на 3 часа](https://mobileproxy.rent/user.html?free&p=279117) ([личный кабинет MobileProxy](https://mobileproxy.rent/?p=279117) — работает в РФ без VPN).
> - 📢 **Релизы, настройка прокси и чат:** подписывайтесь на [Telegram-канал @avito_sdk_pro](https://t.me/avito_sdk_pro).
> - 🐛 **Нашли баг или изменилась вёрстка Авито?** [Откройте Issue (тикет)](https://github.com/eminsk/avito-sdk/issues) — исправления парсера выходят в приоритетном порядке!
> - 💬 **Вопросы, прокси или идеи новых функций?** Загляните в [GitHub Discussions (Обсуждения)](https://github.com/eminsk/avito-sdk/discussions).
> - ⭐ **Полезен проект?** Поставьте звезду репозиторию на GitHub — это помогает большему числу разработчиков найти библиотеку!
> - ☕ **Поддержать разработку (USDT TRC-20):** `TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P` ([Проверить в TronScan](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P))

<p align="center">
  <img src="https://raw.githubusercontent.com/eminsk/avito-sdk/main/docs/images/gui_monitor.png" alt="Avito SDK Pro Desktop GUI — Вкладка Мониторинг и фильтры" width="820">
</p>

---

## 🚀 Ключевые возможности

- 🖥️ **Современный настольный интерфейс (`Avito SDK Pro` Desktop GUI)**: Тёмное приложение на `CustomTkinter` с живой лентой карточек, бейджами снижения цен (`📉`), кнопками быстрого перехода на Авито, проверкой прокси в 1 клик и выгрузкой в Excel.
- 📦 **Автономный Windows `.exe` дистрибутив**: Запускается в 1 клик на Windows 10/11 без установки Python, виртуальных окружений и браузера Chromium (весит ~28 МБ со встроенным `curl_cffi` Chrome TLS).
- 🌐 **Гибкая работа с любыми прокси**: Поддержка дешёвых серверных IPv4/SOCKS5 (с автообновлением cookies через `spfa.pro`), экономных Pay-As-You-Go пулов по мегабайтам (AstroProxy, Asocks) и выделенных 4G/LTE-модемов с ротацией IP по ссылке/ключу (`MobileProxy.rent`).
- ⚡ **Синхронный и Асинхронный движок**: `AsyncAvitoClient` для высоконагруженных Telegram-ботов (Aiogram 3, FastAPI, aiohttp) и `AvitoClient` для простых скриптов и многопоточного сбора.
- 📉 **Трекинг изменения цен (`PriceTracker`)**: Фиксация истории цен в SQLite, автоматический расчёт скидок и падений цены (`price_drop`) с мгновенной отправкой алертов в Telegram.
- 👤 **Данные продавца и контакты**: Извлечение имени продавца (`seller_name`), ID/slug профиля или магазина (`seller_id`) и опциональное получение телефона через `ParsePhone` (`spfa.pro`).
- 📋 **Глубокий сбор характеристик и описаний**: Извлечение всех параметров («О помещении», площадь, этаж, характеристики авто и электроники) и полного многострочного текста описания из сценариев Beduin, Mobile API и Schema.org.
- 🛡️ **Защита от блокировок (TLS Fingerprinting)**: Имитация сетевого отпечатка реального Chrome/Safari через `curl_cffi` с прозрачным фолбэком на `httpx` / `requests` и автоповторами при 429/403.
- 📊 **Экспорт во все популярные форматы**: Стилизованный Excel (`.xlsx` с автошириной колонок и кликабельными ссылками), CSV (UTF-8), JSON, JSONL, а также Pandas / Polars `DataFrame`.
- 🤖 **Интерактивный Telegram-бот (`AvitoTelegramBot`) & CLI**: Управление парсингом прямо из Telegram-чата (`/search`, `/proxy`, `/workers`, живой прогресс-бар и автовыгрузка `.xlsx`) и готовые консольные команды `avito-sdk` / `avito-parser`.
- 🔌 **Нативный MCP-сервер (`avito-mcp`)**: Готовая интеграция по стандарту Model Context Protocol JSON-RPC 2.0 для AI-агентов (Antigravity, Claude Desktop, Cursor, Windsurf).
- 🐍 **Универсальная совместимость**: CPython 3.8 – 3.16+, Free-Threaded No-GIL (3.13t – 3.16t) и PyPy (3.8 – 3.12).

---

<a id="desktop-gui"></a>
## 🖥️ Графический интерфейс Avito SDK Pro (Desktop GUI)

Для тех, кто хочет сразу запустить мониторинг и снайпинг выгодных объявлений без написания кода:

### 1. Запуск готового приложения для Windows (без Python):
1. Скачайте архив **[AvitoSDK_Pro_Windows_x64.zip](https://github.com/eminsk/avito-sdk/releases/latest)** из раздела [Releases](https://github.com/eminsk/avito-sdk/releases).
2. Распакуйте и запустите `AvitoSDK_Pro.exe` (внутри уже вшит движок Chrome TLS `curl_cffi`).
3. Популярные категории и фильтры цен уже преднастроены из коробки!

### 2. Или запуск через Python / PyPI:
```bash
# Мгновенный запуск без установки в глобальное окружение:
uvx --from "avito-sdk[gui]" avito-gui

# Или установка через uv / pip:
pip install "avito-sdk[gui]"
avito-gui
```
Или из клонированного репозитория:
```bash
uv run python run_gui.py
# либо дважды кликните по run_gui.bat
```

### Возможности и вкладки интерфейса:
- 🔍 **Мониторинг**: одновременный опрос нескольких ссылок Авито, фильтры цен (Мин/Макс), белые и чёрные списки слов, настраиваемый интервал с рандомизацией (джиттером).
- ⚡ **Живая лента**: карточки новых лотов в реальном времени с отображением местоположения (`item.location`), индикатором падения цены (`📉 -...`) и кнопкой *«Открыть на Avito ↗»*.
- 📊 **Экспорт в Excel**: сохранение всей живой ленты в красиво отформатированный `.xlsx` с кликабельными ссылками.
- 🌐 **Прокси и Сессия**: строка прокси любого формата, кнопка **«🔍 Проверить прокси»** с замером пинга (мс), настройка ротации `MobileProxy.rent`, опциональный ключ `spfa_api_key` для автообновления cookies на дешёвых IPv4.
- ✈️ **Telegram**: отправка карточек и Excel-отчётов вашему боту, поддержка **изолированного прокси для Telegram** (чтобы не конфликтовать с VPN и РКН) и кнопка тестовой отправки.
- 📋 **Журнал событий и ☕ Донат**: лог проверок, смены IP и статусов в реальном времени, а также кнопки канала [@avito_sdk_pro](https://t.me/avito_sdk_pro) и поддержки проекта прямо в интерфейсе.

<p align="center">
  <img src="https://raw.githubusercontent.com/eminsk/avito-sdk/main/docs/images/gui_feed.png" alt="Avito SDK Pro Desktop GUI — Живая лента и трекер снижения цен" width="820">
</p>

---

## 📦 Установка для разработчиков

### PyPI (`uv` / `pip`)

```bash
# Базовая библиотека, CLI (avito-sdk / avito-parser) и MCP-сервер (avito-mcp)
uv add avito-sdk
# или: pip install avito-sdk

# С графическим интерфейсом Desktop GUI
pip install "avito-sdk[gui]"

# Полная установка (GUI, Excel, Chrome TLS, Async, DataFrames)
pip install "avito-sdk[all]"
```

### Debian / Ubuntu (APT PPA)

```bash
curl -sS https://eminsk.github.io/ppa/setup.sh | sudo bash
sudo apt install python3-avito-sdk
```

### Conda / Pixi (`conda-forge`)

```bash
conda install -c conda-forge avito-sdk
```

---

## 🌟 Что нового в версиях 0.4.5 – 0.4.6

- 🇷🇺 **Полная русскоязычная документация и релизы (`v0.4.6`)**: переведены на русский язык основной `README.md`, карточка пакета на PyPI, описания репозитория и примечания к релизам для максимального удобства разработчиков из РФ/СНГ; обновлены прямые ссылки на логотип и скриншоты GUI.
- 📍 **`Item.location` и стабильность карточек (`v0.4.5`)**: добавлен `@property def location` с фолбэком (`location_name` / `address`), исключающий ошибки отображения локации в живой ленте GUI, а также бейджи снижения цены `(📉 -...)`.
- 🛡️ **Встроенный Chrome TLS (`curl_cffi`) в Windows `.exe`**: автономная сборка GUI работает на Python 3.12 со встроенным TLS-отпечатком Chrome и индикатором статуса в шапке окна.
- 🔑 **Поддержка `spfa.pro` (автообновление cookies и номера телефонов)**: обновлён `ParsePhone` (`https://spfa.pro/api/phone/`) и добавлено поле `spfa_api_key` на вкладке «Прокси».
- 🤖 **Публикация в MCP-каталогах**: добавлены манифест `glama.json`, `smithery.yaml` и `Dockerfile` для автоматической индексации `avito-mcp`.

---

## 🌐 Выбор и настройка сетевых прокси

`Avito SDK Pro` поддерживает любые типы прокси под ваш бюджет и нагрузку:

### 1. Серверные статические прокси (IPv4 / SOCKS5 — от 30–50 ₽/мес)
* **Для чего подходит:** спокойный мониторинг 1–3 ссылок с интервалом 25–40 секунд (`max_workers=1`).
* **Как подключить:**
  ```python
  from avito_sdk import AvitoClient

  # Формат: логин:пароль@хост:порт
  client = AvitoClient(proxy="http://user:pass@185.123.45.67:8000")
  ```
* **Совет:** в GUI встроена кнопка «Проверить прокси», которая мгновенно покажет пинг и ответ Авито через ваш IP.

### 2. Мобильные прокси с оплатой за трафик — Pay-As-You-Go (~150–200 ₽ за 1 ГБ)
* **Для чего подходит:** круглосуточный личный мониторинг **без переплат по 2500 ₽/мес за отдельный модем**.
* **Где взять:** [AstroProxy](https://astroproxy.com) или [Asocks](https://asocks.com).
* **Экономика:** поскольку SDK скачивает только компактный JSON/HTML без картинок (~10–15 КБ на запрос), **1 ГБ хватает на 70 000+ проверок** — целый месяц непрерывной работы!
  ```python
  client = AvitoClient(proxy="http://user:pass@asocks-proxy.com:port")
  ```

### 3. Выделенные мобильные 4G/LTE-модемы с ротацией IP (рекомендуется)
* **Для чего подходит:** высоконагруженный коммерческий парсинг, глубокий сбор характеристик карточек (`enrich_details=True`) и многопоточность (`max_workers=4..16`).
* **Где взять:** [MobileProxy (mobileproxy.rent)](https://mobileproxy.rent/?p=279117) ([бесплатный тест 3 часа без VPN](https://mobileproxy.rent/user.html?free&p=279117)).
  ```python
  client = AvitoClient(
      proxy="http://login:password@proxy-domain.space:port",
      mobileproxy_key="ВАШ_КЛЮЧ_РОТАЦИИ",  # сам соберет URL changeip.mobileproxy.space
  )
  ```

---

## ⚡ Быстрый старт (Python SDK)

### 1. Поиск и выгрузка в Excel (минимум кода)

```python
from avito_sdk import AvitoClient

client = AvitoClient(
    proxy="http://login:password@host:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ",
    modems_count=1,
)

# Поиск по запросу
for item in client.search("RTX 4090", limit=10, show_progress=True):
    print(f"{item.title} | {item.price:,} ₽ | {item.url}")
    print(f"  Продавец: {item.seller_name} | Просмотров: {item.total_views}")

# Либо сбор прямо по URL каталога с сохранением в красивый Excel (.xlsx)
client.scrape_url(
    url="https://www.avito.ru/moskva/noutbuki?cd=1",
    limit=30,
    enrich_details=True,
    excel_path="noutbuki.xlsx",
)
```

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

### 3. Получение полных параметров и характеристик карточек

```python
from avito_sdk import AvitoClient

client = AvitoClient()
item = client.get_item(1234567890)

print("Название:", item.title)
print("Цена:", item.price)
print("Локация:", item.location)
print("Продавец:", item.seller_name)
print("Просмотры:", f"{item.total_views} всего, {item.today_views} сегодня")

print("\nХарактеристики:")
for param_name, param_val in item.params.items():
    print(f"  • {param_name}: {param_val}")

print("\nПолное описание:")
print(item.description)
```

### 4. Отслеживание снижения цен (SQLite `PriceTracker`)

```python
from avito_sdk import AvitoClient

client = AvitoClient(tracker_db="prices.db")

items = list(client.search("iPhone 15 Pro", region="Москва", limit=50))

drops = client.tracker.get_price_drops()
for drop in drops:
    diff = drop["initial_price"] - drop["current_price"]
    print(f"📉 Скидка! {drop['title']}: {drop['initial_price']:,} -> {drop['current_price']:,} ₽ (-{diff:,} ₽)")
```

### 5. Экспорт в Excel / JSON / Pandas DataFrame

```python
from avito_sdk import AvitoClient, to_dataframe, to_excel, to_json

client = AvitoClient()
items = list(client.search("PlayStation 5", limit=30, enrich_details=True))

to_excel(items, "ps5_listings.xlsx")   # Excel с автошириной колонок и ссылками
to_json(items, "ps5_listings.json")    # JSON для аналитики и ML
df = to_dataframe(items)               # Pandas DataFrame
print(df[["id", "title", "price", "seller_name"]].head())
```

### 6. Многопоточность через мобильные прокси (`MobileProxySpace`)

> [!IMPORTANT]
> При включении многопоточности (`max_workers > 1`) или глубоком парсинге карточек (`enrich_details=True`) используйте мобильные прокси (`proxy` + `proxy_change_url` / `mobileproxy_key`), чтобы избежать лимитов 429/403.

```python
from avito_sdk import AvitoClient, MobileProxySpace

client = AvitoClient(
    proxy="http://login:password@proxy-domain.space:port",
    mobileproxy_key="ВАШ_КЛЮЧ_РОТАЦИИ",
)

items = list(
    client.search(
        query="коммерческая недвижимость",
        region="moskva",
        enrich_details=True,  # Забирает блок «О помещении», параметры, просмотры и описание
        max_workers=8,
        limit=100,
    )
)

# Или прямая смена IP вручную:
mps = MobileProxySpace.from_key("ВАШ_КЛЮЧ_РОТАЦИИ")
res = mps.rotate_ip(wait_reconnect=True)
print("Новый внешний IP:", res.get("new_ip"))
```

### 7. Живой прогресс-бар и выгрузка Excel в Telegram

```python
from avito_sdk import AvitoClient

client = AvitoClient(
    proxy="http://user:pass@ip:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ",
    tg_token="123456:ABC-DEF_ТОКЕН_БОТА",
    tg_chat_id="-1001234567890",
)

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

Пример живого прогресс-бара в Telegram во время парсинга:
```text
⏳ Парсинг Авито: аренда склада
🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50% (25/50)
🌐 Мобильный прокси: Активен (ротаций IP: 2)
🧵 Потоков: 4  |  📉 Снижений цен: 3
```

### 8. Интерактивный Telegram-бот (`AvitoTelegramBot`)

Управляйте парсингом напрямую из чата (`/search`, `/proxy`, `/workers`), отслеживайте прогресс и получайте готовый `.xlsx` файл:

```python
from avito_sdk import AvitoTelegramBot

bot = AvitoTelegramBot(
    bot_token="123456:ABC-DEF_ТОКЕН_БОТА",
    proxy="http://user:pass@ip:port",
    proxy_change_url="https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ",
    workers=4,
)
bot.run_polling()
```

---

## 💻 Консольная утилита (CLI)

После установки доступны команды `avito-sdk`, `avito-parser`, `avito` и `avito-mcp`:

```bash
# Быстрый поиск с сохранением в Excel:
avito-sdk search "MacBook M2" --region moskva --max-price 90000 --output macbooks.xlsx

# Многопоточный сбор характеристик («О помещении») через мобильный прокси + выгрузка .xlsx в Telegram:
avito-sdk search "помещение" --region moskva --enrich --workers 5 \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --tg-token "123456:ABC..." --tg-chat-id "-1001234567890" \
  --output premises.xlsx

# Запуск интерактивного Telegram-бота:
avito-sdk bot --tg-token "123456:ABC..." \
  --proxy "http://user:pass@ip:port" \
  --proxy-change-url "https://changeip.mobileproxy.space/?proxy_key=..." \
  --workers 4

# Запуск сценария из готового config.toml:
avito-sdk config config.toml

# Просмотр детальной карточки объявления и списка снижений цен:
avito-sdk item 3854129841
avito-sdk drops --db prices.db

# Запуск MCP-сервера через stdio:
avito-mcp --proxy "http://user:pass@ip:port" --proxy-change-url "https://..."
```

---

<a id="mcp-server-for-ai-agents"></a>
## 🤖 Нативный MCP-сервер (Model Context Protocol)

[![eminsk/avito-sdk MCP server](https://glama.ai/mcp/servers/eminsk/avito-sdk/badges/score.svg)](https://glama.ai/mcp/servers/eminsk/avito-sdk)

В **`avito-sdk`** встроен высокопроизводительный [Model Context Protocol (MCP)](https://modelcontextprotocol.io) сервер (`avito-mcp` / `avito-sdk mcp`) на базе JSON-RPC 2.0 `stdio` (опубликован в каталоге [Glama MCP](https://glama.ai/mcp/servers/eminsk/avito-sdk)).

Это позволяет нейросетям в **Google Antigravity**, **Claude Code / Claude Desktop**, **Cursor IDE**, **OpenAI Codex** и **Windsurf** искать товары на Авито, извлекать полные характеристики и проверять снижения цен.

### 🛠️ Доступные MCP-инструменты

| Инструмент | Описание | Основные параметры |
| :--- | :--- | :--- |
| `avito_search` | Поиск на Авито с фильтрами цен, ключевыми словами и экспортом в Excel | `query`, `region`, `min_price`, `max_price`, `limit`, `enrich_details`, `excel_path` |
| `avito_get_item` | Полный сбор карточки товара (характеристики, описание, продавец, просмотры) | `item_id` |
| `avito_price_drops` | Список товаров со сниженной ценой или история изменения цены | `item_id` (опционально) |

### Конфигурация для AI IDE (`mcp_config.json` / `.cursor/mcp.json`)

```json
{
  "mcpServers": {
    "avito": {
      "command": "uvx",
      "args": ["--from", "avito-sdk", "avito-mcp", "--workers", "2"],
      "env": {
        "AVITO_PROXY": "http://user:pass@ip:port",
        "AVITO_PROXY_CHANGE_URL": "https://changeip.mobileproxy.space/?proxy_key=ВАШ_КЛЮЧ"
      }
    }
  }
}
```

Для **Antigravity CLI**: `agy mcp add avito -- avito-mcp --workers 2`  
Для **Claude Code**: `claude mcp add avito avito-mcp -- --workers 2`

### 💬 Примеры запросов к нейросети
- *«Найди на Авито 5 объявлений по аренде складов в Москве до 300 000 руб и сохрани в `warehouses.xlsx`»*
- *«Открой объявление 4176185210, извлеки все характеристики помещения и покажи данные продавца»*
- *«Проверь локальную базу данных на снижение цен на видеокарты и покажи лучшие скидки»*

---

## 🛠️ Сравнение: Обычные парсеры (Flet/Playwright) vs `avito-sdk`

| Параметр | Обычные десктопные парсеры | **Avito SDK Pro (`avito-sdk`)** |
| :--- | :---: | :---: |
| Графический интерфейс | ⚠️ Тяжёлый Flet / Chromium (требует много RAM) | ✅ Лёгкий **CustomTkinter** GUI + автономный `.exe` (~28 МБ) |
| Сетевой движок | ⚠️ Требует браузер или внешний сайт `spfa.pro` | ✅ Чистый HTTP + **Chrome TLS (`curl_cffi`)**, 100% автономность |
| Запуск на сервере / VPS (1 ГБ RAM) | ⚠️ Часто падает с OOM-ошибкой или требует Xvfb | ✅ Потребляет ~30–40 МБ RAM из коробки |
| Асинхронный API (`asyncio`) | ❌ Нет | ✅ `AsyncAvitoClient` |
| Интеграция в Telegram-ботов | Сложно | ✅ Встроенный **`AvitoTelegramBot`** и раздельный `tg_proxy` |
| Отслеживание истории цен | ⚠️ Ограничено | ✅ Встроенный SQLite `PriceTracker` |
| Характеристики («О помещении» и др.) | ⚠️ Частично | ✅ Глубокий парсер Beduin & Mobile API |
| Поддержка версий Python | 3.11 – 3.13 | ✅ CPython 3.8–3.16, **Free-Threaded No-GIL**, **PyPy** |

---

## 🧪 Автотесты (`pytest`)

```bash
uv run --with pytest pytest -v
```

**84 автотеста** успешно проходят на всех актуальных версиях Python (CPython 3.8–3.16, No-GIL 3.13t–3.16t, PyPy 3.8–3.12).

---

## 🌐 Другие проекты автора для маркетплейсов и системного Python

* 🟣 [**WB SDK Pro (`wb-sdk-pro`)**](https://github.com/eminsk/wildberries_parser) — Универсальный парсер и SDK для Wildberries (CDN, Кошелёк, Rank, Умные отзывы + AI `g4f`, Telegram-бот, 7-вкладочный GUI `.exe` и MCP).
* 🔵 [**Ozon SDK Pro (`ozon-sdk-pro`)**](https://github.com/eminsk/ozon_parser) — Парсер и SDK для Ozon (Composer API v2, ИНН продавцов, Ozon Карта, Rank, Умные отзывы + AI, Telegram-бот, 7-вкладочный GUI `.exe` и MCP).
* ⚡ [**NanoVector**](https://github.com/eminsk/nanovector) • [**AgentJIT**](https://github.com/eminsk/agentjit) • [**NanoGEMM**](https://github.com/eminsk/nanogemm) • [**PureAPK**](https://github.com/eminsk/pyapk) — высокопроизводительные системные и AI-библиотеки (портфолио на [eminsk.github.io](https://eminsk.github.io/)).

---

## ☕ Поддержка, сообщество и донаты

Если проект помогает вам в работе или экономит время:

* ⭐ **Поставьте звезду репозиторию** на [GitHub](https://github.com/eminsk/avito-sdk) — это помогает проекту расти!
* 🐛 **Нашли ошибку?** [Откройте Issue](https://github.com/eminsk/avito-sdk/issues) с деталями воспроизведения.
* 📢 **Telegram-канал и чат:** [@avito_sdk_pro](https://t.me/avito_sdk_pro) — релизы `.exe`, инструкции по прокси и помощь.
* ☕ **Поддержать разработку (USDT TRC-20):**  
  `TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P`  
  *(Сеть: TRON / TRC-20 | [Проверить в TronScan](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P))*

[![GitHub Repo stars](https://img.shields.io/github/stars/eminsk/avito-sdk?style=social)](https://github.com/eminsk/avito-sdk)
[![Telegram Канал](https://img.shields.io/badge/Telegram-@avito__sdk__pro-26A5E4?logo=telegram&style=flat-square)](https://t.me/avito_sdk_pro)
[![GitHub Issues](https://img.shields.io/github/issues/eminsk/avito-sdk?color=red&style=flat-square)](https://github.com/eminsk/avito-sdk/issues)
[![GitHub Discussions](https://img.shields.io/badge/Discussions-Сообщество-blue?logo=github&style=flat-square)](https://github.com/eminsk/avito-sdk/discussions)
[![Donate USDT](https://img.shields.io/badge/Donate-USDT_(TRC20)-26A17B?style=flat-square&logo=tether&logoColor=white)](https://tronscan.org/#/address/TDVbEdnpgNgoAhNcn1EwXxWHiR3RKLit5P)

---

## 📄 Лицензия

Распространяется под свободной лицензией **MIT**.  
Автор: **eminsk** ([M_N_Nik@yahoo.com](mailto:M_N_Nik@yahoo.com))
