"""FitLife — Diary Module (rebuilt two-column splitter layout)"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QComboBox, QLineEdit, QTextEdit,
    QStackedWidget, QDateEdit, QCheckBox, QGridLayout,
    QSplitter, QApplication
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QTimer
from PyQt6.QtGui import QColor

from ui.components.glass_card import SectionHeader
from ui.components.confirm_dialog import ConfirmDialog, InfoDialog
from ui.components.loading_spinner import LoadingOverlay
from utils.thread_worker import Worker
from database.connection import DatabaseConnection
from config.constants import DIARY_TAGS
import logging

logger = logging.getLogger(__name__)

# ── Diary DB helpers (unchanged logic) ────────────────────────────────────────
def _diary_fetch(user_id, search=None, tag=None, pinned_only=False):
    try:
        sql = """
            SELECT id, title, body, entry_date, tags, is_pinned, created_at
            FROM   diary_entries
            WHERE  user_id=? AND is_deleted=0
        """
        params = [user_id]
        if search:
            sql += " AND (title LIKE ? OR body LIKE ?)"; s = f"%{search}%"; params += [s, s]
        if tag:
            sql += " AND tags LIKE ?"; params.append(f"%{tag}%")
        if pinned_only:
            sql += " AND is_pinned=1"
        sql += " ORDER BY is_pinned DESC, entry_date DESC"
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(sql, params); return cursor.fetchall()
    except Exception as e:
        logger.error(f"diary_fetch: {e}"); return []

def _diary_save(user_id, title, body, entry_date, tags, is_pinned, entry_id=None):
    try:
        with DatabaseConnection() as (conn, cursor):
            if entry_id:
                cursor.execute("""
                    UPDATE diary_entries SET title=?,body=?,entry_date=?,tags=?,is_pinned=?,updated_at=GETDATE()
                    WHERE id=? AND user_id=?
                """, (title, body, entry_date, tags, is_pinned, entry_id, user_id))
                return {"success": True, "message": "Entry updated."}
            else:
                cursor.execute("""
                    INSERT INTO diary_entries(user_id,title,body,entry_date,tags,is_pinned,is_deleted,created_at,updated_at)
                    VALUES(?,?,?,?,?,?,0,GETDATE(),GETDATE())
                """, (user_id, title, body, entry_date, tags, is_pinned))
                return {"success": True, "message": "Entry saved."}
    except Exception as e:
        logger.error(f"diary_save: {e}"); return {"success": False, "message": str(e)}

def _diary_delete(entry_id, user_id):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE diary_entries SET is_deleted=1, updated_at=GETDATE() "
                "WHERE id=? AND user_id=?",
                (entry_id, user_id)
            )
        return {"success": True, "message": "Entry deleted."}
    except Exception as e:
        return {"success": False, "message": str(e)}

def _diary_pin(entry_id, user_id):
    try:
        with DatabaseConnection() as (conn, cursor):
            cursor.execute(
                "UPDATE diary_entries SET is_pinned = ~is_pinned, "
                "updated_at=GETDATE() WHERE id=? AND user_id=?",
                (entry_id, user_id)
            )
        return {"success": True, "message": "Pin toggled."}
    except Exception as e:
        return {"success": False, "message": str(e)}


# ── Tag colors ────────────────────────────────────────────────────────────────
TAG_COLORS = {
    'Work':      ('#3B82F6', '#1E3A5F'),
    'Personal':  ('#7C3AED', '#2D1060'),
    'Reminder':  ('#FFB800', '#3D2800'),
    'Important': ('#FF2D78', '#4D0020'),
}

def _tag_style(tag):
    fg, bg = TAG_COLORS.get(tag, ('#7C3AED', '#2D1060'))
    return f"background:{bg};color:{fg};border:1px solid {fg};border-radius:6px;" \
           f"padding:2px 8px;font-size:10px;font-weight:bold;"


# ── Main Diary Module ─────────────────────────────────────────────────────────
class DiaryModule(QWidget):
    """Two-column diary: left=entry list, right=editor/viewer."""

    def __init__(self, session, parent=None):
        super().__init__(parent)
        self._session = session
        self._entries = []               # all fetched entries
        self._selected_id = None        # currently selected entry id
        self._is_dirty = False          # unsaved changes flag
        self.setStyleSheet("background:transparent;")
        self._build_ui()
        self._load_entries()

    # ── UI Construction ───────────────────────────────────────────────────────
    def _build_ui(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setStyleSheet("QSplitter::handle{background:rgba(124,58,237,0.2);width:1px;}")

        # ── LEFT PANEL: list ──────────────────────────────────────────────────
        left = QWidget()
        left.setFixedWidth(310)
        left.setStyleSheet(
            "QWidget{background:rgba(255,255,255,0.03);"
            "border-right:1px solid rgba(124,58,237,0.15);}"
        )
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(8)

        # New Entry button
        self._btn_new = QPushButton("✏️  New Entry")
        self._btn_new.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #7C3AED, stop:1 #5B21B6);
                color: #FFFFFF; border: none; border-radius: 10px;
                padding: 10px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #8B5CF6, stop:1 #7C3AED);
            }
        """)
        self._btn_new.clicked.connect(self._new_entry)
        left_layout.addWidget(self._btn_new)

        # Search
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍 Search entries...")
        self._search.setStyleSheet("""
            QLineEdit {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px; padding: 8px 12px;
                color: #F0F4FF; font-size: 13px;
            }
            QLineEdit:focus { border: 1px solid #7C3AED; }
        """)
        self._search.textChanged.connect(self._filter_entries)
        left_layout.addWidget(self._search)

        # Tag filter
        self._tag_filter = QComboBox()
        self._tag_filter.addItems(["All Tags"] + list(DIARY_TAGS))
        self._tag_filter.setStyleSheet("""
            QComboBox {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.1);
                border-radius: 8px; padding: 6px 12px;
                color: #F0F4FF; font-size: 13px;
            }
        """)
        self._tag_filter.currentTextChanged.connect(lambda _: self._filter_entries())
        left_layout.addWidget(self._tag_filter)

        # Entries scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:transparent;border:none;}")
        self._entries_container = QWidget()
        self._entries_container.setStyleSheet("background:transparent;")
        self._list_layout = QVBoxLayout(self._entries_container)
        self._list_layout.setContentsMargins(0, 0, 0, 0)
        self._list_layout.setSpacing(6)
        self._list_layout.addStretch()
        scroll.setWidget(self._entries_container)
        left_layout.addWidget(scroll, 1)

        # ── RIGHT PANEL: editor ───────────────────────────────────────────────
        right = QWidget()
        right.setStyleSheet("background:transparent;")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24, 20, 24, 20)
        right_layout.setSpacing(0)

        self._right_stack = QStackedWidget()
        self._right_stack.setStyleSheet("background:transparent;")

        # Page 0: empty state
        empty_page = QWidget(); empty_page.setStyleSheet("background:transparent;")
        ep_layout = QVBoxLayout(empty_page)
        ep_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ep_icon = QLabel("📓"); ep_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ep_icon.setStyleSheet("font-size:64px;background:transparent;")
        ep_text = QLabel("Select an entry to view\nor click New Entry to start writing")
        ep_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ep_text.setWordWrap(True)
        ep_text.setStyleSheet("color:rgba(255,255,255,0.35);font-size:14px;background:transparent;")
        ep_layout.addWidget(ep_icon)
        ep_layout.addSpacing(16)
        ep_layout.addWidget(ep_text)

        # Page 1: editor
        editor_page = QWidget(); editor_page.setStyleSheet("background:transparent;")
        ed_layout = QVBoxLayout(editor_page); ed_layout.setSpacing(12); ed_layout.setContentsMargins(0,0,0,0)

        # Title
        self._title_input = QLineEdit()
        self._title_input.setPlaceholderText("Entry title...")
        self._title_input.setStyleSheet("""
            QLineEdit {
                background: transparent; border: none;
                border-bottom: 2px solid rgba(124,58,237,0.4);
                color: #F0F4FF; font-size: 22px; font-weight: bold; padding: 8px 0;
            }
            QLineEdit:focus { border-bottom: 2px solid #7C3AED; }
        """)
        self._title_input.textChanged.connect(self._mark_dirty)
        ed_layout.addWidget(self._title_input)

        # Meta row: date, tag, pin, save status
        meta_row = QHBoxLayout(); meta_row.setSpacing(8)
        self._date_edit = QDateEdit()
        self._date_edit.setCalendarPopup(True)
        self._date_edit.setDate(QDate.currentDate())
        self._date_edit.setDisplayFormat("dd MMM yyyy")
        self._date_edit.setStyleSheet("""
            QDateEdit {
                background: rgba(255,255,255,0.08);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 8px; padding: 5px 10px;
                color: #F0F4FF; font-size: 13px;
            }
        """)
        self._date_edit.dateChanged.connect(lambda _: self._mark_dirty())

        self._tag_combo = QComboBox()
        self._tag_combo.addItem("— No Tag —", "")
        for tg in DIARY_TAGS:
            self._tag_combo.addItem(tg, tg)
        self._tag_combo.setStyleSheet("""
            QComboBox {
                background: rgba(124,58,237,0.2);
                border: 1px solid rgba(124,58,237,0.4);
                border-radius: 8px; padding: 5px 12px;
                color: #F0F4FF; font-size: 13px;
            }
        """)
        self._tag_combo.currentIndexChanged.connect(lambda _: self._mark_dirty())

        self._pin_btn = QPushButton("📌 Pin")
        self._pin_btn.setCheckable(True)
        self._pin_btn.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06);
                border: 1px solid rgba(255,255,255,0.12);
                border-radius: 8px; padding: 5px 12px;
                color: rgba(255,255,255,0.5); font-size: 13px;
            }
            QPushButton:checked {
                background: rgba(255,184,0,0.18);
                border: 1px solid #FFB800; color: #FFB800;
            }
        """)
        self._pin_btn.toggled.connect(lambda _: self._mark_dirty())

        self._save_status = QLabel("All saved ✓")
        self._save_status.setStyleSheet("color:rgba(255,255,255,0.35);font-size: 13px;")

        meta_row.addWidget(self._date_edit)
        meta_row.addWidget(self._tag_combo)
        meta_row.addWidget(self._pin_btn)
        meta_row.addStretch()
        meta_row.addWidget(self._save_status)
        ed_layout.addLayout(meta_row)

        # Body editor
        self._body_editor = QTextEdit()
        self._body_editor.setPlaceholderText("Write your thoughts, notes, reflections...")
        self._body_editor.setStyleSheet("""
            QTextEdit {
                background: rgba(255,255,255,0.04);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 12px; color: #E0E7FF;
                font-size: 14px; padding: 16px; line-height: 1.6;
            }
            QTextEdit:focus { border: 1px solid rgba(124,58,237,0.4); }
        """)
        self._body_editor.textChanged.connect(self._on_body_changed)
        ed_layout.addWidget(self._body_editor, 1)

        # Bottom row
        bottom_row = QHBoxLayout(); bottom_row.setSpacing(8)
        self._char_count = QLabel("0 characters")
        self._char_count.setStyleSheet("color:rgba(255,255,255,0.3);font-size: 13px;")

        self._btn_save = QPushButton("💾 Save Entry")
        self._btn_save.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #00E676, stop:1 #00B248);
                color: #001A0A; font-weight: bold; font-size: 13px;
                border: none; border-radius: 8px; padding: 8px 20px;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                            stop:0 #33FF99, stop:1 #00E676);
            }
        """)
        self._btn_save.clicked.connect(self._save_entry)

        self._btn_del = QPushButton("🗑 Delete")
        self._btn_del.setStyleSheet("""
            QPushButton {
                background: rgba(255,45,120,0.15);
                color: #FF2D78; border: 1px solid rgba(255,45,120,0.3);
                border-radius: 8px; padding: 8px 16px; font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,45,120,0.3); }
        """)
        self._btn_del.clicked.connect(self._delete_current)

        self._btn_cancel = QPushButton("❌ Cancel")
        self._btn_cancel.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.06);
                color: #F0F4FF; border: 1px solid rgba(255,255,255,0.12);
                border-radius: 8px; padding: 8px 16px; font-size: 13px;
            }
            QPushButton:hover { background: rgba(255,255,255,0.12); }
        """)
        self._btn_cancel.clicked.connect(self._close_editor)

        bottom_row.addWidget(self._char_count)
        bottom_row.addStretch()
        bottom_row.addWidget(self._btn_cancel)
        bottom_row.addWidget(self._btn_del)
        bottom_row.addWidget(self._btn_save)
        ed_layout.addLayout(bottom_row)

        self._right_stack.addWidget(empty_page)   # 0
        self._right_stack.addWidget(editor_page)  # 1

        right_layout.addWidget(self._right_stack)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter)

        self._overlay = LoadingOverlay(self)

        # Auto-save timer
        self._autosave = QTimer()
        self._autosave.setInterval(30000)
        self._autosave.timeout.connect(self._auto_save)

    # ── Entry List ────────────────────────────────────────────────────────────
    def _load_entries(self):
        self._overlay.show_loading("Loading diary...")
        uid = self._session.user_id
        self._worker = Worker(_diary_fetch, uid)
        self._worker.result.connect(self._on_entries_loaded)
        self._worker.error.connect(lambda e: self._overlay.hide_loading())
        self._worker.start()

    def _on_entries_loaded(self, entries):
        self._overlay.hide_loading()
        self._entries = entries
        self._filter_entries()

    def _filter_entries(self):
        search = self._search.text().strip().lower()
        tag_sel = self._tag_filter.currentText()
        tag_sel = None if tag_sel == "All Tags" else tag_sel

        filtered = []
        for e in self._entries:
            eid, title, body, edate, tags, pinned, created = e
            if search and search not in title.lower() and search not in body.lower():
                continue
            if tag_sel and (not tags or tag_sel not in tags):
                continue
            filtered.append(e)

        # Rebuild cards
        while self._list_layout.count() > 1:
            item = self._list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not filtered:
            lbl = QLabel("📭 No entries found")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color:rgba(255,255,255,0.3);font-size:13px;padding:20px;")
            self._list_layout.insertWidget(0, lbl)
            return

        for i, e in enumerate(filtered):
            card = self._make_entry_card(e)
            self._list_layout.insertWidget(i, card)

    def _make_entry_card(self, e):
        eid, title, body, edate, tags, pinned, created = e
        is_selected = (eid == self._selected_id)

        card = QFrame()
        card.setFixedHeight(88)
        card.setCursor(Qt.CursorShape.PointingHandCursor)
        if is_selected:
            card.setStyleSheet("""
                QFrame {
                    background: rgba(124,58,237,0.2);
                    border: 1px solid rgba(124,58,237,0.6);
                    border-radius: 10px;
                }
            """)
        else:
            card.setStyleSheet("""
                QFrame {
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.08);
                    border-radius: 10px;
                }
                QFrame:hover {
                    background: rgba(124,58,237,0.12);
                    border: 1px solid rgba(124,58,237,0.35);
                }
            """)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 8, 12, 8)
        lay.setSpacing(3)

        # Top: pin indicator + title + date
        top = QHBoxLayout(); top.setSpacing(4)
        if pinned:
            pin_lbl = QLabel("📌")
            pin_lbl.setStyleSheet("font-size: 13px;background:transparent;")
            top.addWidget(pin_lbl)

        title_lbl = QLabel((title[:28] + "…") if len(title) > 28 else title)
        title_lbl.setStyleSheet("color:#F0F4FF;font-weight:bold;font-size:13px;background:transparent;")
        top.addWidget(title_lbl, 1)

        date_lbl = QLabel(str(edate)[:10])
        date_lbl.setStyleSheet("color:rgba(255,255,255,0.35);font-size: 13px;background:transparent;")
        top.addWidget(date_lbl)
        lay.addLayout(top)

        # Preview
        preview = body[:55].replace('\n', ' ') if body else ""
        if len(body or "") > 55:
            preview += "…"
        prev_lbl = QLabel(preview)
        prev_lbl.setStyleSheet("color:rgba(255,255,255,0.45);font-size: 13px;background:transparent;")
        lay.addWidget(prev_lbl)

        # Tag chip
        if tags:
            tag = tags.split(",")[0].strip()
            bot = QHBoxLayout(); bot.setContentsMargins(0, 0, 0, 0)
            tag_lbl = QLabel(f" {tag} ")
            tag_lbl.setStyleSheet(_tag_style(tag))
            bot.addWidget(tag_lbl)
            bot.addStretch()
            lay.addLayout(bot)

        card.mousePressEvent = lambda ev, i=eid: self._select_entry(i)
        return card

    # ── Entry Editing ─────────────────────────────────────────────────────────
    def _select_entry(self, entry_id):
        self._selected_id = entry_id
        e = next((x for x in self._entries if x[0] == entry_id), None)
        if not e:
            return
        eid, title, body, edate, tags, pinned, created = e

        # Populate editor without triggering dirty
        self._title_input.blockSignals(True)
        self._body_editor.blockSignals(True)
        self._title_input.setText(title or "")
        self._body_editor.setPlainText(body or "")
        if edate:
            try:
                d = edate if hasattr(edate, 'year') else \
                    __import__('datetime').date.fromisoformat(str(edate)[:10])
                self._date_edit.setDate(QDate(d.year, d.month, d.day))
            except Exception:
                self._date_edit.setDate(QDate.currentDate())
        tag_val = tags.split(",")[0].strip() if tags else ""
        idx = self._tag_combo.findData(tag_val)
        self._tag_combo.setCurrentIndex(max(0, idx))
        self._pin_btn.setChecked(bool(pinned))
        self._title_input.blockSignals(False)
        self._body_editor.blockSignals(False)

        self._is_dirty = False
        self._save_status.setText("All saved ✓")
        self._char_count.setText(f"{len(body or '')} characters")
        self._right_stack.setCurrentIndex(1)
        self._autosave.start()

        # Refresh card selection highlights
        self._filter_entries()

    def _new_entry(self):
        self._selected_id = None
        self._title_input.clear()
        self._body_editor.clear()
        self._date_edit.setDate(QDate.currentDate())
        self._tag_combo.setCurrentIndex(0)
        self._pin_btn.setChecked(False)
        self._is_dirty = False
        self._save_status.setText("")
        self._char_count.setText("0 characters")
        self._right_stack.setCurrentIndex(1)
        self._title_input.setFocus()
        self._autosave.start()

    def _mark_dirty(self):
        if not self._is_dirty:
            self._is_dirty = True
            self._save_status.setText("Unsaved changes…")

    def _on_body_changed(self):
        text = self._body_editor.toPlainText()
        self._char_count.setText(f"{len(text)} characters")
        self._mark_dirty()

    def _auto_save(self):
        if self._is_dirty and self._selected_id:
            self._save_entry(silent=True)

    def _save_entry(self, silent=False):
        title = self._title_input.text().strip()
        body = self._body_editor.toPlainText().strip()
        if not title:
            if not silent:
                InfoDialog("Error", "Title is required.", "error", self).exec()
            return
        if not body:
            if not silent:
                InfoDialog("Error", "Content is required.", "error", self).exec()
            return

        tag = self._tag_combo.currentData() or ""
        pinned = 1 if self._pin_btn.isChecked() else 0
        date = self._date_edit.date().toPyDate()

        result = _diary_save(
            self._session.user_id, title, body, date, tag, pinned,
            self._selected_id
        )
        if result["success"]:
            self._is_dirty = False
            self._save_status.setText("All saved ✓")
            self._load_entries()
            if not silent:
                InfoDialog("Saved", result["message"], "success", self).exec()
                self._close_editor()
        else:
            if not silent:
                InfoDialog("Error", result["message"], "error", self).exec()

    def _close_editor(self):
        self._selected_id = None
        self._right_stack.setCurrentIndex(0)
        self._autosave.stop()
        self._filter_entries()

    def _select_latest(self):
        if self._entries:
            self._select_entry(self._entries[0][0])

    def _delete_current(self):
        if not self._selected_id:
            return
        title = self._title_input.text().strip() or "this entry"
        dlg = ConfirmDialog("Delete Entry", f"Delete '{title}'?",
                            "Delete", "danger", self)
        if dlg.exec():
            r = _diary_delete(self._selected_id, self._session.user_id)
            if r["success"]:
                self._selected_id = None
                self._right_stack.setCurrentIndex(0)
                self._load_entries()
            else:
                InfoDialog("Error", r["message"], "error", self).exec()

    def refresh(self):
        self._load_entries()
