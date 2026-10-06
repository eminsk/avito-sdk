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

    def send_message(self, text: str, parse_mode: Optional[str] = "MarkdownV2") -> Dict[str, int]:
        """Send a text message to all configured Telegram chat_ids and return {chat_id: message_id}."""
        msg_ids: Dict[str, int] = {}
        for cid in self.chat_ids:
            mid = self._send_text_to_chat(cid, text, parse_mode=parse_mode)
            if mid is not None:
                msg_ids[cid] = mid
        return msg_ids

    def _send_text_to_chat(
        self,
        chat_id: str,
        message: str,
        parse_mode: Optional[str] = "MarkdownV2",
    ) -> Optional[int]:
        payload = {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

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
    ) -> None:
        """Edit an existing message in Telegram (used for live progress bars)."""
        payload = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            requests.post(
                f"https://api.telegram.org/bot{self.bot_token}/editMessageText",
                json=payload,
                proxies=self.proxies,
                timeout=10,
            )
        except Exception as err:
            logger.debug(f"Could not edit progress message {message_id}: {err}")

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
        bar = render_telegram_progress_bar(0, total)
        proxy_status = "Активен (автосмена IP)" if use_mobile_proxy else "Без прокси"
        text = (
            f"🚀 Парсинг Авито: {query}\n"
            f"{bar}\n"
            f"🌐 Мобильный прокси: {proxy_status}\n"
            f"🧵 Потоков: {workers}"
        )
        return self.send_message(text, parse_mode=None)

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
        bar = render_telegram_progress_bar(current, total)
        proxy_status = f"Активен (ротаций IP: {ip_rotations})" if use_mobile_proxy else "Без прокси"
        text = (
            f"⏳ Парсинг Авито: {query}\n"
            f"{bar}\n"
            f"🌐 Мобильный прокси: {proxy_status}\n"
            f"🧵 Потоков: {workers}  |  📉 Снижений цен: {drops_count}"
        )
        for cid, mid in progress_ids.items():
            self.edit_message(cid, mid, text, parse_mode=None)

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
        bar = render_telegram_progress_bar(total_found, max(total_found, 1))
        proxy_status = f"Активен (ротаций IP: {ip_rotations})" if use_mobile_proxy else "Без прокси"
        text = (
            f"✅ Парсинг завершён: {query}\n"
            f"{bar}\n"
            f"📦 Собрано объявлений: {total_found}  |  📉 Снижений цен: {drops_count}\n"
            f"🌐 Мобильный прокси: {proxy_status}"
        )
        for cid, mid in progress_ids.items():
            self.edit_message(cid, mid, text, parse_mode=None)

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
    - Mobile proxy management (/proxy)
    - Multithreaded workers setting (/workers)
    - Live visual progress bar ([████████░░░░░░░░] 50%)
    - Automatic Excel (.xlsx) generation and upload right to Telegram!
    """

    def __init__(
        self,
        bot_token: str,
        proxy: Optional[str] = None,
        proxy_change_url: Optional[str] = None,
        channel_id: Optional[Union[str, int]] = None,
        workers: int = 4,
        limit: int = 30,
        enrich_details: bool = True,
        use_playwright_cookies: bool = False,
    ):
        self.bot_token = bot_token
        self.proxy = proxy
        self.proxy_change_url = proxy_change_url
        self.channel_id = str(channel_id) if channel_id else None
        self.workers = workers
        self.limit = limit
        self.enrich_details = enrich_details
        self.use_playwright_cookies = use_playwright_cookies
        self._offset = 0

    def _status_text(self) -> str:
        proxy_State = f"✅ {self.proxy}" if self.proxy else "❌ Не задан (рекомендуется мобильный прокси!)"
        rot_state = "✅ Активна" if self.proxy_change_url else "❌ Не задана"
        pw_state = "✅ ВКЛ (Playwright Chromium)" if self.use_playwright_cookies else "ВЫКЛ (быстрый HTTP)"
        chan_state = self.channel_id or "Текущий чат"
        return (
            "🤖 Панель управления Avito SDK Bot\n\n"
            f"🌐 Мобильный прокси: {proxy_State}\n"
            f"🔄 Автосмена IP: {rot_state}\n"
            f"🎭 Playwright Cookies: {pw_state}\n"
            f"🧵 Потоков (workers): {self.workers}\n"
            f"📋 Сбор характеристик («О помещении»): {'ВКЛ' if self.enrich_details else 'ВЫКЛ'}\n"
            f"📢 Канал для уведомлений: {chan_state}\n\n"
            "Команды:\n"
            "• Отправьте любой поисковый запрос или ссылку https://www.avito.ru/... для запуска сбора с выгрузкой в Excel (.xlsx)!\n"
            "• /search <запрос> — поиск с прогресс-баром и отправкой .xlsx файла\n"
            "• /proxy <http://user:pass@ip:port> [url_смены_ip] — настроить мобильный прокси\n"
            "• /playwright — включить/выключить сбор cookies через Playwright\n"
            "• /workers <число> — задать число потоков\n"
            "• /limit <число> — лимит объявлений за раз"
        )

    def handle_update(self, update: dict) -> None:
        from avito_sdk.client import AvitoClient

        msg = update.get("message") or update.get("channel_post")
        if not msg:
            return
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = (msg.get("text") or "").strip()
        if not chat_id or not text:
            return

        notifier = TelegramNotifier(bot_token=self.bot_token, chat_id=chat_id)

        if text.startswith("/start") or text.startswith("/help") or text.startswith("/status"):
            notifier.send_message(self._status_text(), parse_mode=None)
            return

        if text.startswith("/playwright"):
            self.use_playwright_cookies = not self.use_playwright_cookies
            state = "ВКЛ (Playwright Chromium)" if self.use_playwright_cookies else "ВЫКЛ"
            notifier.send_message(f"🎭 Сбор cookies через Playwright: {state}", parse_mode=None)
            return

        if text.startswith("/proxy"):
            parts = text.split()
            if len(parts) >= 2:
                self.proxy = parts[1]
                if len(parts) >= 3:
                    self.proxy_change_url = parts[2]
                notifier.send_message(
                    f"✅ Мобильный прокси обновлён!\nПрокси: {self.proxy}\nАвтосмена IP: {bool(self.proxy_change_url)}",
                    parse_mode=None,
                )
            else:
                notifier.send_message(
                    "Использование: /proxy http://user:pass@ip:port https://changeip.mobileproxy.space/?proxy_key=...",
                    parse_mode=None,
                )
            return

        if text.startswith("/workers"):
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                self.workers = max(1, min(int(parts[1]), 16))
                notifier.send_message(f"✅ Число потоков установлено: {self.workers}", parse_mode=None)
            return

        if text.startswith("/limit"):
            parts = text.split()
            if len(parts) >= 2 and parts[1].isdigit():
                self.limit = max(1, min(int(parts[1]), 500))
                notifier.send_message(f"✅ Лимит объявлений установлен: {self.limit}", parse_mode=None)
            return

        query = text[len("/search"):].strip() if text.startswith("/search") else text
        if not query or query.startswith("/"):
            return

        target_chats = [chat_id]
        if self.channel_id and self.channel_id != chat_id:
            target_chats.append(self.channel_id)

        client = AvitoClient(
            proxy=self.proxy,
            proxy_change_url=self.proxy_change_url,
            use_playwright_cookies=self.use_playwright_cookies,
            tg_token=self.bot_token,
            tg_chat_id=target_chats,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            excel_path = Path(tmpdir) / "avito_results.xlsx"
            try:
                if query.startswith("http://") or query.startswith("https://"):
                    client.scrape_url(
                        url=query,
                        max_pages=2,
                        enrich_details=self.enrich_details,
                        max_workers=self.workers,
                        telegram_progress=True,
                        excel_path=excel_path,
                    )
                else:
                    list(
                        client.search(
                            query=query,
                            enrich_details=self.enrich_details,
                            max_workers=self.workers,
                            limit=self.limit,
                            telegram_progress=True,
                            excel_path=excel_path,
                        )
                    )
            except Exception as err:
                notifier.send_message(f"❌ Ошибка при сборе: {err}", parse_mode=None)
            finally:
                client.close()

    def run_polling(self, poll_interval: float = 1.5) -> None:
        """Start infinite long-polling loop for the Telegram bot controller."""
        print("[*] AvitoTelegramBot запущен! Ожидание команд в Telegram (Ctrl+C для остановки)...")
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
                        self.handle_update(upd)
            except KeyboardInterrupt:
                print("\n[*] Остановка бота.")
                break
            except Exception as err:
                logger.warning(f"Polling error: {err}")
                time.sleep(poll_interval)
