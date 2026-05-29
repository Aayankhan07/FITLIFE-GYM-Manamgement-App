"""FitLife — Members screen package init"""
from .members_screen import MembersScreen
from .member_form import MemberForm
from .member_profile import MemberProfile


class MembersModule(MembersScreen.__bases__[0]):
    """
    Container widget that manages the Members sub-navigation:
    List → Add/Edit Form → Profile View (using QStackedWidget internally).
    """
    from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
    from PyQt6.QtCore import pyqtSignal

    def __init__(self, session, parent=None):
        from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget
        QWidget.__init__(self, parent)
        self._session = session
        self.setStyleSheet("background:transparent;")

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("background:transparent;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._stack)

        # Create screens
        self._list_screen = MembersScreen(session)
        self._list_screen.open_add_form.connect(self._show_add_form)
        self._list_screen.open_edit_form.connect(self._show_edit_form)
        self._list_screen.open_profile.connect(self._show_profile)
        self._stack.addWidget(self._list_screen)

        self._stack.setCurrentWidget(self._list_screen)

    def _show_add_form(self):
        form = MemberForm(self._session)
        form.saved.connect(self._back_to_list)
        form.cancelled.connect(self._back_to_list)
        self._stack.addWidget(form)
        self._stack.setCurrentWidget(form)

    def _show_edit_form(self, member_id: int):
        form = MemberForm(self._session, member_id=member_id)
        form.saved.connect(self._back_to_list)
        form.cancelled.connect(self._back_to_list)
        self._stack.addWidget(form)
        self._stack.setCurrentWidget(form)

    def _show_profile(self, member_id: int):
        profile = MemberProfile(self._session, member_id)
        profile.go_back.connect(self._back_to_list)
        profile.go_edit.connect(self._show_edit_form)
        self._stack.addWidget(profile)
        self._stack.setCurrentWidget(profile)

    def _back_to_list(self):
        # Remove extra widgets (keep only list screen)
        while self._stack.count() > 1:
            w = self._stack.widget(1)
            self._stack.removeWidget(w)
            w.deleteLater()
        self._stack.setCurrentWidget(self._list_screen)
        self._list_screen.refresh()

    def refresh(self):
        if hasattr(self._stack.currentWidget(), "refresh"):
            self._stack.currentWidget().refresh()
