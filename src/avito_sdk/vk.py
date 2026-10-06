"""
VKontakte notification engine (VKNotifier) for avito-sdk.
Ported from Duff89/parser_avito (integrations/notifications/vk.py):
- Sends formatted item alerts with old/new price arrows (📉 50 000 ₽ ➔ 45 000 ₽)
- Uploads item photos directly to VK messages (photos.getMessagesUploadServer -> photos.saveMessagesPhoto)
- Supports multiple recipient user_ids
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional, Sequence, Union

import requests

from avito_sdk.models import Item

logger = logging.getLogger("avito_sdk")


class VKNotifier:
    """Sends Avito listing alerts and photos to VKontakte users."""

    def __init__(
        self,
        vk_token: str,
        user_id: Union[str, int, Sequence[Union[str, int]]],
        max_retries: int = 3,
    ):
        self.vk_token = vk_token
        if isinstance(user_id, (str, int)):
            self.user_ids: List[str] = [str(user_id)]
        else:
            self.user_ids = [str(uid) for uid in user_id if str(uid).strip()]
        self.max_retries = max_retries

    @staticmethod
    def format_item(item: Item) -> str:
        """Format an Item into a clean VK message (with price change arrows and parameters)."""
        price_val = item.price or 0
        price_str = f"{price_val:,}".replace(",", " ") + " ₽"
        title = (item.title or f"Объявление #{item.id}").replace("\xa0", " ")
        short_url = item.url or f"https://avito.ru/{item.id}"
        seller_display = item.seller_name or item.seller_id or ""

        parts: List[str] = []
        if item.old_price is not None and item.old_price != price_val:
            old_formatted = f"{item.old_price:,}".replace(",", " ") + " ₽"
            arrow = "📉" if price_val < item.old_price else "📈"
            price_part = f"{arrow} {old_formatted} ➔ {price_str}"
            if getattr(item, "is_promotion", False):
                price_part += " 🔥"
            parts.append(price_part)
        else:
            price_part = f"💰 {price_str}"
            if getattr(item, "is_promotion", False):
                price_part += " 🔥"
            parts.append(price_part)

        parts.append(f"📦 {title}")
        if seller_display:
            parts.append(f"👤 Продавец: {seller_display}")
        if item.params:
            params_preview = "; ".join(f"{k}: {v}" for k, v in list(item.params.items())[:6])
            parts.append(f"📋 {params_preview}")
        parts.append(f"🔗 {short_url}")
        return "\n".join(parts)

    def _upload_photo(self, photo_url: str) -> Optional[str]:
        headers = {"Authorization": f"Bearer {self.vk_token}"}
        try:
            srv_resp = requests.post(
                "https://api.vk.com/method/photos.getMessagesUploadServer",
                headers=headers,
                params={"v": "5.199"},
                timeout=10,
            ).json()
            if "error" in srv_resp:
                return None
            upload_url = srv_resp["response"]["upload_url"]
            photo_bytes = requests.get(photo_url, timeout=12).content
            up_resp = requests.post(
                upload_url,
                files={"photo": ("photo.jpg", photo_bytes, "image/jpeg")},
                timeout=20,
            ).json()
            if not up_resp.get("photo") or up_resp.get("photo") == "[]":
                return None
            save_resp = requests.post(
                "https://api.vk.com/method/photos.saveMessagesPhoto",
                headers=headers,
                params={
                    "photo": up_resp["photo"],
                    "server": up_resp["server"],
                    "hash": up_resp["hash"],
                    "v": "5.199",
                },
                timeout=10,
            ).json()
            if "error" in save_resp:
                return None
            info = save_resp["response"][0]
            return f"photo{info['owner_id']}_{info['id']}"
        except Exception as err:
            logger.debug(f"VK photo upload failed: {err}")
            return None

    def send_message(self, message: str, attachment: Optional[str] = None) -> None:
        headers = {"Authorization": f"Bearer {self.vk_token}"}
        for uid in self.user_ids:
            payload = {
                "user_id": uid,
                "random_id": 0,
                "message": message,
                "v": "5.199",
            }
            if attachment:
                payload["attachment"] = attachment
            for attempt in range(1, self.max_retries + 1):
                try:
                    requests.post(
                        "https://api.vk.com/method/messages.send",
                        headers=headers,
                        data=payload,
                        timeout=12,
                    )
                    break
                except Exception:
                    time.sleep(1.0 * attempt)

    def notify(self, item: Optional[Item] = None, message: Optional[str] = None) -> None:
        if item is None:
            if message:
                self.send_message(message)
            return
        text = self.format_item(item)
        first_image = item.images[0] if item.images else None
        attachment = self._upload_photo(first_image) if first_image else None
        self.send_message(text, attachment=attachment)
