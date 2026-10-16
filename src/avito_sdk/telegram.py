"""
Built-in Telegram channel/chat notification engine (TelegramNotifier) and
interactive Telegram Bot Controller (AvitoTelegramBot) with:
- Live visual progress bars in Telegram ([████████░░░░░░░░] 50%)
- Direct Excel (.xlsx) report upload to Telegram chat/channel (sendDocument)
- Mobile proxy configuration and automatic IP rotation tracking
- MarkdownV2 formatting compatible with Duff89/parser_avito
"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Union

import requests

from avito_sdk.export import to_excel
from avito_sdk.http import normalize_proxy
from avito_sdk.models import Item

logger = logging.getLogger("avito_sdk")

_MD_V2_SPECIAL = r"_*[]()~`>#+-=|{}.!"


def escape_markdown_v2(text: str) -> str:
    """Escape special characters for Telegram MarkdownV2."""
    if not text:
        return ""
    res = str(text).replace("\\", "\\\\")
    for ch in _MD_V2_SPECIAL:
        res = res.replace(ch, f"\\{ch}")
    return res


def render_progress_bar(current: int, total: int, width: int = 16) -> str:
    """Render a visual progress bar string for terminal: [████████░░░░░░░░] 50% (25/50)."""
    if total <= 0:
        return f"[{'█' * width}] {current} шт."
    ratio = min(max(current / total, 0.0), 1.0)
    filled = int(round(width * ratio))
    bar = "█" * filled + "░" * (width - filled)
    pct = int(round(ratio * 100))
    return f"[{bar}] {pct}% ({current}/{total})"


def render_telegram_progress_bar(current: int, total: int, width: int = 10) -> str:
    """Render a uniform emoji progress bar for Telegram proportional fonts: 🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜ 50% (25/50)."""
    if total <= 0:
        return f"{'🟩' * width} {current} шт."
    ratio = min(max(current / total, 0.0), 1.0)
    filled = int(round(width * ratio))
    bar = "🟩" * filled + "⬜" * (width - filled)
    pct = int(round(ratio * 100))
    return f"{bar} {pct}% ({current}/{total})"


class TelegramNotifier:
    """
    Sends formatted Avito listing notifications, live progress bars,
    and Excel (.xlsx) files to a Telegram channel or chat.
    """

    def __init__(
        self,
        bot_token: str,
        chat_id: Union[str, int, Sequence[Union[str, int]]],
        proxy: Optional[str] = None,
        only_text: bool = False,
        include_params: bool = True,
        max_retries: int = 3,
    ):
        self.bot_token = bot_token
        if isinstance(chat_id, (str, int)):
            self.chat_ids: List[str] = [str(chat_id)]
        else:
            self.chat_ids = [str(cid) for cid in chat_id]
        norm_proxy = normalize_proxy(proxy)
        self.proxies = {"http": norm_proxy, "https": norm_proxy} if norm_proxy else None
        self.only_text = only_text
        self.include_params = include_params
        self.max_retries = max_retries

    def format_item(self, item: Item) -> str:
        """Format an Item into a Telegram MarkdownV2 message (parser_avito style)."""
        price_val = item.price or 0
        price_str = f"{price_val:,}".replace(",", " ") + " ₽"
        title = escape_markdown_v2(item.title or f"Объявление #{item.id}")
        seller_display = item.seller_name or item.seller_id or ""
        seller = escape_markdown_v2(str(seller_display)) if seller_display else ""
        short_url = item.url or f"https://avito.ru/{item.id}"

        parts: List[str] = []

        if item.old_price is not None and item.old_price != price_val:
            old_formatted = f"{item.old_price:,}".replace(",", " ") + " ₽"
            arrow = "📉" if price_val < item.old_price else "📈"
            price_change_text = escape_markdown_v2(f"{arrow} {old_formatted} ➔ {price_str}")
            part = f"*{price_change_text}*"
            if getattr(item, "is_promotion", False):
                part += " 🢁"
            parts.append(part)
        else:
            part = f"*{escape_markdown_v2(price_str)}*"
            if getattr(item, "is_promotion", False):
                part += " 🢁"
            parts.append(part)

        parts.append(f"[{title}]({short_url})")

        if seller:
            parts.append(f"Продавец: {seller}")

        if self.include_params and item.params:
            params_preview = "; ".join(f"{k}: {v}" for k, v in list(item.params.items())[:6])
            parts.append(f"📋 {escape_markdown_v2(params_preview)}")

        parts.append(f"🔗 {escape_markdown_v2(short_url)}")

        return "\n".join(parts)

    def _request_with_retries(self, fn):
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = fn()
                if resp.status_code == 429:
                    retry_after = 2.0 * attempt
                    try:
                        retry_after = float(resp.json().get("parameters", {}).get("retry_after", retry_after))
                    except Exception:
                        pass
                    time.sleep(retry_after)
                    continue
                resp.raise_for_status()
                return resp
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 400:
                    raise
                last_err = e
                time.sleep(1.0 * attempt)
            except Exception as e:
                last_err = e
                time.sleep(1.0 * attempt)
        if last_err:
            raise last_err

    def send_message(
        self,
        text: str,
        parse_mode: Optional[str] = "MarkdownV2",
        reply_markup: Optional[dict] = None,
    ) -> Dict[str, int]:
        """Send a text message to all configured Telegram chat_ids and return {chat_id: message_id}."""
        msg_ids: Dict[str, int] = {}
        for cid in self.chat_ids:
            mid = self._send_text_to_chat(cid, text, parse_mode=parse_mode, reply_markup=reply_markup)
            if mid is not None:
                msg_ids[cid] = mid
        return msg_ids

    def _send_text_to_chat(
        self,
        chat_id: str,
        message: str,
        parse_mode: Optional[str] = "MarkdownV2",
        reply_markup: Optional[dict] = None,
    ) -> Optional[int]:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        def _send():
            return requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendMessage",
                json=payload,
                proxies=self.proxies,
                timeout=12,
            )

        resp = self._request_with_retries(_send)
        try:
            return resp.json().get("result", {}).get("message_id")
        except Exception:
            return None

    def edit_message(
        self,
        chat_id: str,
        message_id: int,
        text: str,
        parse_mode: Optional[str] = None,
        reply_markup: Optional[dict] = None,
    ) -> None:
        """Edit an existing message in Telegram (used for live progress bars and menus)."""
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup

        try:
            requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/editMessageText",
                json=payload,
                proxies=self.proxies,
                timeout=10,
            )
        except Exception as err:
            logger.debug(f"Could not edit progress message {message_id}: {err}")

    def answer_callback(
        self,
        callback_query_id: str,
        text: Optional[str] = None,
        show_alert: bool = False,
    ) -> None:
        """Acknowledge or respond to an inline button click."""
        payload = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
            payload["show_alert"] = show_alert
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/answerCallbackQuery",
                json=payload,
                proxies=self.proxies,
                timeout=8,
            )
        except Exception as err:
            logger.debug(f"Could not answer callback query {callback_query_id}: {err}")

    def set_bot_commands(self) -> None:
        """Register command list in Telegram client UI."""
        commands = [
            {"command": "start", "description": "🏠 Главное меню и статус"},
            {"command": "code", "description": "💻 Готовый код для запуска (без лишнего)"},
            {"command": "search", "description": "🔍 Поиск объявлений с выгрузкой в Excel"},
            {"command": "workers", "description": "🧵 Настройка потоков (1-2 для 1 модема)"},
            {"command": "limit", "description": "📦 Лимит объявлений (10..1000 шт, до 5000)"},
            {"command": "status", "description": "📊 Состояние прокси и параметры сбора"},
            {"command": "help", "description": "ℹ️ Инструкция и примеры"},
        ]
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/setMyCommands",
                json={"commands": commands},
                proxies=self.proxies,
                timeout=8,
            )
        except Exception:
            pass

    def send_excel(
        self,
        filepath: Union[str, Path],
        caption: Optional[str] = None,
        target_chat_ids: Optional[Sequence[str]] = None,
    ) -> None:
        """Upload a generated Excel (.xlsx) file directly to Telegram chat/channel."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")

        chats = target_chat_ids if target_chat_ids is not None else self.chat_ids
        for cid in chats:
            def _send_doc():
                with open(path, "rb") as f:
                    data = {"chat_id": cid}
                    if caption:
                        data["caption"] = caption
                    return requests.post(
                        f"https://api.telegram.org/bot{self.bot_token}/sendDocument",
                        data=data,
                        files={
                            "document": (
                                path.name,
                                f,
                                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            )
                        },
                        proxies=self.proxies,
                        timeout=45,
                    )

            self._request_with_retries(_send_doc)

    def start_progress(
        self,
        query: str,
        total: int = 0,
        use_mobile_proxy: bool = False,
        workers: int = 1,
    ) -> Dict[str, int]:
        """Send an initial live progress bar message to Telegram."""
        import html
        bar = render_telegram_progress_bar(0, total)
        proxy_status = "Подключен (Mobile 4G LTE)" if use_mobile_proxy else "Без прокси"
        text = (
            f"🚀 <b>Сбор данных с Авито</b>\n\n"
            f"🔍 <b>Запрос:</b> <code>{html.escape(query)}</code>\n"
            f"📊 <b>Прогресс:</b> {bar}\n\n"
            f"🌐 <b>Мобильный прокси:</b> {proxy_status}\n"
            f"🧵 <b>Потоков:</b> {workers} <i>(Safe Mode: 1 модем)</i>\n"
            f"⚡ <i>Запуск сбора и обогащения характеристик...</i>"
        )
        return self.send_message(text, parse_mode="HTML")

    def update_progress(
        self,
        progress_ids: Dict[str, int],
        query: str,
        current: int,
        total: int,
        use_mobile_proxy: bool = False,
        workers: int = 1,
        drops_count: int = 0,
        ip_rotations: int = 0,
    ) -> None:
        """Update the live progress bar message in Telegram."""
        import html
        bar = render_telegram_progress_bar(current, total)
        proxy_status = f"Активен (ротаций IP: {ip_rotations})" if use_mobile_proxy else "Без прокси"
        text = (
            f"⏳ <b>Сбор данных с Авито в процессе...</b>\n\n"
            f"🔍 <b>Запрос:</b> <code>{html.escape(query)}</code>\n"
            f"📊 <b>Прогресс:</b> {bar}\n\n"
            f"📦 <b>Собрано:</b> {current} из {total}\n"
            f"🌐 <b>Мобильный прокси:</b> {proxy_status}\n"
            f"🧵 <b>Потоков:</b> {workers}  |  📉 <b>Снижений цен:</b> {drops_count}\n"
            f"⚡ <i>Обогащение характеристик и запись в Excel...</i>"
        )
        for cid, mid in progress_ids.items():
            self.edit_message(cid, mid, text, parse_mode="HTML")

    def finish_progress(
        self,
        progress_ids: Dict[str, int],
        query: str,
        total_found: int,
        use_mobile_proxy: bool = False,
        drops_count: int = 0,
        ip_rotations: int = 0,
        excel_path: Optional[Union[str, Path]] = None,
    ) -> None:
        """Mark the live progress bar as 100% complete and optionally upload the Excel file."""
        import html
        bar = render_telegram_progress_bar(total_found, max(total_found, 1))
        proxy_status = f"Активен (ротаций IP: {ip_rotations})" if use_mobile_proxy else "Без прокси"
        text = (
            f"✅ <b>Парсинг успешно завершён!</b>\n\n"
            f"🔍 <b>Запрос:</b> <code>{html.escape(query)}</code>\n"
            f"📊 <b>Прогресс:</b> {bar}\n\n"
            f"📦 <b>Собрано объявлений:</b> {total_found}\n"
            f"📉 <b>Снижений цен:</b> {drops_count}\n"
            f"🌐 <b>Мобильный прокси:</b> {proxy_status}\n"
            f"🧵 <b>Потоков:</b> Safe Mode (1 модем)\n\n"
            f"📊 <i>Детальный отчёт Excel (.xlsx) с ценами и продавцами загружается ниже 👇</i>"
        )
        for cid, mid in progress_ids.items():
            self.edit_message(cid, mid, text, parse_mode="HTML")

        if excel_path and Path(excel_path).exists():
            caption = f"📊 Отчёт Excel: {query} ({total_found} объявлений)"
            self.send_excel(excel_path, caption=caption, target_chat_ids=list(progress_ids.keys()))

    def _send_photo_bytes(self, chat_id: str, image_url: str, caption: str) -> bool:
        try:
            img_resp = requests.get(image_url, proxies=self.proxies, timeout=15)
            img_resp.raise_for_status()
            image_bytes = img_resp.content
        except Exception as e:
            logger.warning(f"Could not download image for Telegram multipart upload: {e}")
            return False

        def _send():
            return requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/sendPhoto",
                data={
                    "chat_id": chat_id,
                    "caption": caption,
                    "parse_mode": "MarkdownV2",
                },
                files={"photo": ("photo.jpg", image_bytes, "image/jpeg")},
                proxies=self.proxies,
                timeout=30,
            )

        try:
            self._request_with_retries(_send)
            return True
        except Exception as e:
            logger.warning(f"Telegram multipart photo upload failed: {e}")
            return False

    def notify(self, item: Optional[Item] = None, message: Optional[str] = None) -> None:
        """Send an Item notification (or custom text message) to all configured Telegram channels/chats."""
        if item is None:
            if message:
                self.send_message(escape_markdown_v2(message))
            return

        formatted = self.format_item(item)
        first_image = item.images[0] if item.images else None

        for cid in self.chat_ids:
            if self.only_text or not first_image:
                self._send_text_to_chat(cid, formatted)
                continue

            def _send_photo():
                return requests.post(
                    f"https://api.telegram.org/bot{self.bot_token}/sendPhoto",
                    json={
                        "chat_id": cid,
                        "caption": formatted,
                        "photo": first_image,
                        "parse_mode": "MarkdownV2",
                    },
                    proxies=self.proxies,
                    timeout=12,
                )

            try:
                self._request_with_retries(_send_photo)
            except requests.HTTPError as e:
                if e.response is not None and e.response.status_code == 400:
                    uploaded = self._send_photo_bytes(cid, first_image, formatted)
                    if not uploaded:
                        self._send_text_to_chat(cid, formatted)
                else:
                    raise

    def notify_many(self, items: Sequence[Item]) -> None:
        """Send multiple items sequentially to Telegram."""
        for item in items:
            self.notify(item=item)


