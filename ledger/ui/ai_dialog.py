"""AI 自然语言录入对话框。"""

from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, TextEdit, PushButton,
    InfoBar, InfoBarPosition
)

from ledger.ui.theme import Theme
from ledger.services.transaction_service import TransactionService
from ledger.services.ai_service import AICommandService


class AICommandDialog(MessageBoxBase):
    """通过自然语言新增/修改/删除交易的对话框。"""

    executed = pyqtSignal(dict)  # 执行完成后发出结果统计

    def __init__(self, service: TransactionService, parent=None):
        super().__init__(parent)
        self.ts = service
        self.ai = AICommandService(self.ts)
        self._init_ui()

    def _init_ui(self):
        self.titleLabel = SubtitleLabel("AI 自然语言录入", self)
        self.titleLabel.setFont(Theme.font(Theme.FONT_TITLE, True))

        # 主体区
        self.viewLayout.setSpacing(Theme.SPACING_MEDIUM)
        self.viewLayout.setContentsMargins(
            Theme.SPACING_LARGE, Theme.SPACING_MEDIUM, Theme.SPACING_LARGE, Theme.SPACING_LARGE
        )

        self.inputEdit = TextEdit(self)
        self.inputEdit.setPlaceholderText(
            "例如：‘今天中午吃饭花了36.5元，标签餐饮；把昨天的星巴克支出改为45元；删除上周三的兼职收入’"
        )
        self.inputEdit.setFixedHeight(160)
        self.inputEdit.setFont(Theme.font(Theme.FONT_BODY))
        self.viewLayout.addWidget(self.inputEdit)

        # 底部按钮
        self.yesButton.setText("解析并执行")
        self.yesButton.setFont(Theme.font(Theme.FONT_BODY, True))
        self.yesButton.setFixedHeight(42)
        self.yesButton.clicked.connect(self.on_execute)

        self.cancelButton.setText("取消")
        self.cancelButton.setFont(Theme.font(Theme.FONT_BODY))
        self.cancelButton.setFixedHeight(42)

        # 仅解析的次按钮
        self.parseOnlyBtn = PushButton("仅解析")
        self.parseOnlyBtn.setFixedHeight(42)
        self.parseOnlyBtn.clicked.connect(self.on_parse_only)
        self.buttonLayout.insertWidget(0, self.parseOnlyBtn)

        self.widget.setMinimumWidth(720)

    def on_parse_only(self):
        text = self.inputEdit.toPlainText().strip()
        if not text:
            self._warn("请输入自然语言指令")
            return
        try:
            ops = self.ai.parse(text)
            count = len(ops)
            self._ok(f"解析完成，共 {count} 项操作（未执行）")
        except Exception as e:  # pylint: disable=broad-except
            self._err(str(e))

    def on_execute(self):
        text = self.inputEdit.toPlainText().strip()
        if not text:
            self._warn("请输入自然语言指令")
            return
        try:
            _ops, result = self.ai.parse_and_execute(text)
            added = len(result.get("added", []))
            updated = len(result.get("updated", []))
            deleted = len(result.get("deleted", []))
            self._ok(f"执行完成：新增 {added}，更新 {updated}，删除 {deleted}")
            # 通知外层刷新与展示
            self.executed.emit(result)
            self.accept()
        except Exception as e:  # pylint: disable=broad-except
            self._err(str(e))

    # ---------- InfoBar helpers ----------
    def _ok(self, msg: str):
        InfoBar.success(
            title="成功",
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2500,
            parent=self,
        )

    def _warn(self, msg: str):
        InfoBar.warning(
            title="提示",
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2500,
            parent=self,
        )

    def _err(self, msg: str):
        InfoBar.error(
            title="失败",
            content=msg,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self,
        )
