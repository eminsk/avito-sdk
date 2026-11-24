"""
Avito SDK Pro — Modern Desktop GUI Application.
High-performance, dark-themed, resilient desktop interface for Avito monitoring & sniping.
"""

from __future__ import annotations

import json
import logging
import os
import queue
import random
import sys
import threading
import time
import webbrowser
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

try:
    import customtkinter as ctk
except ImportError:
    ctk = None

from avito_sdk.client import AvitoClient
from avito_sdk.models import Item
from avito_sdk.telegram import TelegramNotifier
from avito_sdk.export import to_excel, to_json

logger = logging.getLogger("avito_sdk.gui")


def _get_base_dir() -> Path:
    """Return the application base directory (safe for both normal and PyInstaller frozen execution)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    try:
        # parent of src/ is repository root
        return Path(__file__).resolve().parent.parent.parent.parent
    except Exception:
        return Path.cwd()


class GUIConfig:
    """Persistent configuration for the GUI application."""

    CONFIG_PATH = _get_base_dir() / "storage" / "gui_config.json"

    def __init__(self):
        self.urls: List[str] = [
            "https://www.avito.ru/all/bytovaya_tehnika/klimaticheskoe_oborudovanie/pribory_dlia_obrabotki_vozduxa-ASgBAgICAkRguE_SB8BP/category-uvlazhnitel-vozduha?s=104",
            "https://www.avito.ru/all/bytovaya_tehnika?q=smartmi&s=104",
            "https://www.avito.ru/all/bytovaya_tehnika/klimaticheskoe_oborudovanie/category-moyka-vozduha?s=104",
        ]
        self.interval_sec: int = 30
        self.min_price: str = ""
        self.max_price: str = "5000"
        self.white_keywords: str = ""
        self.black_keywords: str = ""
        self.proxy_string: str = ""
        self.proxy_change_url: str = ""
        self.tg_token: str = ""
        self.tg_chat_id: str = ""
        self.tg_proxy: str = ""
        self.tg_only_text: bool = False
        self.only_new: bool = True
        self.track_price_drops: bool = True

    @classmethod
    def load(cls) -> "GUIConfig":
        cfg = cls()
        if cls.CONFIG_PATH.exists():
            try:
                data = json.loads(cls.CONFIG_PATH.read_text(encoding="utf-8"))
                for k, v in data.items():
                    if hasattr(cfg, k):
                        setattr(cfg, k, v)
            except Exception as e:
                logger.warning(f"Failed to load gui_config.json: {e}")
        return cfg

    def save(self) -> None:
        try:
            self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            self.CONFIG_PATH.write_text(
                json.dumps(self.__dict__, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.warning(f"Failed to save gui_config.json: {e}")


class AvitoGUIApp:
    """Main desktop application window built on CustomTkinter."""

    def __init__(self):
        if ctk is None:
            raise RuntimeError(
                "customtkinter is required for the GUI. Run: uv pip install customtkinter"
            )

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Avito SDK Pro — Мониторинг & Снайпинг Объявлений")
        self.root.geometry("1120x760")
        self.root.minsize(960, 640)

        # Windows Taskbar AppUserModelID (ensures custom icon appears on taskbar)
        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("eminsk.avitosdkpro.monitor.0.4.3")
            except Exception:
                pass

        # Set window icon and taskbar / Alt-Tab icon for main and all child windows
        self._app_photo_icon = None
        for icon_candidate in [
            _get_base_dir() / "assets" / "icon.ico",
            Path(__file__).resolve().parent / "assets" / "icon.ico",
        ]:
            if icon_candidate.exists():
                try:
                    self.root.iconbitmap(str(icon_candidate))
                    break
                except Exception:
                    pass

        for png_candidate in [
            _get_base_dir() / "assets" / "icon_256.png",
            _get_base_dir() / "assets" / "icon.png",
            Path(__file__).resolve().parent / "assets" / "icon.png",
        ]:
            if png_candidate.exists():
                try:
                    from PIL import Image, ImageTk
                    pil_img = Image.open(png_candidate)
                    self._app_photo_icon = ImageTk.PhotoImage(pil_img)
                    self.root.iconphoto(True, self._app_photo_icon)
                    break
                except Exception:
                    pass

        self.config = GUIConfig.load()
        self.worker_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.stop_event = threading.Event()
        self.log_queue: queue.Queue[str] = queue.Queue()
        self.item_queue: queue.Queue[Item] = queue.Queue()

        self.seen_ids: Set[int] = set()
        self.discovered_items: List[Item] = []
        self.stats_found = 0
        self.stats_tg_sent = 0
        self.stats_checks = 0

        self._build_ui()
        self._load_config_into_ui()
        self._start_pollers()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        # Header bar
        header_frame = ctk.CTkFrame(self.root, corner_radius=0, height=65, fg_color="#1a1c23")
        header_frame.pack(fill="x", side="top", padx=0, pady=0)

        # App logo icon
        self.logo_image = None
        for png_candidate in [
            _get_base_dir() / "assets" / "icon_256.png",
            _get_base_dir() / "assets" / "icon.png",
            Path(__file__).resolve().parent / "assets" / "icon.png",
        ]:
            if png_candidate.exists():
                try:
                    from PIL import Image
                    pil_img = Image.open(png_candidate)
                    self.logo_image = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(38, 38))
                    break
                except Exception:
                    pass

        if self.logo_image:
            lbl_logo = ctk.CTkLabel(header_frame, image=self.logo_image, text="")
            lbl_logo.pack(side="left", padx=(18, 8), pady=12)

        title_label = ctk.CTkLabel(
            header_frame,
            text="AVITO SDK PRO",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#38bdf8",
        )
        title_label.pack(side="left", padx=(0 if self.logo_image else 20, 8), pady=12)

        badge_label = ctk.CTkLabel(
            header_frame,
            text="v0.4.3 • Autonomous",
            font=ctk.CTkFont(size=11),
            text_color="#94a3b8",
            fg_color="#334155",
            corner_radius=6,
            padx=8,
            pady=2,
        )
        badge_label.pack(side="left", padx=5, pady=18)

        btn_issues = ctk.CTkButton(
            header_frame,
            text="🐛 Баги / GitHub",
            width=120,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=12, weight="bold"),
            command=lambda: webbrowser.open("https://github.com/eminsk/avito-sdk/issues"),
        )
        btn_issues.pack(side="right", padx=(6, 16), pady=16)

        self.status_pill = ctk.CTkLabel(
            header_frame,
            text="● ГОТОВ К РАБОТЕ",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#22c55e",
            fg_color="#064e3b",
            corner_radius=12,
            padx=14,
            pady=4,
        )
        self.status_pill.pack(side="right", padx=(10, 6), pady=15)

        # Quick Stats strip
        stats_strip = ctk.CTkFrame(self.root, height=36, fg_color="#0f172a", corner_radius=0)
        stats_strip.pack(fill="x", side="top", padx=0, pady=0)

        self.lbl_stats_found = ctk.CTkLabel(
            stats_strip,
            text="📦 Найдено лотов: 0",
            font=ctk.CTkFont(size=12),
            text_color="#cbd5e1",
        )
        self.lbl_stats_found.pack(side="left", padx=20, pady=4)

        self.lbl_stats_tg = ctk.CTkLabel(
            stats_strip,
            text="✈️ Отправлено в TG: 0",
            font=ctk.CTkFont(size=12),
            text_color="#cbd5e1",
        )
        self.lbl_stats_tg.pack(side="left", padx=20, pady=4)

        self.lbl_stats_checks = ctk.CTkLabel(
            stats_strip,
            text="⏱️ Проверок: 0",
            font=ctk.CTkFont(size=12),
            text_color="#cbd5e1",
        )
        self.lbl_stats_checks.pack(side="left", padx=20, pady=4)

        # Main Tabview
        self.tabview = ctk.CTkTabview(self.root, corner_radius=10, fg_color="#1e293b")
        self.tabview.pack(fill="both", expand=True, padx=16, pady=12)

        self.tab_monitor = self.tabview.add("🔍 Мониторинг")
        self.tab_feed = self.tabview.add("⚡ Живая лента")
        self.tab_proxy = self.tabview.add("🌐 Прокси")
        self.tab_tg = self.tabview.add("✈️ Telegram")
        self.tab_logs = self.tabview.add("📋 Журнал событий")

        self._build_monitor_tab()
        self._build_feed_tab()
        self._build_proxy_tab()
        self._build_tg_tab()
        self._build_logs_tab()

    def _build_monitor_tab(self) -> None:
        tab = self.tab_monitor

        # Left / Right columns
        col_left = ctk.CTkFrame(tab, fg_color="transparent")
        col_left.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        lbl_urls = ctk.CTkLabel(
            col_left,
            text="Ссылки Avito для мониторинга (по одной на строке):",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        lbl_urls.pack(anchor="w", padx=4, pady=(0, 4))

        self.txt_urls = ctk.CTkTextbox(col_left, height=180, font=ctk.CTkFont(size=12))
        self.txt_urls.pack(fill="x", padx=4, pady=(0, 10))

        # Filters Row
        filter_card = ctk.CTkFrame(col_left, fg_color="#0f172a", corner_radius=8)
        filter_card.pack(fill="x", padx=4, pady=5)

        lbl_filters = ctk.CTkLabel(
            filter_card, text="Фильтры цен и ключевых слов:", font=ctk.CTkFont(size=12, weight="bold")
        )
        lbl_filters.pack(anchor="w", padx=12, pady=(8, 4))

        price_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        price_row.pack(fill="x", padx=10, pady=4)

        self.ent_min_price = ctk.CTkEntry(price_row, placeholder_text="Мин. цена (₽)", width=160)
        self.ent_min_price.pack(side="left", padx=4)

        self.ent_max_price = ctk.CTkEntry(price_row, placeholder_text="Макс. цена (₽)", width=160)
        self.ent_max_price.pack(side="left", padx=4)

        kw_row = ctk.CTkFrame(filter_card, fg_color="transparent")
        kw_row.pack(fill="x", padx=10, pady=(4, 10))

        self.ent_white_kw = ctk.CTkEntry(
            kw_row, placeholder_text="Белый список (слова через запятую)", width=220
        )
        self.ent_white_kw.pack(side="left", fill="x", expand=True, padx=4)

        self.ent_black_kw = ctk.CTkEntry(
            kw_row, placeholder_text="Минус-слова (черный список)", width=220
        )
        self.ent_black_kw.pack(side="left", fill="x", expand=True, padx=4)

        # Right side: Control buttons & settings
        col_right = ctk.CTkFrame(tab, width=320, fg_color="#0f172a", corner_radius=10)
        col_right.pack(side="right", fill="y", padx=10, pady=10)

        lbl_params = ctk.CTkLabel(
            col_right, text="Параметры работы", font=ctk.CTkFont(size=14, weight="bold")
        )
        lbl_params.pack(anchor="w", padx=16, pady=(14, 8))

        lbl_interval = ctk.CTkLabel(col_right, text="Интервал проверки (сек):")
        lbl_interval.pack(anchor="w", padx=16, pady=(4, 2))

        self.combo_interval = ctk.CTkComboBox(
            col_right,
            values=["15", "30", "45", "60", "120", "300"],
            width=260,
        )
        self.combo_interval.set("30")
        self.combo_interval.pack(padx=16, pady=(0, 10))

        self.chk_only_new = ctk.CTkCheckBox(
            col_right, text="Только новые объявления", onvalue=True, offvalue=False
        )
        self.chk_only_new.select()
        self.chk_only_new.pack(anchor="w", padx=16, pady=6)

        self.chk_price_drops = ctk.CTkCheckBox(
            col_right, text="Отслеживать падение цен (📉)", onvalue=True, offvalue=False
        )
        self.chk_price_drops.select()
        self.chk_price_drops.pack(anchor="w", padx=16, pady=6)

        self.chk_tg_notify = ctk.CTkCheckBox(
            col_right, text="Шлать алерты в Telegram", onvalue=True, offvalue=False
        )
        self.chk_tg_notify.select()
        self.chk_tg_notify.pack(anchor="w", padx=16, pady=6)

        # Action Buttons
        self.btn_start = ctk.CTkButton(
            col_right,
            text="▶ ЗАПУСТИТЬ МОНИТОРИНГ",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#16a34a",
            hover_color="#15803d",
            height=46,
            command=self.start_monitoring,
        )
        self.btn_start.pack(fill="x", padx=16, pady=(24, 8))

        self.btn_stop = ctk.CTkButton(
            col_right,
            text="⏹ ОСТАНОВИТЬ",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#dc2626",
            hover_color="#b91c1c",
            height=40,
            state="disabled",
            command=self.stop_monitoring,
        )
        self.btn_stop.pack(fill="x", padx=16, pady=(0, 14))

    def _build_feed_tab(self) -> None:
        tab = self.tab_feed

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=8, pady=(4, 8))

        lbl_feed_title = ctk.CTkLabel(
            top_bar,
            text="Свежие карточки лотов (нажмите кнопку для быстрого выкупа):",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        lbl_feed_title.pack(side="left", padx=4)

        btn_export_xlsx = ctk.CTkButton(
            top_bar,
            text="📊 Экспорт в Excel",
            width=130,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._export_excel,
        )
        btn_export_xlsx.pack(side="right", padx=6)

        btn_clear_feed = ctk.CTkButton(
            top_bar,
            text="🗑 Очистить",
            width=90,
            fg_color="#475569",
            hover_color="#334155",
            command=self._clear_feed,
        )
        btn_clear_feed.pack(side="right", padx=4)

        self.feed_scroll = ctk.CTkScrollableFrame(tab, fg_color="#0f172a", corner_radius=8)
        self.feed_scroll.pack(fill="both", expand=True, padx=8, pady=4)

    def _build_proxy_tab(self) -> None:
        tab = self.tab_proxy
        card = ctk.CTkFrame(tab, fg_color="#0f172a", corner_radius=10)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        lbl_desc = ctk.CTkLabel(
            card,
            text="Настройка сетевых прокси для безопасного парсинга Avito",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#38bdf8",
        )
        lbl_desc.pack(anchor="w", padx=20, pady=(16, 6))

        lbl_info = ctk.CTkLabel(
            card,
            text="Поддерживаются любые типы: Серверные РФ, AstroProxy, Asocks, MobileProxy.space или без прокси.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        lbl_info.pack(anchor="w", padx=20, pady=(0, 10))

        # Mobile Proxy Recommendation Banner
        promo_frame = ctk.CTkFrame(card, fg_color="#1e293b", corner_radius=8)
        promo_frame.pack(fill="x", padx=20, pady=(0, 14))

        lbl_promo = ctk.CTkLabel(
            promo_frame,
            text="📱 Нужен надежный мобильный 4G прокси с ротацией IP без банов?",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#f8fafc",
        )
        lbl_promo.pack(side="left", padx=14, pady=8)

        btn_mobile_link = ctk.CTkButton(
            promo_frame,
            text="MobileProxy.space ↗",
            width=170,
            height=28,
            fg_color="#e11d48",
            hover_color="#be123c",
            font=ctk.CTkFont(size=11, weight="bold"),
            command=lambda: webbrowser.open("https://mobileproxy.space/?p=32111"),
        )
        btn_mobile_link.pack(side="right", padx=12, pady=8)

        lbl_proxy = ctk.CTkLabel(card, text="Строка прокси (HTTP / SOCKS5):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_proxy.pack(anchor="w", padx=20, pady=(6, 2))

        self.ent_proxy_str = ctk.CTkEntry(
            card,
            placeholder_text="Например: логин:пароль@mproxy.site:23915  или  user:pass@host:port",
            width=650,
        )
        self.ent_proxy_str.pack(anchor="w", padx=20, pady=(0, 12))

        lbl_rot = ctk.CTkLabel(
            card,
            text="URL смены IP или ключ (только если используете мобильный модем с ротацией):",
            font=ctk.CTkFont(size=12),
        )
        lbl_rot.pack(anchor="w", padx=20, pady=(4, 2))

        self.ent_proxy_change = ctk.CTkEntry(
            card, placeholder_text="Ссылка смены IP (опционально, для серверных прокси оставить пустым)", width=650
        )
        self.ent_proxy_change.pack(anchor="w", padx=20, pady=(0, 16))

        # Check proxy button & status
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(anchor="w", padx=20, pady=8)

        self.btn_check_proxy = ctk.CTkButton(
            btn_row,
            text="🔍 Проверить прокси",
            width=160,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._check_proxy,
        )
        self.btn_check_proxy.pack(side="left", padx=(0, 12))

        self.lbl_proxy_status = ctk.CTkLabel(
            btn_row, text="Статус: Не проверен", font=ctk.CTkFont(size=12), text_color="#94a3b8"
        )
        self.lbl_proxy_status.pack(side="left", padx=6)

        btn_proxy_help = ctk.CTkButton(
            btn_row,
            text="🐛 Сообщить о баге на GitHub",
            width=190,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            font=ctk.CTkFont(size=11),
            command=lambda: webbrowser.open("https://github.com/eminsk/avito-sdk/issues"),
        )
        btn_proxy_help.pack(side="right", padx=10)

    def _build_tg_tab(self) -> None:
        tab = self.tab_tg
        card = ctk.CTkFrame(tab, fg_color="#0f172a", corner_radius=10)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        lbl_tg_title = ctk.CTkLabel(
            card,
            text="Настройка Telegram-бота для мгновенных алертов",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#38bdf8",
        )
        lbl_tg_title.pack(anchor="w", padx=20, pady=(16, 6))

        lbl_tg_info = ctk.CTkLabel(
            card,
            text="Создайте бота через @BotFather, получите токен и отправьте любое сообщение боту, чтобы узнать свой Chat ID.",
            font=ctk.CTkFont(size=12),
            text_color="#94a3b8",
        )
        lbl_tg_info.pack(anchor="w", padx=20, pady=(0, 14))

        lbl_token = ctk.CTkLabel(card, text="Telegram Bot Token:", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_token.pack(anchor="w", padx=20, pady=(6, 2))

        self.ent_tg_token = ctk.CTkEntry(
            card, placeholder_text="1234567890:AAHdqTcvCH1vGWJxj84xG9_Kqwmtx444444", width=550
        )
        self.ent_tg_token.pack(anchor="w", padx=20, pady=(0, 12))

        lbl_chat_id = ctk.CTkLabel(card, text="Chat ID получателя (можно несколько через запятую):", font=ctk.CTkFont(size=12, weight="bold"))
        lbl_chat_id.pack(anchor="w", padx=20, pady=(4, 2))

        self.ent_tg_chat_id = ctk.CTkEntry(card, placeholder_text="987654321", width=550)
        self.ent_tg_chat_id.pack(anchor="w", padx=20, pady=(0, 12))

        lbl_tg_proxy = ctk.CTkLabel(
            card,
            text="Отдельный прокси для Telegram (нужен, если в вашей сети заблокирован api.telegram.org):",
            font=ctk.CTkFont(size=12),
        )
        lbl_tg_proxy.pack(anchor="w", padx=20, pady=(4, 2))

        self.ent_tg_proxy = ctk.CTkEntry(
            card, placeholder_text="логин:пароль@хост:порт (или оставить пустым, если Telegram доступен)", width=550
        )
        self.ent_tg_proxy.pack(anchor="w", padx=20, pady=(0, 14))

        self.chk_tg_text_only = ctk.CTkCheckBox(
            card, text="Присылать только текст без изображений", onvalue=True, offvalue=False
        )
        self.chk_tg_text_only.pack(anchor="w", padx=20, pady=(0, 16))

        # Test TG Button
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(anchor="w", padx=20, pady=8)

        self.btn_test_tg = ctk.CTkButton(
            btn_row,
            text="🚀 Отправить тестовое сообщение",
            width=220,
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=self._test_telegram,
        )
        self.btn_test_tg.pack(side="left", padx=(0, 12))

        self.lbl_tg_status = ctk.CTkLabel(
            btn_row, text="Статус: Не проверялся", font=ctk.CTkFont(size=12), text_color="#94a3b8"
        )
        self.lbl_tg_status.pack(side="left", padx=6)

    def _build_logs_tab(self) -> None:
        tab = self.tab_logs

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.pack(fill="x", padx=8, pady=(4, 8))

        lbl_logs = ctk.CTkLabel(top_bar, text="Журнал событий в реальном времени:", font=ctk.CTkFont(size=13, weight="bold"))
        lbl_logs.pack(side="left", padx=4)

        btn_clear_log = ctk.CTkButton(
            top_bar, text="Очистить лог", width=110, fg_color="#475569", hover_color="#334155", command=self._clear_log
        )
        btn_clear_log.pack(side="right", padx=4)

        self.txt_logs = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="Consolas", size=11))
        self.txt_logs.pack(fill="both", expand=True, padx=8, pady=4)

    # ------------------ Configuration Management ------------------

    def _load_config_into_ui(self) -> None:
        if self.config.urls:
            self.txt_urls.delete("1.0", "end")
            self.txt_urls.insert("1.0", "\n".join(self.config.urls))

        self.combo_interval.set(str(self.config.interval_sec))
        self.ent_min_price.insert(0, str(self.config.min_price or ""))
        self.ent_max_price.insert(0, str(self.config.max_price or ""))
        self.ent_white_kw.insert(0, str(self.config.white_keywords or ""))
        self.ent_black_kw.insert(0, str(self.config.black_keywords or ""))

        self.ent_proxy_str.insert(0, str(self.config.proxy_string or ""))
        self.ent_proxy_change.insert(0, str(self.config.proxy_change_url or ""))

        self.ent_tg_token.insert(0, str(self.config.tg_token or ""))
        self.ent_tg_chat_id.insert(0, str(self.config.tg_chat_id or ""))
        self.ent_tg_proxy.insert(0, str(self.config.tg_proxy or ""))

        if self.config.only_new:
            self.chk_only_new.select()
        else:
            self.chk_only_new.deselect()

        if self.config.track_price_drops:
            self.chk_price_drops.select()
        else:
            self.chk_price_drops.deselect()

        if self.config.tg_only_text:
            self.chk_tg_text_only.select()
        else:
            self.chk_tg_text_only.deselect()

    def _save_ui_to_config(self) -> None:
        raw_urls = self.txt_urls.get("1.0", "end").strip().splitlines()
        self.config.urls = [u.strip() for u in raw_urls if u.strip()]

        try:
            self.config.interval_sec = int(self.combo_interval.get())
        except ValueError:
            self.config.interval_sec = 30

        self.config.min_price = self.ent_min_price.get().strip()
        self.config.max_price = self.ent_max_price.get().strip()
        self.config.white_keywords = self.ent_white_kw.get().strip()
        self.config.black_keywords = self.ent_black_kw.get().strip()

        self.config.proxy_string = self.ent_proxy_str.get().strip()
        self.config.proxy_change_url = self.ent_proxy_change.get().strip()

        self.config.tg_token = self.ent_tg_token.get().strip()
        self.config.tg_chat_id = self.ent_tg_chat_id.get().strip()
        self.config.tg_proxy = self.ent_tg_proxy.get().strip()

        self.config.only_new = bool(self.chk_only_new.get())
        self.config.track_price_drops = bool(self.chk_price_drops.get())
        self.config.tg_only_text = bool(self.chk_tg_text_only.get())

        self.config.save()

    # ------------------ Logging & Item Queue Poller ------------------

    def log(self, message: str) -> None:
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_queue.put(f"[{ts}] {message}\n")

    def _start_pollers(self) -> None:
        self._drain_queues()

    def _drain_queues(self) -> None:
        # Drain log queue
        while not self.log_queue.empty():
            try:
                msg = self.log_queue.get_nowait()
                self.txt_logs.insert("end", msg)
                self.txt_logs.see("end")
            except queue.Empty:
                break

        # Drain items queue
        while not self.item_queue.empty():
            try:
                item = self.item_queue.get_nowait()
                self._add_item_card(item)
            except queue.Empty:
                break

        # Refresh stats counters
        self.lbl_stats_found.configure(text=f"📦 Найдено лотов: {self.stats_found}")
        self.lbl_stats_tg.configure(text=f"✈️ Отправлено в TG: {self.stats_tg_sent}")
        self.lbl_stats_checks.configure(text=f"⏱️ Проверок: {self.stats_checks}")

        # Schedule next poll in 100ms
        self.root.after(100, self._drain_queues)

    def _clear_log(self) -> None:
        self.txt_logs.delete("1.0", "end")

    def _clear_feed(self) -> None:
        for widget in self.feed_scroll.winfo_children():
            widget.destroy()
        self.discovered_items.clear()
        self.stats_found = 0
        self.lbl_stats_found.configure(text="📦 Найдено лотов: 0")

    def _add_item_card(self, item: Item) -> None:
        card = ctk.CTkFrame(self.feed_scroll, fg_color="#1e293b", corner_radius=8)
        card.pack(fill="x", padx=4, pady=4)

        row_top = ctk.CTkFrame(card, fg_color="transparent")
        row_top.pack(fill="x", padx=10, pady=(6, 2))

        time_str = datetime.now().strftime("%H:%M:%S")
        lbl_time = ctk.CTkLabel(
            row_top, text=f"⏱️ {time_str}", font=ctk.CTkFont(size=11), text_color="#94a3b8"
        )
        lbl_time.pack(side="left")

        price_text = f"{item.price:,} ₽".replace(",", " ") if item.price else "Цена не указана"
        lbl_price = ctk.CTkLabel(
            row_top,
            text=f"💰 {price_text}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#22c55e",
        )
        lbl_price.pack(side="right")

        # Title & location
        lbl_title = ctk.CTkLabel(
            card,
            text=item.title,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#f8fafc",
            anchor="w",
            wraplength=700,
        )
        lbl_title.pack(anchor="w", padx=10, pady=(2, 2))

        meta_parts = []
        if item.location:
            meta_parts.append(f"📍 {item.location}")
        if item.seller_name:
            meta_parts.append(f"👤 {item.seller_name}")

        if meta_parts:
            lbl_meta = ctk.CTkLabel(
                card,
                text="  •  ".join(meta_parts),
                font=ctk.CTkFont(size=11),
                text_color="#94a3b8",
                anchor="w",
            )
            lbl_meta.pack(anchor="w", padx=10, pady=(0, 4))

        # Bottom row with Open button
        row_bot = ctk.CTkFrame(card, fg_color="transparent")
        row_bot.pack(fill="x", padx=10, pady=(2, 6))

        btn_open = ctk.CTkButton(
            row_bot,
            text="Открыть на Avito ↗",
            width=140,
            height=28,
            font=ctk.CTkFont(size=12, weight="bold"),
            fg_color="#0284c7",
            hover_color="#0369a1",
            command=lambda u=item.url: webbrowser.open(u),
        )
        btn_open.pack(side="right")

    # ------------------ Testing Tools ------------------

    def _check_proxy(self) -> None:
        proxy = self.ent_proxy_str.get().strip()
        self.lbl_proxy_status.configure(text="Статус: Проверка соединения...", text_color="#f59e0b")

        def _run():
            try:
                t0 = time.time()
                client = AvitoClient(proxy=proxy or None)
                res = client.scrape_page_items("https://www.avito.ru/rossiya")
                dt = int((time.time() - t0) * 1000)
                client.close()
                self.log(f"Проверка прокси успешна! Ответ за {dt} мс, карточек получено: {len(res)}")
                self.root.after(
                    0,
                    lambda: self.lbl_proxy_status.configure(
                        text=f"Статус: ✅ Работает ({dt} мс)", text_color="#22c55e"
                    ),
                )
            except Exception as e:
                self.log(f"Ошибка проверки прокси: {e}")
                self.root.after(
                    0,
                    lambda: self.lbl_proxy_status.configure(
                        text=f"Статус: ❌ Ошибка подключения", text_color="#ef4444"
                    ),
                )

        threading.Thread(target=_run, daemon=True).start()

    def _test_telegram(self) -> None:
        token = self.ent_tg_token.get().strip()
        chat_id = self.ent_tg_chat_id.get().strip()
        tg_proxy = self.ent_tg_proxy.get().strip()

        if not token or not chat_id:
            self.lbl_tg_status.configure(text="Укажите Token и Chat ID!", text_color="#ef4444")
            return

        self.lbl_tg_status.configure(text="Отправка теста...", text_color="#f59e0b")

        def _run():
            try:
                notifier = TelegramNotifier(bot_token=token, chat_id=chat_id, proxy=tg_proxy or None)
                test_item = Item(
                    id=999999999,
                    title="🔥 Тестовое уведомление от Avito SDK Pro",
                    price=15000,
                    url="https://www.avito.ru",
                    location="Москва",
                    seller_name="Avito SDK Тест",
                )
                notifier.notify(test_item)
                self.log("Тестовое уведомление успешно доставлено в Telegram!")
                self.root.after(
                    0,
                    lambda: self.lbl_tg_status.configure(
                        text="Статус: ✅ Успешно доставлено", text_color="#22c55e"
                    ),
                )
            except Exception as e:
                self.log(f"Ошибка отправки Telegram: {e}")
                self.root.after(
                    0,
                    lambda: self.lbl_tg_status.configure(
                        text=f"Статус: ❌ Ошибка отправки", text_color="#ef4444"
                    ),
                )

        threading.Thread(target=_run, daemon=True).start()

    def _export_excel(self) -> None:
        if not self.discovered_items:
            self.log("Живая лента пуста, нечего экспортировать в Excel.")
            return

        out_path = _get_base_dir() / "result" / f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            to_excel(self.discovered_items, out_path)
            self.log(f"Экспорт успешно сохранен в: {out_path.resolve()}")
            webbrowser.open(str(out_path.parent.resolve()))
        except Exception as e:
            self.log(f"Ошибка экспорта в Excel: {e}")

    # ------------------ Monitoring Engine ------------------

    def start_monitoring(self) -> None:
        if self.is_running:
            return

        self._save_ui_to_config()

        if not self.config.urls:
            self.log("Ошибка: не указаны ссылки для мониторинга!")
            return

        self.is_running = True
        self.stop_event.clear()

        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.status_pill.configure(text="● МОНИТОРИНГ АКТИВЕН", text_color="#38bdf8", fg_color="#0369a1")

        self.log("=== ЗАПУСК ЦИКЛА МОНИТОРИНГА ===")
        self.log(f"Интервал: {self.config.interval_sec} сек. Ссылок в работе: {len(self.config.urls)}")

        self.worker_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.worker_thread.start()

    def stop_monitoring(self) -> None:
        if not self.is_running:
            return

        self.is_running = False
        self.stop_event.set()

        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self.status_pill.configure(text="● ОСТАНОВЛЕН", text_color="#94a3b8", fg_color="#334155")
        self.log("=== МОНИТОРИНГ ОСТАНОВЛЕН ПОЛЬЗОВАТЕЛЕМ ===")

    def _monitoring_loop(self) -> None:
        client = None
        notifier = None

        try:
            client = AvitoClient(
                proxy=self.config.proxy_string or None,
                proxy_change_url=self.config.proxy_change_url or None,
            )

            if self.config.tg_token and self.config.tg_chat_id:
                notifier = TelegramNotifier(
                    bot_token=self.config.tg_token,
                    chat_id=self.config.tg_chat_id,
                    proxy=self.config.tg_proxy or None,
                    only_text=self.config.tg_only_text,
                )

            is_first_pass = True

            while not self.stop_event.is_set():
                for url in self.config.urls:
                    if self.stop_event.is_set():
                        break

                    self.log(f"Опрос ссылки: {url[:70]}...")
                    try:
                        items = client.scrape_url(
                            url=url,
                            max_pages=1,
                            max_workers=1,
                            min_price=int(self.config.min_price) if self.config.min_price.isdigit() else None,
                            max_price=int(self.config.max_price) if self.config.max_price.isdigit() else None,
                            white_keywords=[k.strip() for k in self.config.white_keywords.split(",") if k.strip()] if self.config.white_keywords else None,
                            black_keywords=[k.strip() for k in self.config.black_keywords.split(",") if k.strip()] if self.config.black_keywords else None,
                        )

                        self.stats_checks += 1

                        new_count = 0
                        for item in items:
                            if item.id in self.seen_ids:
                                continue

                            self.seen_ids.add(item.id)
                            self.discovered_items.insert(0, item)
                            self.stats_found += 1
                            new_count += 1

                            self.item_queue.put(item)

                            # Send Telegram alert
                            if notifier and (not is_first_pass or not self.config.only_new):
                                try:
                                    notifier.notify(item)
                                    self.stats_tg_sent += 1
                                    self.log(f"✈️ Алерт отправлен в TG: {item.title[:45]} ({item.price} ₽)")
                                except Exception as e:
                                    self.log(f"Ошибка отправки алерта: {e}")

                        if new_count > 0:
                            self.log(f"Найдено новых лотов: {new_count}")

                    except Exception as e:
                        self.log(f"Ошибка при запросе к Avito: {e}")

                    # Micro pause between URLs
                    time.sleep(2.0)

                is_first_pass = False

                # Jittered sleep interval
                jitter = random.uniform(0.9, 1.15)
                sleep_time = max(5.0, self.config.interval_sec * jitter)
                self.log(f"Пауза перед следующей проверкой: {sleep_time:.1f} сек.")

                steps = int(sleep_time * 10)
                for _ in range(steps):
                    if self.stop_event.is_set():
                        break
                    time.sleep(0.1)

        except Exception as e:
            self.log(f"Фатальная ошибка в цикле мониторинга: {e}")
        finally:
            if client:
                try:
                    client.close()
                except Exception:
                    pass

    def _on_close(self) -> None:
        self.stop_monitoring()
        self._save_ui_to_config()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()


def run_app() -> None:
    app = AvitoGUIApp()
    app.run()


if __name__ == "__main__":
    run_app()