class AvitoTelegramBot:
    """
    Interactive Telegram Bot controller for Avito parsing with:
    - Rich interactive Inline Keyboards and callbacks
    - Built-in multi-threading safety limit (max 2 workers for 1 modem)
    - Full privacy mode (zero credentials leaked in UI or logs)
    - Live visual emoji progress bars ([🟩🟩🟩⬜⬜] 60%)
    - Instant Excel (.xlsx) file generation and delivery
    """

    def __init__(
        self,
        bot_token: str,
        proxy: Optional[str] = None,
        proxy_change_url: Optional[str] = None,
        channel_id: Optional[Union[str, int]] = None,
        workers: int = 2,
        limit: int = 30,
        enrich_details: bool = True,
        use_playwright_cookies: bool = False,
        modems_count: int = 1,
    ):
        self.bot_token = bot_token
        self.proxy = proxy
        self.proxy_change_url = proxy_change_url
        self.channel_id = str(channel_id) if channel_id else None
        self.modems_count = max(1, int(modems_count))
        self.workers = min(max(1, int(workers)), 16)
        if self.workers > self.modems_count * 2:
            logger.info(
                f"[TelegramBot] Запущено {self.workers} потоков (Fast/Turbo Mode) "
                f"с адаптивным микро-сглаживанием запросов."
            )
        self.limit = max(1, limit)
        self.enrich_details = enrich_details
        self.use_playwright_cookies = use_playwright_cookies
        self._offset = 0

    def _main_keyboard(self) -> dict:
        enrich_icon = "✅ ВКЛ" if self.enrich_details else "❌ ВЫКЛ"
        return {
            "inline_keyboard": [
                [
                    {"text": "🔍 Начать поиск", "callback_data": "menu_search"},
                    {"text": "📊 Статус системы", "callback_data": "menu_status"},
                ],
                [
                    {"text": f"🧵 Потоки: {self.workers} воркера", "callback_data": "menu_workers"},
                    {"text": f"📦 Лимит: {self.limit} шт", "callback_data": "menu_limit"},
                ],
                [
                    {"text": f"📋 Характеристики: {enrich_icon}", "callback_data": "toggle_enrich"},
                    {"text": "🌐 Мобильный прокси", "callback_data": "menu_proxy"},
                ],
                [
                    {"text": "💻 Готовый код для запуска", "callback_data": "menu_code"},
                    {"text": "ℹ️ Инструкция", "callback_data": "menu_help"},
                ],
            ]
        }

    def _workers_keyboard(self) -> dict:
        def _wm(n):
            return " ✅" if self.workers == n else ""
        return {
            "inline_keyboard": [
                [
                    {"text": f"🧵 1 поток{_wm(1)}", "callback_data": "set_workers:1"},
                    {"text": f"🧵 2 потока (Safe){_wm(2)}", "callback_data": "set_workers:2"},
                ],
                [
                    {"text": f"⚡ 4 потока (Fast){_wm(4)}", "callback_data": "set_workers:4"},
                    {"text": f"🚀 8 потоков (Turbo){_wm(8)}", "callback_data": "set_workers:8"},
                ],
                [
                    {"text": "❓ Подробнее о скорости и воркерах", "callback_data": "faq_workers"},
                ],
                [
                    {"text": "« Назад в главное меню", "callback_data": "menu_main"},
                ],
            ]
        }

    def _limit_keyboard(self) -> dict:
        def _m(n):
            return " ✅" if self.limit == n else ""
        return {
            "inline_keyboard": [
                [
                    {"text": f"10 шт{_m(10)}", "callback_data": "set_limit:10"},
                    {"text": f"50 шт{_m(50)}", "callback_data": "set_limit:50"},
                    {"text": f"100 шт{_m(100)}", "callback_data": "set_limit:100"},
                ],
                [
                    {"text": f"200 шт{_m(200)}", "callback_data": "set_limit:200"},
                    {"text": f"500 шт{_m(500)}", "callback_data": "set_limit:500"},
                    {"text": f"1000 шт{_m(1000)}", "callback_data": "set_limit:1000"},
                ],
                [
                    {"text": "« Назад в главное меню", "callback_data": "menu_main"},
                ],
            ]
        }

    def _search_prompt_keyboard(self) -> dict:
        return {
            "inline_keyboard": [
                [
                    {"text": "💻 RTX 4090", "callback_data": "quick_search:RTX 4090"},
                    {"text": "📱 iPhone 15 Pro", "callback_data": "quick_search:iPhone 15 Pro"},
                ],
                [
                    {"text": "💻 Ноутбуки", "callback_data": "quick_search:Ноутбуки"},
                    {"text": "🏢 Квартиры", "callback_data": "quick_search:Квартиры"},
                ],
                [
                    {"text": "« Назад в главное меню", "callback_data": "menu_main"},
                ],
            ]
        }

    def _back_keyboard(self) -> dict:
        return {
            "inline_keyboard": [
                [
                    {"text": "« Назад в главное меню", "callback_data": "menu_main"},
                ]
            ]
        }

    def _status_text(self) -> str:
        proxy_state = "✅ Подключен (Mobile 4G LTE)" if self.proxy else "❌ Не задан"
        rot_state = "✅ Активна (MobileProxy.space)" if self.proxy_change_url else "❌ Не задана"
        enrich_state = "ВКЛ (глубокий сбор)" if self.enrich_details else "ВЫКЛ (только выдача)"
        chan_state = self.channel_id or "Текущий диалог"
        return (
            "🤖 <b>Панель управления Avito SDK Bot</b>\n\n"
            f"🌐 <b>Мобильный прокси:</b> {proxy_state}\n"
            f"🔄 <b>Автосмена IP:</b> {rot_state}\n"
            f"🧵 <b>Потоков (воркеров):</b> <code>{self.workers}</code> <i>(Safe Mode: 1 модем)</i>\n"
            f"📦 <b>Лимит выдачи:</b> <code>{self.limit}</code> объявлений\n"
            f"📋 <b>Сбор характеристик:</b> {enrich_state}\n"
            f"📢 <b>Канал уведомлений:</b> {chan_state}\n"
            "🔒 <b>Режим приватности:</b> Активен (данные прокси скрыты для видео)\n\n"
            "💡 <i>Отправьте любой поисковый запрос (например: <code>RTX 4090</code>) "
            "или прямую ссылку на каталог Авито — бот сразу запустит сбор и пришлёт Excel-отчёт!</i>"
        )

    def _proxy_info_text(self) -> str:
        proxy_state = "✅ Подключен (Mobile 4G LTE)" if self.proxy else "❌ Не задан"
        rot_state = "✅ Активна (MobileProxy.space)" if self.proxy_change_url else "❌ Не задана"
        return (
            "🌐 <b>Управление мобильным прокси</b>\n\n"
            f"• <b>Статус:</b> {proxy_state}\n"
            f"• <b>Автоматическая ротация IP:</b> {rot_state}\n"
            "• <b>Защита от банов:</b> ВКЛ (мгновенная ротация при SmartCaptcha/429)\n"
            "• <b>Режим видеозаписи:</b> 🔒 Полная маскировка логинов, паролей и URL\n\n"
            "💡 <b>Для смены прокси отправьте команду:</b>\n"
            "<code>/proxy http://user:pass@host:port [url_ротации_ip]</code>"
        )

    def _code_text(self) -> str:
        return (
            "💻 <b>Минимальный код для запуска (без лишнего boilerplate):</b>\n\n"
            "📦 <b>1. Установка библиотеки:</b>\n"
            "<code>uv add avito-sdk</code>\n"
            "<i>или:</i> <code>pip install avito-sdk</code>\n\n"
            "🚀 <b>2. Простой Python-код:</b>\n\n"
            "<pre><code class=\"language-python\">from avito_sdk import AvitoClient\n\n"
            "# 1. Подключение (подставьте свои данные прокси)\n"
            "client = AvitoClient(\n"
            "    proxy=\"http://login:password@host:port\",\n"
            "    proxy_change_url=\"https://changeip.mobileproxy.space/?proxy_key=...\",\n"
            "    modems_count=1,\n"
            ")\n\n"
            "# 2. Поиск по запросу (или по прямой ссылке на каталог Авито)\n"
            "for item in client.search(\"RTX 4090\", limit=10, show_progress=True):\n"
            "    print(f\"{item.title} | {item.price:,} ₽\")\n"
            "    print(f\"Ссылка: {item.url}\")\n"
            "    print(f\"Продавец: {item.seller_name} | Просмотров: {item.total_views}\")\n\n"
            "# 3. Либо выгрузка по ссылке сразу в Excel (.xlsx)\n"
            "client.scrape_url(\n"
            "    url=\"https://www.avito.ru/moskva/noutbuki?cd=1\",\n"
            "    limit=30,\n"
            "    enrich_details=True,\n"
            "    excel_path=\"noutbuki.xlsx\",\n"
            ")</code></pre>\n\n"
            "💡 <i>Код полностью готов к работе, не содержит лишних main-функций и автоматически меняет IP при капче!</i>"
        )

    def _help_text(self) -> str:
        return (
            "📖 <b>Инструкция по использованию Avito SDK Bot</b>\n\n"
            "1️⃣ <b>Быстрый поиск:</b>\n"
            "Просто напишите в чат любой текст для поиска:\n"
            "• <code>RTX 4090</code>\n"
            "• <code>ноутбук lenovo legion 5</code>\n"
            "• <code>iphone 15 pro max 256</code>\n\n"
            "2️⃣ <b>Поиск по ссылке с фильтрами:</b>\n"
            "Настройте фильтры на Авито (город, цена, сортировка) и отправьте ссылку:\n"
            "• <code>https://m.avito.ru/moskva/noutbuki?...</code>\n\n"
            "3️⃣ <b>Контроль потоков (/workers):</b>\n"
            "Для 1 мобильного модема безопасно использовать <b>до 2 потоков</b>. "
            "Это ускоряет сбор в 2 раза и на 100% исключает баны Avito WAF.\n\n"
            "4️⃣ <b>Экспорт данных:</b>\n"
            "По окончании сбора бот автоматически формирует и присылает детальный "
            "файл Excel (.xlsx) с ценами, продавцами, характеристиками и ссылками."
        )

    def _run_search_flow(self, chat_id: str, query: str) -> None:
        from avito_sdk.client import AvitoClient
        notifier = TelegramNotifier(bot_token=self.bot_token, chat_id=chat_id)
        target_chats = [chat_id]
        if self.channel_id and self.channel_id != chat_id:
            target_chats.append(self.channel_id)

        client = AvitoClient(
            proxy=self.proxy,
            proxy_change_url=self.proxy_change_url,
            use_playwright_cookies=self.use_playwright_cookies,
            tg_token=self.bot_token,
            tg_chat_id=target_chats,
            modems_count=self.modems_count,
        )

        reports_dir = Path("storage/reports")
        reports_dir.mkdir(parents=True, exist_ok=True)
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        excel_path = reports_dir / f"avito_results_{timestamp}.xlsx"

        try:
            pages_needed = max(1, (self.limit + 29) // 30)
            if query.startswith("http://") or query.startswith("https://"):
                items = client.scrape_url(
                    url=query,
                    max_pages=pages_needed,
                    limit=self.limit,
                    enrich_details=self.enrich_details,
                    max_workers=self.workers,
                    telegram_progress=True,
                    excel_path=excel_path,
                )
                if not items:
                    notifier.send_message(
                        "ℹ️ По данной ссылке не найдено активных объявлений.\n"
                        "💡 <i>Проверьте ссылку в браузере: возможно, в адресе опечатка или страница не существует на Авито.</i>",
                        parse_mode="HTML",
                    )
                return len(items)
            else:
                items = list(
                    client.search(
                        query=query,
                        max_pages=pages_needed,
                        enrich_details=self.enrich_details,
                        max_workers=self.workers,
                        limit=self.limit,
                        telegram_progress=True,
                        excel_path=excel_path,
                    )
                )
                if not items:
                    notifier.send_message(
                        f"ℹ️ По запросу «{query}» не найдено объявлений.",
                        parse_mode=None,
                    )
                return len(items)
        except Exception as err:
            logger.error(f"Search flow error: {err}")
            notifier.send_message(f"❌ Ошибка при сборе: {err}", parse_mode=None)
            return 0
        finally:
            client.close()

    def handle_callback(self, cb: dict) -> None:
        cb_id = str(cb.get("id", ""))
        msg = cb.get("message") or {}
        chat_id = str(msg.get("chat", {}).get("id", ""))
        mid = msg.get("message_id")
        data = str(cb.get("data", "")).strip()
        if not chat_id or not mid:
            return

        notifier = TelegramNotifier(bot_token=self.bot_token, chat_id=chat_id)

        if data in ("menu_main", "menu_status"):
            notifier.answer_callback(cb_id)
            notifier.edit_message(chat_id, mid, self._status_text(), parse_mode="HTML", reply_markup=self._main_keyboard())
            return

        if data == "menu_workers":
            notifier.answer_callback(cb_id)
            mode_desc = "Safe Mode" if self.workers <= 2 else ("Fast Mode ⚡" if self.workers <= 4 else "Turbo Mode 🚀")
            text = (
                "🧵 <b>Настройка параллельных потоков</b>\n\n"
                f"Текущее значение: <b>{self.workers} воркеров</b> ({mode_desc})\n\n"
                "• <b>1-2 потока (Safe Mode):</b> Идеальная стабильность для 1 мобильного модема.\n"
                "• <b>4 потока (Fast Mode):</b> Ускорение сбора в 2 раза с адаптивным микро-сглаживанием.\n"
                "• <b>8 потоков (Turbo Mode):</b> Максимальная скорость для быстрых 4G-каналов.\n\n"
                "💡 <i>Также можно задать любое число командой:</i> <code>/workers 4</code>"
            )
            notifier.edit_message(chat_id, mid, text, parse_mode="HTML", reply_markup=self._workers_keyboard())
            return

        if data.startswith("set_workers:"):
            num = int(data.split(":")[1])
            self.workers = min(max(1, num), 16)
            mode_desc = "Safe Mode" if self.workers <= 2 else ("Fast Mode ⚡" if self.workers <= 4 else "Turbo Mode 🚀")
            notifier.answer_callback(cb_id, text=f"✅ Установлено: {self.workers} воркеров ({mode_desc})")
            text = (
                "🧵 <b>Настройка параллельных потоков</b>\n\n"
                f"Текущее значение: <b>{self.workers} воркеров</b> ({mode_desc})\n\n"
                "• <b>1-2 потока (Safe Mode):</b> Идеальная стабильность для 1 мобильного модема.\n"
                "• <b>4 потока (Fast Mode):</b> Ускорение сбора в 2 раза с адаптивным микро-сглаживанием.\n"
                "• <b>8 потоков (Turbo Mode):</b> Максимальная скорость для быстрых 4G-каналов.\n\n"
                "💡 <i>Также можно задать любое число командой:</i> <code>/workers 4</code>"
            )
            notifier.edit_message(chat_id, mid, text, parse_mode="HTML", reply_markup=self._workers_keyboard())
            return

        if data == "faq_workers":
            notifier.answer_callback(
                cb_id,
                text="⚡ Скорость и воркеры:\n• 1-2 воркера: без риска блокировок WAF на 1 модеме.\n• 4 воркера: ускоряет сбор в 2 раза благодаря микро-сглаживанию задержек.\n• 8 воркеров: максимальная параллелизация (для 2+ модемов или мощных 4G LTE сессий).",
                show_alert=True,
            )
            return

        if data == "menu_limit":
            notifier.answer_callback(cb_id)
            text = (
                f"📦 <b>Выберите лимит объявлений для выгрузки:</b>\n\n"
                f"Текущий лимит: <b>{self.limit} объявлений</b>\n\n"
                f"💡 <i>Вы также можете задать любое своё число командой:</i> <code>/limit 1000</code> <i>(до 5000)</i>"
            )
            notifier.edit_message(chat_id, mid, text, parse_mode="HTML", reply_markup=self._limit_keyboard())
            return

        if data.startswith("set_limit:"):
            lim = int(data.split(":")[1])
            self.limit = lim
            notifier.answer_callback(cb_id, text=f"✅ Лимит: {self.limit} шт")
            text = (
                f"📦 <b>Выберите лимит объявлений для выгрузки:</b>\n\n"
                f"Текущий лимит: <b>{self.limit} объявлений</b>\n\n"
                f"💡 <i>Вы также можете задать любое своё число командой:</i> <code>/limit 1000</code> <i>(до 5000)</i>"
            )
            notifier.edit_message(chat_id, mid, text, parse_mode="HTML", reply_markup=self._limit_keyboard())
            return

        if data == "toggle_enrich":
            self.enrich_details = not self.enrich_details
            state = "ВКЛ" if self.enrich_details else "ВЫКЛ"
            notifier.answer_callback(cb_id, text=f"Сбор характеристик: {state}")
            notifier.edit_message(chat_id, mid, self._status_text(), parse_mode="HTML", reply_markup=self._main_keyboard())
            return

        if data == "menu_code":
            notifier.answer_callback(cb_id)
            notifier.edit_message(chat_id, mid, self._code_text(), parse_mode="HTML", reply_markup=self._back_keyboard())
            return

        if data == "menu_proxy":
            notifier.answer_callback(cb_id)
            notifier.edit_message(chat_id, mid, self._proxy_info_text(), parse_mode="HTML", reply_markup=self._back_keyboard())
            return

        if data == "menu_help":
            notifier.answer_callback(cb_id)
            notifier.edit_message(chat_id, mid, self._help_text(), parse_mode="HTML", reply_markup=self._back_keyboard())
            return

        if data == "menu_search":
            notifier.answer_callback(cb_id)
            text = (
                "🔍 <b>Поиск объявлений по Авито</b>\n\n"
                "Напишите в ответ любое название товара (например: <code>RTX 4090</code>, <code>iPhone 15</code>) "
                "или вставьте прямую ссылку на каталог Авито.\n\n"
                "Либо выберите один из быстрых примеров ниже:"
            )
            notifier.edit_message(chat_id, mid, text, parse_mode="HTML", reply_markup=self._search_prompt_keyboard())
            return

        if data.startswith("quick_search:"):
            q = data.split(":", 1)[1]
            notifier.answer_callback(cb_id, text=f"🚀 Запуск поиска: {q}")
            self._run_search_flow(chat_id, q)
            return

    def handle_update(self, update: dict) -> None:
        msg = update.get("message") or update.get("channel_post")
        if not msg:
            return
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = (msg.get("text") or "").strip()
        if not chat_id or not text:
            return

        try:
            from pathlib import Path
            Path("storage").mkdir(exist_ok=True)
            Path("storage/last_chat_id.txt").write_text(str(chat_id), encoding="utf-8")
        except Exception:
            pass

        notifier = TelegramNotifier(bot_token=self.bot_token, chat_id=chat_id)

        if text.startswith("/code"):
            notifier.send_message(self._code_text(), parse_mode="HTML", reply_markup=self._back_keyboard())
            return

        if text.startswith("/start") or text.startswith("/help") or text.startswith("/status"):
            notifier.send_message(self._status_text(), parse_mode="HTML", reply_markup=self._main_keyboard())
            return

        if text.startswith("/playwright"):
            self.use_playwright_cookies = not self.use_playwright_cookies
            state = "ВКЛ (Playwright Chromium)" if self.use_playwright_cookies else "ВЫКЛ (быстрый HTTP)"
            notifier.send_message(f"🎭 Сбор cookies через Playwright: <b>{state}</b>", parse_mode="HTML")
            return

        if text.startswith("/proxy"):
            parts = text.split()
            if len(parts) >= 2:
                self.proxy = parts[1]
                if len(parts) >= 3:
                    self.proxy_change_url = parts[2]
                rot_str = "✅ Активна" if self.proxy_change_url else "❌ Не настроена"
                notifier.send_message(
                    "✅ <b>Мобильный прокси успешно настроен и защищён!</b>\n\n"
                    "🌐 <b>Статус:</b> Подключен (Mobile 4G LTE)\n"
                    f"🔄 <b>Автосмена IP:</b> {rot_str}\n"
                    "🔒 <b>Безопасность:</b> Учётные данные и ключи скрыты для видеозаписи.",
                    parse_mode="HTML",
                    reply_markup=self._main_keyboard(),
                )
            else:
                notifier.send_message(
                    "💡 <b>Использование:</b>\n<code>/proxy http://user:pass@ip:port [url_ротации]</code>",
                    parse_mode="HTML",
                )
            return

        if text.startswith("/workers"):
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                requested = max(1, min(int(parts[1]), 16))
                self.workers = requested
                mode_desc = "Safe Mode" if self.workers <= 2 else ("Fast Mode ⚡" if self.workers <= 4 else "Turbo Mode 🚀")
                notifier.send_message(
                    f"✅ <b>Число воркеров установлено: {self.workers}</b> ({mode_desc})\n\n"
                    f"💡 <i>Включено микро-сглаживание задержек между параллельными запросами для защиты от банов.</i>",
                    parse_mode="HTML",
                    reply_markup=self._workers_keyboard(),
                )
            else:
                mode_desc = "Safe Mode" if self.workers <= 2 else ("Fast Mode ⚡" if self.workers <= 4 else "Turbo Mode 🚀")
                notifier.send_message(
                    f"🧵 Текущее число воркеров: <b>{self.workers}</b> ({mode_desc})\n"
                    f"Доступно от 1 до 16 потоков: <code>/workers 4</code> или <code>/workers 8</code>",
                    parse_mode="HTML",
                    reply_markup=self._workers_keyboard(),
                )
            return

        if text.startswith("/limit"):
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                self.limit = max(1, min(int(parts[1]), 5000))
                notifier.send_message(f"✅ Лимит объявлений установлен: <b>{self.limit}</b>", parse_mode="HTML", reply_markup=self._limit_keyboard())
            else:
                notifier.send_message(f"📦 Текущий лимит: <b>{self.limit}</b>", parse_mode="HTML", reply_markup=self._limit_keyboard())
            return

        query = text[len("/search"):].strip() if text.startswith("/search") else text
        if not query or query.startswith("/"):
            return

        import re
        urls = re.findall(r'https?://[^\s]+', query)
        if len(urls) > 1:
            notifier.send_message(
                f"🔗 <b>Обнаружено {len(urls)} ссылки для сбора данных!</b>\n\n"
                f"Запускаю последовательный сбор каждой ссылки (лимит: <b>{self.limit}</b> на ссылку, воркеров: <b>{self.workers}</b>)...",
                parse_mode="HTML",
            )
            success_count = 0
            total_items = 0
            for idx, u in enumerate(urls, 1):
                notifier.send_message(f"⏳ <i>[Ссылка {idx}/{len(urls)}] Обработка:</i> <code>{u[:50]}...</code>", parse_mode="HTML")
                cnt = self._run_search_flow(chat_id, u) or 0
                if cnt > 0:
                    success_count += 1
                    total_items += cnt

            if success_count == len(urls):
                notifier.send_message(f"🎉 <b>Все {len(urls)} ссылки успешно выгружены в Excel!</b> (Всего собрано: {total_items} объявл.)", parse_mode="HTML")
            else:
                notifier.send_message(
                    f"🏁 <b>Сбор завершён:</b> обработано ссылок: {len(urls)}, успешно: {success_count}, собрано объявлений: {total_items}.\n"
                    f"💡 <i>Если по какой-то ссылке найдено 0 объявлений — проверьте её открытие в браузере.</i>",
                    parse_mode="HTML",
                )
            return

        self._run_search_flow(chat_id, query)

    def run_polling(self, poll_interval: float = 1.0) -> None:
        """Start infinite long-polling loop for the Telegram bot controller."""
        notifier = TelegramNotifier(bot_token=self.bot_token, chat_id="")
        notifier.set_bot_commands()
        print("[*] AvitoTelegramBot запущен! Меню и команды зарегистрированы в Telegram.")
        print("[*] Ожидание действий пользователя (Ctrl+C для остановки)...")
        while True:
            try:
                resp = requests.get(
                    f"https://api.telegram.org/bot{self.bot_token}/getUpdates",
                    params={"offset": self._offset, "timeout": 25},
                    timeout=35,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    for upd in data.get("result", []):
                        self._offset = max(self._offset, upd["update_id"] + 1)
                        if "callback_query" in upd:
                            self.handle_callback(upd["callback_query"])
                        elif "message" in upd or "channel_post" in upd:
                            self.handle_update(upd)
            except KeyboardInterrupt:
                print("\n[*] Остановка бота.")
                break
            except Exception as err:
                logger.warning(f"Polling error: {err}")
                time.sleep(poll_interval)
