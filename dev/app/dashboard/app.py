"""Main PyQt6 window for Resellix."""
from __future__ import annotations

import logging
import sys
import time
import webbrowser
from datetime import datetime
from typing import Optional

from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QKeySequence, QShortcut, QTextCharFormat
from PyQt6.QtWidgets import (
    QApplication,
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database as db
from categories import SNIPE_CATEGORIES
from listing_utils import size_option_label
from config import AppConfig, load_config, save_config
from subscription import activate_license, can_add_snipe_target, get_entitlements, require_feature
from notifier import TelegramNotifier
from sniper import MatchEvent, Sniper
from telegram_bot import ResellTelegramBot
from listing_utils import (
    SORT_LABELS,
    enrich_match_row,
    filter_rows_by_platform,
    filter_rows_by_size_keys,
    filter_rows_by_target,
    sort_rows,
)
from platforms import ALL_PLATFORMS, PLATFORM_LABELS, platform_label
from trends import TrendResult
from vinted import SnipeTarget, TargetStore, _parse_str_list, build_search_url

from .pickers import CategoryPickerWidget, PlatformPickerWidget, SizeFilterWidget
from .platform_filter import PlatformFilterBar
from .size_filter import SizeFilterBar
from .styles import STYLESHEET
from .ui_components import (
    GlassCard,
    GlassScroll,
    drop_shadow,
    form_label,
    page_header,
    section_title,
)
from .ui_effects import fade_in_widget, install_button_press_effect, switch_stack_page
from .widgets import DealCard, StatCard
from .workers import (
    CheapDealsThread,
    DashboardScanThread,
    SniperBridge,
    TelegramThread,
    TrendDrilldownThread,
    TrendScanThread,
)

CONTENT_MARGINS = (32, 28, 32, 28)
PAGE_SPACING = 18

log = logging.getLogger("dashboard.app")


PAGE_DASHBOARD = 0
PAGE_TARGETS = 1
PAGE_DEALS = 2
PAGE_TRENDS = 3
PAGE_SETTINGS = 4
PAGE_LOGS = 5


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Resellix")
        self.resize(1320, 820)
        self.setMinimumSize(1100, 700)

        self.cfg: AppConfig = load_config()
        self.targets = TargetStore()
        self.notifier = TelegramNotifier(self.cfg)
        self.sniper = Sniper(self.cfg, self.targets, self.notifier)
        self.bridge = SniperBridge(self.sniper)
        self.start_ts = time.time()

        self._tg_thread: Optional[TelegramThread] = None
        self._tg_bot: Optional[ResellTelegramBot] = None
        self._cheap_thread: Optional[CheapDealsThread] = None
        self._trend_thread: Optional[TrendScanThread] = None
        self._dash_scan_thread: Optional[DashboardScanThread] = None
        self._trend_drill_thread: Optional[TrendDrilldownThread] = None
        self._deals_cache: list[dict] = []
        self._trend_results: list[TrendResult] = []

        self._build_ui()
        self._wire_signals()
        self._apply_sidebar_update_notice()
        self._apply_entitlements_ui()
        self._refresh_status_strip()
        install_button_press_effect(self)
        fade_in_widget(self.centralWidget(), duration_ms=280)
        self._refresh_targets_table()
        self._rebuild_target_filter_combo()
        self._refresh_dashboard_feed()

        # Tick uptime label
        self._tick = QTimer(self)
        self._tick.setInterval(1000)
        self._tick.timeout.connect(self._refresh_status_strip)
        self._tick.start()

        # Auto-start sniper if cookie set
        if self.cfg.vinted_ready:
            self.sniper.start()

        # Auto-start telegram if configured
        if self.cfg.telegram_enabled:
            self._start_telegram()

    # ------------------------------------------------------------------
    # UI build
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("AppCanvas")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ---- sidebar
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(268)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        brand_block = QFrame()
        brand_block.setObjectName("BrandBlock")
        bb = QVBoxLayout(brand_block)
        bb.setContentsMargins(22, 26, 22, 20)
        bb.setSpacing(4)
        brand_title = QLabel("Resellix")
        brand_title.setObjectName("BrandTitle")
        brand_tag = QLabel("Vinted sniper")
        brand_tag.setObjectName("BrandTagline")
        self.sidebar_tier = QLabel()
        self.sidebar_tier.setObjectName("SidebarTier")
        self.sidebar_tier.setWordWrap(True)
        bb.addWidget(brand_title)
        bb.addWidget(brand_tag)
        bb.addWidget(self.sidebar_tier)
        sb.addWidget(brand_block)

        nav_wrap = QFrame()
        nav_wrap.setObjectName("SidebarNav")
        nav_lay = QVBoxLayout(nav_wrap)
        nav_lay.setContentsMargins(14, 16, 14, 12)
        nav_lay.setSpacing(2)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)

        def nav_btn(text: str, idx: int) -> QPushButton:
            btn = QPushButton(text)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _=False, i=idx: self._switch_page(i))
            nav_lay.addWidget(btn)
            self.nav_group.addButton(btn, idx)
            return btn

        self.nav_dashboard = nav_btn("Dashboard", PAGE_DASHBOARD)
        self.nav_targets = nav_btn("Snipe Targets", PAGE_TARGETS)
        self.nav_deals = nav_btn("Cheap Deals", PAGE_DEALS)
        self.nav_trends = nav_btn("Steal Niches", PAGE_TRENDS)
        self.nav_settings = nav_btn("Settings", PAGE_SETTINGS)
        self.nav_logs = nav_btn("Logs", PAGE_LOGS)
        sb.addWidget(nav_wrap, 1)

        footer = QFrame()
        footer.setObjectName("SidebarFooter")
        foot_lay = QVBoxLayout(footer)
        foot_lay.setContentsMargins(18, 14, 18, 18)
        foot_lay.setSpacing(6)

        self._sidebar_update_frame = QFrame()
        self._sidebar_update_frame.setObjectName("SidebarUpdateBanner")
        update_layout = QVBoxLayout(self._sidebar_update_frame)
        update_layout.setContentsMargins(12, 0, 12, 8)
        update_layout.setSpacing(4)
        update_title = QLabel("Update available")
        update_title.setObjectName("SidebarUpdateTitle")
        self._sidebar_update_text = QLabel("")
        self._sidebar_update_text.setObjectName("SidebarUpdateText")
        self._sidebar_update_text.setWordWrap(True)
        update_layout.addWidget(update_title)
        update_layout.addWidget(self._sidebar_update_text)
        self._sidebar_update_frame.hide()
        foot_lay.addWidget(self._sidebar_update_frame)

        attribution = QLabel(
            "Thomas Mikhline\n"
            "Private use only. Sharing may result in legal action."
        )
        attribution.setObjectName("SidebarAttribution")
        attribution.setWordWrap(True)
        foot_lay.addWidget(attribution)

        version = QLabel("Resellix v1.0")
        version.setObjectName("SidebarVersion")
        foot_lay.addWidget(version)
        sb.addWidget(footer)

        root.addWidget(sidebar)

        # ---- right side
        right = QVBoxLayout()
        right.setContentsMargins(0, 0, 0, 0)
        right.setSpacing(0)

        # status strip
        self.status_strip = self._build_status_strip()
        right.addWidget(self.status_strip)

        # pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_page_dashboard())
        self.stack.addWidget(self._build_page_targets())
        self.stack.addWidget(self._build_page_deals())
        self.stack.addWidget(self._build_page_trends())
        self.stack.addWidget(self._build_page_settings())
        self.stack.addWidget(self._build_page_logs())
        right.addWidget(self.stack, 1)

        wrap = QWidget()
        wrap.setLayout(right)
        root.addWidget(wrap, 1)

        # default page
        self.nav_dashboard.setChecked(True)
        self.stack.setCurrentIndex(PAGE_DASHBOARD)

    def _apply_entitlements_ui(self) -> None:
        ent = get_entitlements()
        if hasattr(self, "sidebar_tier"):
            self.sidebar_tier.setText(ent.sidebar_label)
        self.nav_deals.setVisible(ent.cheap_deals)
        self.nav_trends.setVisible(ent.trends)
        if hasattr(self, "set_sniper_platforms"):
            for code, cb in getattr(self.set_sniper_platforms, "_boxes", {}).items():
                allowed = code in ent.allowed_platforms
                cb.setEnabled(allowed)
                if not allowed:
                    cb.setChecked(False)
        if hasattr(self, "target_platform_picker"):
            for code, cb in getattr(self.target_platform_picker, "_boxes", {}).items():
                allowed = code in ent.allowed_platforms
                cb.setEnabled(allowed)
                if not allowed:
                    cb.setChecked(code == "vinted")
        if hasattr(self, "set_poll_min"):
            self.set_poll_min.setMinimum(ent.poll_min_floor)
            if self.set_poll_min.value() < ent.poll_min_floor:
                self.set_poll_min.setValue(ent.poll_min_floor)
        poll_hint = getattr(self, "_poll_hint_label", None)
        if poll_hint:
            if ent.instant_telegram:
                poll_hint.setText(
                    "Lower = faster alerts (~20–35s). Below ~15s risks Vinted rate limits."
                )
            else:
                poll_hint.setText(
                    f"Your plan uses slower alerts (min {ent.poll_min_floor}s). "
                    "Upgrade to Pro/Max for instant Telegram notifications."
                )
        if hasattr(self, "license_status_label"):
            self.license_status_label.setText(
                f"{ent.display_name}\n{ent.updates_status_line()}"
            )

    def _activate_license_key(self) -> None:
        code = self.license_key_input.text().strip()
        ok, msg = activate_license(code)
        if ok:
            self.license_key_input.clear()
            self.cfg = load_config()
            self._apply_entitlements_ui()
            QMessageBox.information(self, "License", msg)
        else:
            QMessageBox.warning(self, "License", msg)

    def _apply_sidebar_update_notice(self) -> None:
        try:
            from github_update import sidebar_update_notice

            notice = sidebar_update_notice()
        except Exception:
            notice = None
        frame = getattr(self, "_sidebar_update_frame", None)
        label = getattr(self, "_sidebar_update_text", None)
        if not frame or not label:
            return
        if notice:
            label.setText(notice)
            frame.show()
        else:
            frame.hide()

    # ----- status strip -----

    def _build_status_strip(self) -> QFrame:
        strip = QFrame()
        strip.setObjectName("StatusStrip")
        strip.setMinimumHeight(64)
        lay = QHBoxLayout(strip)
        lay.setContentsMargins(28, 12, 28, 12)
        lay.setSpacing(20)

        self.status_dot = QLabel("")
        self.status_dot.setObjectName("StatusDot")
        self.status_dot.setFixedSize(10, 10)
        self.status_text = QLabel("Idle")
        self.status_text.setObjectName("StatusText")
        status_grp = QHBoxLayout()
        status_grp.setSpacing(10)
        status_grp.addWidget(self.status_dot)
        status_grp.addWidget(self.status_text)
        lay.addLayout(status_grp)

        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet("color: rgba(15, 23, 42, 0.12); max-width: 1px;")
        lay.addWidget(sep1)

        self.status_uptime = QLabel("Uptime  00:00:00")
        self.status_checked = QLabel("Checked  0")
        self.status_matches = QLabel("Matches  0")
        for w in (self.status_uptime, self.status_checked, self.status_matches):
            w.setObjectName("ToolbarLabel")
            lay.addWidget(w)

        lay.addStretch(1)

        self.btn_start = QPushButton("Start sniper")
        self.btn_start.setObjectName("PrimaryButton")
        self.btn_pause = QPushButton("Pause")
        self.btn_pause.setObjectName("GhostButton")
        self.btn_pause.setEnabled(False)
        self.btn_start.clicked.connect(self._toggle_sniper)
        self.btn_pause.clicked.connect(self._toggle_pause)
        lay.addWidget(self.btn_start)
        lay.addWidget(self.btn_pause)

        drop_shadow(strip, blur=20, offset_y=4, alpha=35)
        return strip

    # ----- dashboard page -----

    def _build_page_dashboard(self) -> QWidget:
        page = QWidget()
        page.setObjectName("ContentPage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(*CONTENT_MARGINS)
        outer.setSpacing(PAGE_SPACING)

        outer.addWidget(
            page_header("Dashboard", "Live sniper stats and your latest matches.")
        )

        grid = QGridLayout()
        grid.setSpacing(18)
        for col in range(4):
            grid.setColumnStretch(col, 1)
        self.card_targets = StatCard("Active targets", "0")
        self.card_checked = StatCard("Listings checked", "0")
        self.card_matches = StatCard("Matches today", "0")
        self.card_state = StatCard("Sniper state", "stopped")
        grid.addWidget(self.card_targets, 0, 0)
        grid.addWidget(self.card_checked, 0, 1)
        grid.addWidget(self.card_matches, 0, 2)
        grid.addWidget(self.card_state, 0, 3)
        outer.addLayout(grid)

        filter_card = GlassCard()
        fc = QVBoxLayout(filter_card)
        fc.setContentsMargins(20, 18, 20, 18)
        fc.setSpacing(14)
        fc.addWidget(section_title("Recent matches"))

        row1 = QHBoxLayout()
        row1.setSpacing(12)
        self.dash_platform_filter = PlatformFilterBar()
        self.dash_platform_filter.selection_changed.connect(self._render_dashboard_feed)
        row1.addWidget(form_label("Source"))
        row1.addWidget(self.dash_platform_filter, 1)
        self.dash_target_filter = QComboBox()
        self.dash_target_filter.setMinimumWidth(180)
        self.dash_target_filter.addItem("All targets")
        self.dash_target_filter.currentTextChanged.connect(
            lambda _: self._render_dashboard_feed()
        )
        row1.addWidget(form_label("Target"))
        row1.addWidget(self.dash_target_filter)
        fc.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(12)
        self.dash_size_filter = SizeFilterBar()
        self.dash_size_filter.selection_changed.connect(self._render_dashboard_feed)
        row2.addWidget(form_label("Size"))
        row2.addWidget(self.dash_size_filter, 1)
        self.dash_sort = QComboBox()
        self.dash_sort.setMinimumWidth(160)
        for _key, label in SORT_LABELS:
            self.dash_sort.addItem(label, _key)
        self.dash_sort.currentIndexChanged.connect(lambda _: self._render_dashboard_feed())
        row2.addWidget(form_label("Sort"))
        row2.addWidget(self.dash_sort)
        btn_dash_refresh = QPushButton("Refresh")
        btn_dash_refresh.setObjectName("GhostButton")
        btn_dash_refresh.clicked.connect(self._refresh_dashboard_feed)
        btn_dash_scan = QPushButton("Scan now")
        btn_dash_scan.setObjectName("PrimaryButton")
        btn_dash_scan.clicked.connect(self._scan_all_targets)
        row2.addWidget(btn_dash_refresh)
        row2.addWidget(btn_dash_scan)
        fc.addLayout(row2)
        outer.addWidget(filter_card)

        hint = QLabel(
            "Filter by target and size. Est. resale = keyword + product type + Vinted median."
        )
        hint.setObjectName("HintLabel")
        hint.setWordWrap(True)
        outer.addWidget(hint)

        self.recent_scroll = QScrollArea()
        self.recent_scroll.setWidgetResizable(True)
        self.recent_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.recent_container = QWidget()
        self.recent_layout = QVBoxLayout(self.recent_container)
        self.recent_layout.setContentsMargins(0, 0, 0, 0)
        self.recent_layout.setSpacing(10)
        self.recent_layout.addStretch(1)
        self.recent_scroll.setWidget(self.recent_container)
        outer.addWidget(self.recent_scroll, 1)

        return page

    # ----- targets page -----

    def _build_page_targets(self) -> QWidget:
        page = QWidget()
        page.setObjectName("ContentPage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(*CONTENT_MARGINS)
        outer.setSpacing(PAGE_SPACING)

        outer.addWidget(
            page_header(
                "Snipe Targets",
                "Scroll the form for all options. Your active targets stay visible below.",
            )
        )

        form_scroll = GlassScroll()
        form_scroll.setMinimumHeight(280)
        form_scroll.setMaximumHeight(420)
        form_host = QWidget()
        form_outer = QVBoxLayout(form_host)
        form_outer.setContentsMargins(2, 2, 10, 2)
        form_outer.setSpacing(0)

        add_card = GlassCard()
        addl = QVBoxLayout(add_card)
        addl.setContentsMargins(26, 24, 26, 24)
        addl.setSpacing(22)

        basics = QGridLayout()
        basics.setHorizontalSpacing(16)
        basics.setVerticalSpacing(10)
        basics.addWidget(form_label("Keyword"), 0, 0, 1, 2)
        self.in_keyword = QLineEdit()
        self.in_keyword.setPlaceholderText("e.g. ralph lauren pullover")
        self.in_keyword.setMinimumHeight(42)
        basics.addWidget(self.in_keyword, 1, 0, 1, 2)
        addl.addLayout(basics)

        addl.addWidget(section_title("Price and profit"))
        price_row = QGridLayout()
        price_row.setHorizontalSpacing(14)
        price_row.setVerticalSpacing(10)
        for col, (label, attr) in enumerate(
            [
                ("Min price (€)", "in_min_price"),
                ("Max price (€)", "in_max_price"),
                ("Expected sell (€)", "in_expected"),
                ("Min profit (€)", "in_min_profit"),
            ]
        ):
            price_row.addWidget(form_label(label), 0, col)
            spin = QDoubleSpinBox()
            spin.setRange(0, 9999)
            spin.setDecimals(2)
            spin.setSingleStep(1)
            spin.setMinimumHeight(42)
            spin.setMinimumWidth(130)
            if attr == "in_min_price":
                spin.setSpecialValueText("—")
                self.in_min_price = spin
            elif attr == "in_max_price":
                spin.setValue(20)
                self.in_max_price = spin
            elif attr == "in_expected":
                self.in_expected = spin
            else:
                self.in_min_profit = spin
            price_row.addWidget(spin, 1, col)
        addl.addLayout(price_row)

        addl.addWidget(section_title("Text filters"))
        text_row = QGridLayout()
        text_row.setHorizontalSpacing(16)
        text_row.addWidget(form_label("Colors"), 0, 0)
        self.in_colors = QLineEdit()
        self.in_colors.setPlaceholderText("navy, black (optional)")
        self.in_colors.setMinimumHeight(42)
        text_row.addWidget(self.in_colors, 1, 0)
        text_row.addWidget(form_label("Exclude words"), 0, 1)
        self.in_exclude = QLineEdit()
        self.in_exclude.setPlaceholderText("baby, enfant, damaged")
        self.in_exclude.setMinimumHeight(42)
        text_row.addWidget(self.in_exclude, 1, 1)
        addl.addLayout(text_row)

        addl.addWidget(section_title("Platforms"))
        self.target_platform_picker = PlatformPickerWidget()
        addl.addWidget(self.target_platform_picker)

        addl.addWidget(section_title("Clothing type"))
        self.target_category_picker = CategoryPickerWidget()
        addl.addWidget(self.target_category_picker)

        addl.addWidget(section_title("Sizes"))
        self.target_size_filter = SizeFilterWidget()
        addl.addWidget(self.target_size_filter)

        target_help = QLabel(
            "Tip: Vinted for clothes, eBay and Kleinanzeigen for tech and local deals."
        )
        target_help.setObjectName("HintLabel")
        target_help.setWordWrap(True)
        addl.addWidget(target_help)

        btn_add = QPushButton("Add snipe target")
        btn_add.setObjectName("PrimaryButton")
        btn_add.setMinimumHeight(48)
        btn_add.clicked.connect(self._add_target)
        addl.addWidget(btn_add)

        form_outer.addWidget(add_card)
        form_scroll.setWidget(form_host)
        outer.addWidget(form_scroll)

        table_card = GlassCard()
        table_lay = QVBoxLayout(table_card)
        table_lay.setContentsMargins(16, 14, 16, 16)
        table_lay.setSpacing(10)
        table_lay.addWidget(section_title("Active targets"))

        self.targets_table = QTableWidget(0, 7)
        self.targets_table.setHorizontalHeaderLabels(
            ["", "Keyword", "Min €", "Max €", "Expect €", "Min profit €", "Actions"]
        )
        self.targets_table.verticalHeader().setVisible(False)
        self.targets_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.targets_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.targets_table.setMinimumHeight(200)
        h = self.targets_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in (2, 3, 4, 5):
            h.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
            self.targets_table.setColumnWidth(col, 100)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.targets_table.verticalHeader().setDefaultSectionSize(52)
        self.targets_table.setAlternatingRowColors(True)
        table_lay.addWidget(self.targets_table, 1)
        outer.addWidget(table_card, 1)

        return page

    # ----- cheap deals page -----

    def _build_page_deals(self) -> QWidget:
        page = QWidget()
        page.setObjectName("ContentPage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(*CONTENT_MARGINS)
        outer.setSpacing(PAGE_SPACING)

        head = QHBoxLayout()
        title = QLabel("Cheap Deals")
        title.setObjectName("SectionTitle")
        head.addWidget(title)
        head.addStretch(1)
        self.btn_scan_deals = QPushButton("Scan now")
        self.btn_scan_deals.setObjectName("PrimaryButton")
        self.btn_scan_deals.clicked.connect(self._scan_cheap_deals)
        self.btn_clear_deals = QPushButton("Clear")
        self.btn_clear_deals.setObjectName("GhostButton")
        self.btn_clear_deals.clicked.connect(self._clear_deals)
        self.deals_sort = QComboBox()
        for _key, label in SORT_LABELS:
            self.deals_sort.addItem(label, _key)
        self.deals_size_filter = SizeFilterBar()
        self.deals_size_filter.selection_changed.connect(self._render_deals_feed)
        lbl_dsz = QLabel("Size")
        lbl_dsz.setObjectName("ToolbarLabel")
        head.addWidget(lbl_dsz)
        head.addWidget(self.deals_size_filter)

        lbl_dsort = QLabel("Sort")
        lbl_dsort.setObjectName("ToolbarLabel")
        head.addWidget(lbl_dsort)
        head.addWidget(self.deals_sort)
        head.addWidget(self.btn_scan_deals)
        head.addWidget(self.btn_clear_deals)
        outer.addLayout(head)

        info = QLabel(
            "Real underpriced steals only (≥38% below value). Use Size to narrow to your fit."
        )
        info.setObjectName("HintLabel")
        info.setWordWrap(True)
        outer.addWidget(info)

        self.deals_progress = QLabel("")
        self.deals_progress.setObjectName("ProgressLabel")
        outer.addWidget(self.deals_progress)

        self.deals_scroll = QScrollArea()
        self.deals_scroll.setWidgetResizable(True)
        self.deals_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.deals_container = QWidget()
        self.deals_layout = QVBoxLayout(self.deals_container)
        self.deals_layout.setContentsMargins(0, 0, 0, 0)
        self.deals_layout.setSpacing(10)
        self.deals_layout.addStretch(1)
        self.deals_scroll.setWidget(self.deals_container)
        outer.addWidget(self.deals_scroll, 1)

        self.deals_sort.currentIndexChanged.connect(lambda _: self._render_deals_feed())
        idx_best = self.deals_sort.findData("deal_best")
        if idx_best >= 0:
            self.deals_sort.blockSignals(True)
            self.deals_sort.setCurrentIndex(idx_best)
            self.deals_sort.blockSignals(False)

        return page

    # ----- trends page -----

    def _build_page_trends(self) -> QWidget:
        page = QWidget()
        page.setObjectName("ContentPage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(*CONTENT_MARGINS)
        outer.setSpacing(PAGE_SPACING)

        head = QHBoxLayout()
        title = QLabel("Steal niches")
        title.setObjectName("SectionTitle")
        head.addWidget(title)
        head.addStretch(1)
        self.btn_scan_trends = QPushButton("Scan trends")
        self.btn_scan_trends.setObjectName("PrimaryButton")
        self.btn_scan_trends.clicked.connect(self._scan_trends)
        head.addWidget(self.btn_scan_trends)
        outer.addLayout(head)

        self.trends_progress = QLabel("")
        self.trends_progress.setObjectName("ProgressLabel")
        outer.addWidget(self.trends_progress)

        split = QSplitter(Qt.Orientation.Horizontal)
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 8, 0)
        left_lay.addWidget(QLabel("Underpriced niches on Vinted (click a row)"))
        self.trends_table = QTableWidget(0, 4)
        self.trends_table.setHorizontalHeaderLabels(
            ["#", "Product niche", "Steals", "Median €"]
        )
        self.trends_table.verticalHeader().setVisible(False)
        self.trends_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.trends_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.trends_table.cellClicked.connect(self._on_trend_row_clicked)
        h = self.trends_table.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        left_lay.addWidget(self.trends_table)
        split.addWidget(left)

        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(8, 0, 0, 0)
        self.trend_drill_title = QLabel("Resell picks for trend")
        self.trend_drill_title.setObjectName("SectionTitle")
        right_lay.addWidget(self.trend_drill_title)
        self.trend_drill_progress = QLabel("")
        self.trend_drill_progress.setObjectName("ProgressLabel")
        right_lay.addWidget(self.trend_drill_progress)
        self.trend_drill_scroll = QScrollArea()
        self.trend_drill_scroll.setWidgetResizable(True)
        self.trend_drill_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.trend_drill_container = QWidget()
        self.trend_drill_layout = QVBoxLayout(self.trend_drill_container)
        self.trend_drill_layout.setContentsMargins(0, 0, 0, 0)
        self.trend_drill_layout.setSpacing(10)
        self.trend_drill_layout.addStretch(1)
        self.trend_drill_scroll.setWidget(self.trend_drill_container)
        right_lay.addWidget(self.trend_drill_scroll, 1)
        split.addWidget(right)
        split.setSizes([380, 520])
        outer.addWidget(split, 1)

        return page

    # ----- settings page -----

    def _build_page_settings(self) -> QWidget:
        page = QWidget()
        page.setObjectName("ContentPage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(*CONTENT_MARGINS)
        outer.setSpacing(PAGE_SPACING)

        outer.addWidget(page_header("Settings", "License, Vinted, platforms, and Telegram."))

        scroll = GlassScroll()
        scroll_host = QWidget()
        scroll_lay = QVBoxLayout(scroll_host)
        scroll_lay.setContentsMargins(2, 2, 10, 2)
        scroll_lay.setSpacing(16)

        lic_card = GlassCard()
        lic_lay = QVBoxLayout(lic_card)
        lic_lay.setContentsMargins(20, 16, 20, 16)
        lic_lay.setSpacing(8)
        lic_lay.addWidget(section_title("Subscription and license"))
        self.license_status_label = QLabel()
        self.license_status_label.setWordWrap(True)
        self.license_status_label.setObjectName("HintLabel")
        lic_lay.addWidget(self.license_status_label)
        lic_row = QHBoxLayout()
        self.license_key_input = QLineEdit()
        self.license_key_input.setPlaceholderText("Paste license key (RX-PLUS-…, RX-PRO-…, RX-MAX-…)")
        btn_lic = QPushButton("Activate")
        btn_lic.setObjectName("PrimaryButton")
        btn_lic.clicked.connect(self._activate_license_key)
        lic_row.addWidget(self.license_key_input, 1)
        lic_row.addWidget(btn_lic)
        lic_lay.addLayout(lic_row)
        plans = QLabel(
            "Paste the license key you received from Thomas. "
            "Plans: Plus, Pro, Max, and optional Updates extension."
        )
        plans.setWordWrap(True)
        plans.setObjectName("HintLabel")
        lic_lay.addWidget(plans)
        scroll_lay.addWidget(lic_card)

        form = GlassCard()
        fl = QGridLayout(form)
        fl.setContentsMargins(26, 24, 26, 24)
        fl.setHorizontalSpacing(18)
        fl.setVerticalSpacing(14)

        row = 0
        api_hint = QLabel(
            "Uses pyVinted (github.com/herissondev/vinted-api-wrapper): "
            "auto session via HEAD request — optional _vinted_de_session override."
        )
        api_hint.setWordWrap(True)
        api_hint.setObjectName("HintLabel")
        fl.addWidget(api_hint, row, 0, 1, 4)
        row += 1

        fl.addWidget(form_label("Session cookie (optional)"), row, 0)
        self.set_cookie = QLineEdit()
        self.set_cookie.setEchoMode(QLineEdit.EchoMode.Password)
        self.set_cookie.setPlaceholderText("_vinted_de_session value — only if auto-fetch fails")
        self.set_cookie.setText(self.cfg.vinted_session_cookie)
        fl.addWidget(self.set_cookie, row, 1, 1, 3)
        row += 1

        self.set_show_cookie = QCheckBox("show secrets")
        self.set_show_cookie.toggled.connect(self._toggle_secret_fields)
        fl.addWidget(self.set_show_cookie, row, 1)
        row += 1

        fl.addWidget(form_label("Vinted host"), row, 0)
        self.set_host = QComboBox()
        self.set_host.setEditable(True)
        self.set_host.addItems([
            "www.vinted.de",
            "www.vinted.com",
            "www.vinted.fr",
            "www.vinted.it",
            "www.vinted.es",
            "www.vinted.nl",
            "www.vinted.pl",
        ])
        self.set_host.setCurrentText(self.cfg.vinted_host)
        fl.addWidget(self.set_host, row, 1)

        fl.addWidget(form_label("Locale"), row, 2)
        self.set_locale = QLineEdit(self.cfg.vinted_locale)
        fl.addWidget(self.set_locale, row, 3)
        row += 1

        fl.addWidget(form_label("Poll interval (seconds) min / max"), row, 0)
        self.set_poll_min = QSpinBox()
        self.set_poll_min.setRange(8, 3600)
        self.set_poll_min.setValue(self.cfg.poll_min_seconds)
        self.set_poll_max = QSpinBox()
        self.set_poll_max.setRange(10, 7200)
        self.set_poll_max.setValue(self.cfg.poll_max_seconds)
        fl.addWidget(self.set_poll_min, row, 1)
        fl.addWidget(self.set_poll_max, row, 2)
        poll_hint = QLabel("Lower = faster alerts (~20–35s). Below ~15s risks Vinted rate limits.")
        poll_hint.setObjectName("HintLabel")
        poll_hint.setWordWrap(True)
        self._poll_hint_label = poll_hint
        fl.addWidget(poll_hint, row, 3)
        row += 1

        fl.addWidget(section_title("Sniper platforms (global)"), row, 0, 1, 4)
        row += 1

        self.set_sniper_platforms = PlatformPickerWidget()
        self.set_sniper_platforms.set_platforms(self.cfg.sniper_platforms)
        fl.addWidget(self.set_sniper_platforms, row, 0, 1, 4)
        row += 1

        fl.addWidget(form_label("Kleinanzeigen API URL"), row, 0)
        self.set_klein_api = QLineEdit(self.cfg.kleinanzeigen_api_url)
        self.set_klein_api.setPlaceholderText("http://127.0.0.1:8000")
        fl.addWidget(self.set_klein_api, row, 1, 1, 3)
        row += 1

        ka_hint = QLabel(
            "Kleinanzeigen API starts automatically with start.bat (first run may take 1–2 min)."
        )
        ka_hint.setObjectName("HintLabel")
        ka_hint.setWordWrap(True)
        fl.addWidget(ka_hint, row, 0, 1, 4)
        row += 1

        fl.addWidget(form_label("eBay host"), row, 0)
        self.set_ebay_host = QLineEdit(self.cfg.ebay_host)
        fl.addWidget(self.set_ebay_host, row, 1)
        row += 1

        fl.addWidget(section_title("Telegram"), row, 0, 1, 4)
        row += 1

        fl.addWidget(form_label("Bot token"), row, 0)
        self.set_tg_token = QLineEdit(self.cfg.telegram_bot_token)
        self.set_tg_token.setEchoMode(QLineEdit.EchoMode.Password)
        fl.addWidget(self.set_tg_token, row, 1, 1, 3)
        row += 1

        fl.addWidget(form_label("Chat ID"), row, 0)
        self.set_tg_chat = QLineEdit(self.cfg.telegram_chat_id)
        fl.addWidget(self.set_tg_chat, row, 1)

        fl.addWidget(form_label("SerpAPI key (optional)"), row, 2)
        self.set_serp = QLineEdit(self.cfg.serpapi_key)
        self.set_serp.setEchoMode(QLineEdit.EchoMode.Password)
        fl.addWidget(self.set_serp, row, 3)
        row += 1

        scroll_lay.addWidget(form)

        help_lbl = QLabel(
            "Backend: bundled dev/app/vendor/pyVinted. "
            "If search fails, paste _vinted_de_session from browser cookies."
        )
        help_lbl.setWordWrap(True)
        help_lbl.setObjectName("HintLabel")
        scroll_lay.addWidget(help_lbl)

        scroll.setWidget(scroll_host)
        outer.addWidget(scroll, 1)

        btns = QHBoxLayout()
        btns.setSpacing(12)
        btn_diag = QPushButton("Diagnose access")
        btn_diag.setObjectName("GhostButton")
        btn_diag.clicked.connect(self._diagnose_vinted)
        btn_test = QPushButton("Test search")
        btn_test.setObjectName("GhostButton")
        btn_test.clicked.connect(self._test_vinted)
        btn_test_tg = QPushButton("Test Telegram")
        btn_test_tg.setObjectName("GhostButton")
        btn_test_tg.clicked.connect(self._test_telegram)
        btn_save = QPushButton("Save settings")
        btn_save.setObjectName("PrimaryButton")
        btn_save.clicked.connect(self._save_settings)
        btns.addWidget(btn_diag)
        btns.addWidget(btn_test)
        btns.addWidget(btn_test_tg)
        btns.addStretch(1)
        btns.addWidget(btn_save)
        outer.addLayout(btns)

        return page

    # ----- logs page -----

    def _build_page_logs(self) -> QWidget:
        page = QWidget()
        page.setObjectName("ContentPage")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(*CONTENT_MARGINS)
        outer.setSpacing(PAGE_SPACING)

        head = QHBoxLayout()
        title = QLabel("Logs")
        title.setObjectName("SectionTitle")
        head.addWidget(title)
        head.addStretch(1)
        clear = QPushButton("Clear")
        clear.setObjectName("GhostButton")
        clear.clicked.connect(lambda: self.log_view.clear())
        head.addWidget(clear)
        outer.addLayout(head)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        outer.addWidget(self.log_view, 1)

        return page

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------

    def _wire_signals(self) -> None:
        self.bridge.log_message.connect(self._on_log)
        self.bridge.match_found.connect(self._on_match)
        self.bridge.status_update.connect(self._on_status)

    # ------------------------------------------------------------------
    # Page switching
    # ------------------------------------------------------------------

    def _switch_page(self, idx: int) -> None:
        switch_stack_page(self.stack, idx)

    # ------------------------------------------------------------------
    # Status strip / dashboard refresh
    # ------------------------------------------------------------------

    def _refresh_status_strip(self) -> None:
        up = int(time.time() - self.start_ts)
        h, rem = divmod(up, 3600)
        m, s = divmod(rem, 60)
        self.status_uptime.setText(f"Uptime  {h:02d}:{m:02d}:{s:02d}")
        self.status_checked.setText(f"Checked  {db.get_stat('listings_checked')}")
        self.status_matches.setText(f"Matches  {db.get_stat('matches_sent')}")

        # Dashboard cards
        self.card_targets.set_value(str(len([t for t in self.targets.list() if t.enabled])))
        self.card_checked.set_value(str(db.get_stat("listings_checked")))
        self.card_matches.set_value(str(db.get_stat("matches_sent")))

        if not self.sniper.running:
            self.status_dot.setObjectName("StatusDotError")
            self.status_text.setText("Sniper stopped")
            self.card_state.set_value("Stopped")
        elif self.sniper.paused:
            self.status_dot.setObjectName("StatusDotPaused")
            self.status_text.setText("Paused")
            self.card_state.set_value("Paused")
        else:
            self.status_dot.setObjectName("StatusDot")
            self.status_text.setText("Scanning")
            self.card_state.set_value("Running")
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)
        # Re-apply stylesheet to reflect object name change
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)

        running = self.sniper.running
        self.btn_start.setText("Stop sniper" if running else "Start sniper")
        self.btn_start.setObjectName("StopButton" if running else "PrimaryButton")
        self.btn_start.style().unpolish(self.btn_start)
        self.btn_start.style().polish(self.btn_start)
        self.btn_pause.setEnabled(running)
        self.btn_pause.setText("Resume" if self.sniper.paused else "Pause")

    # ------------------------------------------------------------------
    # Sniper controls
    # ------------------------------------------------------------------

    def _toggle_sniper(self) -> None:
        if self.sniper.running:
            self.sniper.stop()
            self._append_log("Sniper stop requested.")
        else:
            if not self._sniper_can_start():
                QMessageBox.warning(
                    self,
                    "Cannot start sniper",
                    "Enable at least one platform in Settings and configure Vinted cookies "
                    "and/or Kleinanzeigen API URL.",
                )
                return
            self.sniper.start()
            self._append_log("Sniper started.")
        self._refresh_status_strip()

    def _toggle_pause(self) -> None:
        self.sniper.pause(not self.sniper.paused)
        self._refresh_status_strip()

    # ------------------------------------------------------------------
    # Targets
    # ------------------------------------------------------------------

    def _add_target(self) -> None:
        keyword = self.in_keyword.text().strip()
        if not keyword:
            QMessageBox.information(self, "Add target", "Enter a keyword first.")
            return
        ok, msg = can_add_snipe_target(len(self.targets.list()))
        if not ok:
            QMessageBox.warning(self, "Snipe limit", msg)
            return
        size_mode = self.target_size_filter.size_mode()
        size_keys = sorted(self.target_size_filter.selected_keys())
        if size_mode in ("include", "exclude") and not size_keys:
            QMessageBox.information(
                self,
                "Add target",
                "Select at least one size, or switch size mode to “All sizes”.",
            )
            return
        min_p = self.in_min_price.value() or None
        max_p = self.in_max_price.value() or None
        if min_p and max_p and min_p > max_p:
            QMessageBox.warning(
                self,
                "Add target",
                "Min price cannot be higher than max price.",
            )
            return
        target = SnipeTarget(
            keyword=keyword,
            min_price=min_p,
            max_price=max_p,
            expected_price=self.in_expected.value() or None,
            min_profit=self.in_min_profit.value() or None,
            sizes=size_keys,
            size_mode=size_mode,
            colors=_parse_str_list(self.in_colors.text()),
            categories=self.target_category_picker.selected_categories(),
            exclude_words=_parse_str_list(self.in_exclude.text()),
            platforms=self.target_platform_picker.selected_platforms(),
        )
        self.targets.add(target)
        self.in_keyword.clear()
        self.in_colors.clear()
        self.in_exclude.clear()
        self.target_size_filter.reset()
        self.target_category_picker.reset_to_all()
        self.target_platform_picker.reset_all()
        self._refresh_targets_table()
        self._rebuild_target_filter_combo()
        self._append_log(f"Added target: {target.label}")

    def _refresh_targets_table(self) -> None:
        targets = self.targets.list()
        self.targets_table.setRowCount(len(targets))
        for i, t in enumerate(targets):
            chk = QCheckBox()
            chk.setChecked(t.enabled)
            chk.toggled.connect(lambda checked, idx=i: self._set_target_enabled(idx, checked))
            self.targets_table.setCellWidget(i, 0, chk)
            kw_item = QTableWidgetItem(t.keyword)
            tips: list[str] = []
            cats = getattr(t, "categories", None) or []
            if cats and "all" not in cats:
                labels = {k: v for k, v in SNIPE_CATEGORIES}
                tips.append(f"Types: {', '.join(labels.get(c, c) for c in cats)}")
            mode = getattr(t, "size_mode", "any") or "any"
            if t.sizes and mode == "exclude":
                lbl = ", ".join(size_option_label(s) for s in t.sizes)
                tips.append(f"Exclude sizes: {lbl}")
            elif t.sizes and mode == "include":
                lbl = ", ".join(size_option_label(s) for s in t.sizes)
                tips.append(f"Only sizes: {lbl}")
            elif mode == "any":
                tips.append("Sizes: all")
            if t.colors:
                tips.append(f"Colors: {', '.join(t.colors)}")
            if t.exclude_words:
                tips.append(f"Exclude: {', '.join(t.exclude_words)}")
            plats = getattr(t, "platforms", None) or []
            if plats and set(plats) != set(ALL_PLATFORMS):
                tips.append(
                    "Platforms: " + ", ".join(platform_label(p) for p in plats)
                )
            if tips:
                kw_item.setToolTip("\n".join(tips))
            self.targets_table.setItem(i, 1, kw_item)
            self.targets_table.setItem(
                i, 2,
                QTableWidgetItem("" if t.min_price is None else f"{t.min_price:.2f}"),
            )
            self.targets_table.setItem(
                i, 3,
                QTableWidgetItem("" if t.max_price is None else f"{t.max_price:.2f}"),
            )
            self.targets_table.setItem(
                i, 4,
                QTableWidgetItem("" if t.expected_price is None else f"{t.expected_price:.2f}"),
            )
            self.targets_table.setItem(
                i, 5,
                QTableWidgetItem("" if t.min_profit is None else f"{t.min_profit:.2f}"),
            )

            actions = QWidget()
            al = QHBoxLayout(actions)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(6)
            btn_open = QPushButton("↗")
            btn_open.setToolTip("Open on Vinted")
            btn_open.setObjectName("GhostButton")
            btn_open.setFixedWidth(36)
            btn_open.clicked.connect(
                lambda _=False, kw=t.keyword, mp=t.max_price:
                webbrowser.open(build_search_url(self.cfg.vinted_host, kw, mp))
            )
            btn_del = QPushButton("✕")
            btn_del.setToolTip("Remove")
            btn_del.setObjectName("DangerButton")
            btn_del.setFixedWidth(36)
            btn_del.clicked.connect(lambda _=False, idx=i: self._remove_target(idx))
            al.addWidget(btn_open)
            al.addWidget(btn_del)
            al.addStretch(1)
            self.targets_table.setCellWidget(i, 6, actions)
        self._rebuild_target_filter_combo()

    def _set_target_enabled(self, idx: int, enabled: bool) -> None:
        targets = self.targets.list()
        if not (0 <= idx < len(targets)):
            return
        t = targets[idx]
        if t.enabled == enabled:
            return
        self.targets.toggle(idx)

    def _remove_target(self, idx: int) -> None:
        removed = self.targets.remove(idx)
        if removed:
            n = db.delete_matches_for_target(removed.keyword)
            self._append_log(
                f"Removed target: {removed.keyword}"
                + (f" ({n} matches cleared)" if n else "")
            )
        self._refresh_targets_table()
        self._refresh_dashboard_feed()

    # ------------------------------------------------------------------
    # Recent matches feed
    # ------------------------------------------------------------------

    def _targets_by_kw(self) -> dict[str, SnipeTarget]:
        return {t.keyword: t for t in self.targets.list()}

    def _rebuild_target_filter_combo(self) -> None:
        combo = self.dash_target_filter
        prev = combo.currentText()
        combo.blockSignals(True)
        combo.clear()
        combo.addItem("All targets")
        for t in self.targets.list():
            combo.addItem(t.keyword)
        idx = combo.findText(prev)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    @staticmethod
    def _cancel_widget_photo(w: QWidget | None) -> None:
        if w is None:
            return
        loader = getattr(w, "_loader", None)
        if loader is not None and hasattr(loader, "cancel"):
            loader.cancel()

    def _clear_recent_layout(self) -> None:
        while self.recent_layout.count() > 1:
            item = self.recent_layout.takeAt(0)
            w = item.widget()
            self._cancel_widget_photo(w)
            if w is not None:
                w.deleteLater()

    def _refresh_dashboard_feed(self) -> None:
        self._render_dashboard_feed()

    def _render_dashboard_feed(self) -> None:
        if not hasattr(self, "recent_layout"):
            return
        self._clear_recent_layout()
        targets_map = self._targets_by_kw()
        active = set(targets_map.keys())
        rows = [
            r for r in db.recent_matches(150)
            if (r.get("target_label") or "") in active
        ]
        rows = [enrich_match_row(r, targets_map) for r in rows]
        self.dash_size_filter.set_rows(rows)
        label = self.dash_target_filter.currentText()
        rows = filter_rows_by_target(rows, label)
        rows = filter_rows_by_platform(rows, self.dash_platform_filter.selected_platforms())
        rows = filter_rows_by_size_keys(rows, self.dash_size_filter.selected_keys())
        mode = self.dash_sort.currentData() or "newest"
        if isinstance(mode, str):
            rows = sort_rows(rows, mode)
        for row in rows[:50]:
            self._insert_match_card(row)

    def _insert_match_card(self, row: dict) -> None:
        title = row.get("title") or "Untitled"
        price = float(row.get("price") or 0.0)
        currency = row.get("currency") or "EUR"
        size = row.get("size") or "—"
        brand = row.get("brand") or "—"
        status = row.get("status") or "—"
        plat = platform_label(row.get("platform") or "vinted")
        meta = f"{plat}  •  {brand}  •  size {size}  •  {status}  •  {row.get('target_label')}"
        parts: list[str] = []
        est = float(row.get("estimated_resale") or 0.0)
        profit = float(row.get("profit") or 0.0)
        confident = row.get("profit_confident")
        if est > 0:
            parts.append(f"Est. resale ~{est:.0f}€")
        if confident and profit > 0:
            parts.append(f"+{profit:.0f}€ est. profit")
        savings = "  •  ".join(parts)
        card = DealCard(
            title=title,
            price_str=f"{price:.2f} {currency}",
            meta=meta,
            url=row.get("url") or "",
            photo_url=row.get("photo_url") or "",
            savings_str=savings,
        )
        self.recent_layout.insertWidget(self.recent_layout.count() - 1, card)

    def _scan_all_targets(self) -> None:
        if not self.cfg.vinted_ready:
            QMessageBox.warning(
                self,
                "Missing Vinted auth",
                "Settings → Test search, or paste your Vinted session cookie.",
            )
            return
        enabled = [t for t in self.targets.list() if t.enabled]
        if not enabled:
            QMessageBox.information(self, "Scan", "Add and enable at least one snipe target.")
            return
        if self._dash_scan_thread and self._dash_scan_thread.isRunning():
            return
        self._append_log("Manual target scan started…")
        t = DashboardScanThread(self.cfg, enabled, self)
        t.progress.connect(lambda m: self._append_log(m))
        t.finished_ok.connect(self._on_dash_scan_done)
        t.failed.connect(lambda m: QMessageBox.warning(self, "Scan failed", m))
        self._dash_scan_thread = t
        t.start()

    def _on_dash_scan_done(self, count: int) -> None:
        self._append_log(f"Target scan finished ({count} listings fetched). Refreshing feed…")
        self._refresh_dashboard_feed()

    # ------------------------------------------------------------------
    # Live sniper callbacks (from bridge)
    # ------------------------------------------------------------------

    def _on_log(self, msg: str) -> None:
        self._append_log(msg)

    def _on_match(self, event: MatchEvent) -> None:
        self._refresh_dashboard_feed()

    def _on_status(self, payload: dict) -> None:
        action = payload.get("action") or "running"
        nxt = payload.get("next_in")
        if nxt is not None:
            self.status_text.setText(f"{action}  (next in {nxt}s)")
        else:
            self.status_text.setText(str(action))

    def _append_log(self, msg: str) -> None:
        if not hasattr(self, "log_view"):
            return
        ts = datetime.now().strftime("%H:%M:%S")
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)

        fmt_ts = QTextCharFormat()
        fmt_ts.setForeground(QColor("#64748b"))
        cursor.insertText(f"[{ts}] ", fmt_ts)

        if "MATCH" in msg.upper():
            fmt_match = QTextCharFormat()
            fmt_match.setForeground(QColor("#22d3ee"))
            fmt_match.setFontWeight(700)
            parts = msg.split("[", 1)
            if len(parts) == 2:
                cursor.insertText(parts[0], fmt_ts)
                fmt_brand = QTextCharFormat()
                fmt_brand.setForeground(QColor("#a5b4fc"))
                cursor.insertText("[" + parts[1], fmt_brand)
            else:
                cursor.insertText(msg, fmt_match)
        elif "error" in msg.lower() or "fail" in msg.lower():
            fmt_err = QTextCharFormat()
            fmt_err.setForeground(QColor("#fb7185"))
            cursor.insertText(msg, fmt_err)
        elif "Telegram" in msg or "Sniper" in msg:
            fmt_sys = QTextCharFormat()
            fmt_sys.setForeground(QColor("#c4b5fd"))
            cursor.insertText(msg, fmt_sys)
        else:
            fmt_def = QTextCharFormat()
            fmt_def.setForeground(QColor("#e2e8f0"))
            cursor.insertText(msg, fmt_def)

        cursor.insertText("\n")
        self.log_view.setTextCursor(cursor)
        self.log_view.ensureCursorVisible()

    # ------------------------------------------------------------------
    # Cheap deals
    # ------------------------------------------------------------------

    def _clear_deals(self) -> None:
        self._deals_cache.clear()
        while self.deals_layout.count() > 1:
            item = self.deals_layout.takeAt(0)
            w = item.widget()
            self._cancel_widget_photo(w)
            if w is not None:
                w.deleteLater()

    def _clear_layout_widgets(self, layout: QVBoxLayout) -> None:
        while layout.count() > 1:
            item = layout.takeAt(0)
            w = item.widget()
            self._cancel_widget_photo(w)
            if w is not None:
                w.deleteLater()

    def _deal_row_from_listing(
        self, listing, expected: float, score: float, keyword: str = ""
    ) -> dict:
        return {
            "title": listing.title or "Untitled",
            "price": float(listing.price or 0),
            "currency": listing.currency or "EUR",
            "brand": listing.brand or "—",
            "size": listing.size or "—",
            "status": listing.status or "—",
            "url": listing.url or "",
            "photo_url": listing.photo_url or "",
            "created_ts": int(getattr(listing, "created_ts", 0) or time.time()),
            "expected": expected,
            "score": score,
            "keyword": keyword,
        }

    def _render_deals_feed(self) -> None:
        if not hasattr(self, "deals_layout"):
            return
        self._clear_layout_widgets(self.deals_layout)
        mode = self.deals_sort.currentData() or "newest"
        if not isinstance(mode, str):
            mode = "newest"
        rows = list(self._deals_cache)
        self.deals_size_filter.set_rows(rows)
        rows = filter_rows_by_size_keys(rows, self.deals_size_filter.selected_keys())
        rows = sort_rows(rows, mode)
        load_photo = DealCard.load_photos
        for row in rows[:80]:
            expected = float(row.get("expected") or 0)
            price = float(row.get("price") or 0)
            score = float(row.get("score") or 0)
            savings = expected - price
            kw = row.get("keyword") or ""
            meta = (
                f"{row.get('brand')}  •  size {row.get('size')}  •  {row.get('status')}"
                + (f"  •  {kw}" if kw else "")
            )
            savings_str = (
                f"Est. resale ~{expected:.0f}€  •  save ~{savings:.0f}€ ({int(score * 100)}% under)"
                if expected > 0
                else ""
            )
            card = DealCard(
                title=row.get("title") or "Untitled",
                price_str=f"{price:.2f} {row.get('currency') or 'EUR'}",
                meta=meta,
                url=row.get("url") or "",
                photo_url=row.get("photo_url") or "",
                savings_str=savings_str,
                load_photo=load_photo,
            )
            self.deals_layout.insertWidget(self.deals_layout.count() - 1, card)

    def _scan_cheap_deals(self) -> None:
        ok, msg = require_feature("cheap_deals")
        if not ok:
            QMessageBox.information(self, "Resellix Pro", msg)
            return
        if not self.cfg.vinted_ready:
            QMessageBox.warning(
                self,
                "Missing Vinted auth",
                "Settings → set Vinted host, then Test search.",
            )
            return
        if self._cheap_thread and self._cheap_thread.isRunning():
            return
        self._deals_cache.clear()
        self._clear_deals()
        self.btn_scan_deals.setEnabled(False)
        self.deals_progress.setText("Scanning…")

        t = CheapDealsThread(self.cfg, self)
        t.progress.connect(self.deals_progress.setText)
        t.deals_ready.connect(self._on_cheap_deals_batch)
        t.finished_ok.connect(self._on_cheap_done)
        t.failed.connect(self._on_cheap_failed)
        t.finished.connect(lambda: self.btn_scan_deals.setEnabled(True))
        self._cheap_thread = t
        t.start()

    def _on_cheap_deals_batch(self, collected: list) -> None:
        self._deals_cache = [
            self._deal_row_from_listing(lst, exp, sc, kw)
            for lst, exp, sc, kw in collected
        ]
        self._render_deals_feed()

    def _on_cheap_done(self, count: int) -> None:
        self.deals_progress.setText(f"Done — {count} underpriced listing(s).")

    def _on_cheap_failed(self, msg: str) -> None:
        self.deals_progress.setText(f"Failed: {msg}")

    # ------------------------------------------------------------------
    # Trends
    # ------------------------------------------------------------------

    def _scan_trends(self) -> None:
        ok, msg = require_feature("trends")
        if not ok:
            QMessageBox.information(self, "Resellix Pro", msg)
            return
        if self._trend_thread and self._trend_thread.isRunning():
            return
        self.btn_scan_trends.setEnabled(False)
        self.trends_progress.setText("Scanning Vinted for underpriced niches…")
        self.trends_table.setRowCount(0)

        t = TrendScanThread(self.cfg, self)
        t.progress.connect(self.trends_progress.setText)
        t.finished_ok.connect(self._on_trends_ok)
        t.failed.connect(self._on_trends_failed)
        t.finished.connect(lambda: self.btn_scan_trends.setEnabled(True))
        self._trend_thread = t
        t.start()

    def _on_trends_ok(self, results: list) -> None:
        self._trend_results = list(results)
        self.trends_progress.setText(
            f"Found {len(results)} niches with steals — click to browse listings."
        )
        self.trends_table.setRowCount(len(results))
        for i, r in enumerate(results):
            self.trends_table.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self.trends_table.setItem(i, 1, QTableWidgetItem(r.name))
            self.trends_table.setItem(i, 2, QTableWidgetItem(str(r.score)))
            med = getattr(r, "median_eur", 0) or 0
            self.trends_table.setItem(i, 3, QTableWidgetItem(f"{med:.0f}" if med else "—"))
            tip = getattr(r, "sample_snippet", "") or ""
            if tip:
                for col in range(4):
                    it = self.trends_table.item(i, col)
                    if it:
                        it.setToolTip(tip)
        if results:
            self._drill_trend(results[0].name)

    def _on_trends_failed(self, msg: str) -> None:
        self.trends_progress.setText(f"Failed: {msg}")

    def _on_trend_row_clicked(self, row: int, _col: int) -> None:
        item = self.trends_table.item(row, 1)
        if item:
            self._drill_trend(item.text())

    def _clear_trend_drill_layout(self) -> None:
        self._clear_layout_widgets(self.trend_drill_layout)

    def _drill_trend(self, name: str) -> None:
        if not name.strip():
            return
        if not self.cfg.vinted_ready:
            self.trend_drill_progress.setText("Set Vinted auth in Settings first.")
            return
        if self._trend_drill_thread and self._trend_drill_thread.isRunning():
            return
        self.trend_drill_title.setText(f"Resell picks: {name}")
        self.trend_drill_progress.setText("Searching Vinted…")
        self._clear_trend_drill_layout()
        t = TrendDrilldownThread(self.cfg, name, self)
        t.progress.connect(self.trend_drill_progress.setText)
        t.deals_ready.connect(self._on_trend_drill_batch)
        t.finished_ok.connect(self._on_trend_drill_done)
        t.failed.connect(self._on_trend_drill_failed)
        self._trend_drill_thread = t
        t.start()

    def _on_trend_drill_batch(self, collected: list) -> None:
        self._clear_trend_drill_layout()
        load_photo = DealCard.load_photos
        for listing, expected, score, keyword in collected[:40]:
            row = self._deal_row_from_listing(listing, expected, score, keyword)
            price = float(row.get("price") or 0)
            savings = float(expected) - price
            sc = float(score)
            card = DealCard(
                title=row.get("title") or "Untitled",
                price_str=f"{price:.2f} {row.get('currency') or 'EUR'}",
                meta=f"{row.get('brand')}  •  size {row.get('size')}  •  {row.get('status')}",
                url=row.get("url") or "",
                photo_url=row.get("photo_url") or "",
                savings_str=(
                    f"Est. resale ~{expected:.0f}€  •  save ~{savings:.0f}€ ({int(sc * 100)}% under)"
                    if expected > 0
                    else ""
                ),
                load_photo=load_photo,
            )
            self.trend_drill_layout.insertWidget(self.trend_drill_layout.count() - 1, card)

    def _on_trend_drill_done(self, count: int) -> None:
        self.trend_drill_progress.setText(f"Done — {count} underpriced listing(s).")

    def _on_trend_drill_failed(self, msg: str) -> None:
        self.trend_drill_progress.setText(f"Failed: {msg}")

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _cfg_from_form(self) -> "AppConfig":
        tmp = load_config()
        tmp.vinted_session_cookie = self.set_cookie.text().strip()
        tmp.vinted_host = self.set_host.currentText().strip() or tmp.vinted_host
        tmp.vinted_locale = self.set_locale.text().strip() or tmp.vinted_locale
        return tmp

    def _toggle_secret_fields(self, on: bool) -> None:
        mode = QLineEdit.EchoMode.Normal if on else QLineEdit.EchoMode.Password
        self.set_cookie.setEchoMode(mode)
        self.set_tg_token.setEchoMode(mode)
        self.set_serp.setEchoMode(mode)

    def _sniper_can_start(self) -> bool:
        from platforms import PLATFORM_EBAY, PLATFORM_KLEINANZEIGEN, PLATFORM_VINTED

        enabled = set(self.cfg.sniper_platforms or ALL_PLATFORMS)
        if PLATFORM_VINTED in enabled and self.cfg.vinted_ready:
            return True
        if PLATFORM_KLEINANZEIGEN in enabled and self.cfg.kleinanzeigen_api_url:
            return True
        if PLATFORM_EBAY in enabled:
            return True
        return False

    def _save_settings(self) -> None:
        from subscription import clamp_poll_intervals, filter_platforms

        plat = filter_platforms(self.set_sniper_platforms.selected_platforms())
        poll_min, poll_max = clamp_poll_intervals(
            self.set_poll_min.value(), self.set_poll_max.value()
        )
        plat_csv = ",".join(plat) if plat else "vinted"
        updates = {
            "VINTED_SESSION_COOKIE": self.set_cookie.text().strip(),
            "VINTED_HOST": self.set_host.currentText().strip(),
            "VINTED_LOCALE": self.set_locale.text().strip(),
            "POLL_MIN_SECONDS": str(poll_min),
            "POLL_MAX_SECONDS": str(poll_max),
            "KLEINANZEIGEN_API_URL": self.set_klein_api.text().strip(),
            "EBAY_HOST": self.set_ebay_host.text().strip(),
            "SNIPER_PLATFORMS": plat_csv,
            "TELEGRAM_BOT_TOKEN": self.set_tg_token.text().strip(),
            "TELEGRAM_CHAT_ID": self.set_tg_chat.text().strip(),
            "SERPAPI_KEY": self.set_serp.text().strip(),
        }
        save_config(updates)
        self.cfg = load_config()
        self.sniper.refresh_config(self.cfg)
        self.notifier.refresh(self.cfg)
        self._apply_entitlements_ui()
        self._append_log("Settings saved.")
        QMessageBox.information(self, "Saved", "Settings written to .env.")

        # auto-start telegram if it became available
        if self.cfg.telegram_enabled and (
            self._tg_thread is None or not self._tg_thread.isRunning()
        ):
            self._start_telegram()

    def _diagnose_vinted(self) -> None:
        from PyQt6.QtWidgets import QDialog, QDialogButtonBox

        tmp = self._cfg_from_form()
        dlg = QDialog(self)
        dlg.setWindowTitle("Vinted access diagnosis")
        dlg.resize(620, 480)
        lay = QVBoxLayout(dlg)
        box = QPlainTextEdit()
        box.setReadOnly(True)
        box.setPlainText("Running checks (10–30 s)…")
        lay.addWidget(box)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(dlg.reject)
        lay.addWidget(buttons)

        class DiagnoseThread(QThread):
            finished_text = pyqtSignal(str)

            def __init__(self, cfg, parent=None):
                super().__init__(parent)
                self._cfg = cfg

            def run(self) -> None:
                try:
                    from vinted import VintedClient
                    lines = VintedClient(self._cfg).run_diagnose()
                    self.finished_text.emit("\n".join(lines))
                except Exception as exc:
                    self.finished_text.emit(f"Diagnosis failed: {exc}")

        th = DiagnoseThread(tmp, dlg)
        th.finished_text.connect(box.setPlainText)
        th.start()
        dlg.exec()

    def _test_vinted(self) -> None:
        from vinted import VintedAuthError, VintedClient, VintedError

        tmp = self._cfg_from_form()
        client = VintedClient(tmp)
        try:
            listings = client.search("nike", max_price=200, per_page=5)
            QMessageBox.information(
                self,
                "Test OK",
                f"Backend: pyVinted\nFetched {len(listings)} listings.\n\n"
                + "\n".join(f"• {l.title[:60]}  -  {l.price} {l.currency}" for l in listings[:5]),
            )
        except VintedAuthError as exc:
            QMessageBox.critical(
                self,
                "Auth error",
                f"{exc}\n\nTry: Diagnose access, or paste _vinted_de_session from Chrome.",
            )
        except VintedError as exc:
            QMessageBox.critical(self, "Vinted error", str(exc))
        except Exception as exc:
            QMessageBox.critical(self, "Error", str(exc))

    def _test_telegram(self) -> None:
        import asyncio
        token = self.set_tg_token.text().strip()
        chat = self.set_tg_chat.text().strip()
        if not (token and chat):
            QMessageBox.warning(self, "Telegram", "Set both bot token and chat id first.")
            return
        try:
            from telegram import Bot
            async def _send():
                bot = Bot(token=token)
                await bot.send_message(chat_id=chat, text="✅ Resellix — test message")
            asyncio.run(_send())
            QMessageBox.information(self, "Telegram", "Test message sent.")
        except Exception as exc:
            QMessageBox.critical(self, "Telegram", f"Failed: {exc}")

    # ------------------------------------------------------------------
    # Telegram thread
    # ------------------------------------------------------------------

    def _start_telegram(self) -> None:
        if self._tg_thread and self._tg_thread.isRunning():
            return
        if not self.cfg.telegram_enabled:
            return
        try:
            self._tg_bot = ResellTelegramBot(
                self.cfg, self.targets, self.start_ts, sniper=self.sniper
            )
            self._tg_thread = TelegramThread(self._tg_bot, self)
            self._tg_thread.failed.connect(
                lambda msg: self._append_log(f"Telegram bot error: {msg}")
            )
            self._tg_thread.start()
            self._append_log("Telegram bot starting...")
        except Exception as exc:
            self._append_log(f"Could not start Telegram bot: {exc}")

    # ------------------------------------------------------------------
    # Shutdown
    # ------------------------------------------------------------------

    def closeEvent(self, event) -> None:
        self.sniper.stop()
        super().closeEvent(event)


# ---------------------------------------------------------------------------


def _prepare_qt_paths() -> None:
    """Windows: ensure Qt platform plugins (qwindows.dll) are found."""
    import os
    from pathlib import Path

    try:
        import PyQt6
    except ImportError:
        return
    qt6 = Path(PyQt6.__file__).resolve().parent / "Qt6"
    plugins = qt6 / "plugins"
    if plugins.is_dir():
        os.environ.setdefault("QT_PLUGIN_PATH", str(plugins))
    bin_dir = qt6 / "bin"
    if bin_dir.is_dir():
        os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ.get("PATH", "")


def run_dashboard() -> int:
    _prepare_qt_paths()
    try:
        app = QApplication(sys.argv)
    except Exception as exc:
        raise RuntimeError(
            f"PyQt6 konnte nicht starten ({exc}). "
            "Fuehre repair.bat aus (fehlende Qt-Plugins)."
        ) from exc
    app.setApplicationName("Resellix")
    app.setStyleSheet(STYLESHEET)
    w = MainWindow()
    w.show()
    return app.exec()
