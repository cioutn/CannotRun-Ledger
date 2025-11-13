"""
添加/编辑交易对话框 - Fluent Design风格

使用qfluentwidgets组件实现现代化对话框
"""

from datetime import datetime
from PyQt5.QtWidgets import QVBoxLayout, QLabel, QWidget
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from qfluentwidgets import (
    MessageBoxBase, SubtitleLabel, LineEdit, ComboBox, DateEdit,
    DoubleSpinBox, TextEdit, InfoBar, InfoBarPosition
)
from ledger.models.transaction import Transaction
from ledger.ui.theme import Theme


class AddTransactionDialog(MessageBoxBase):
    """添加/编辑交易对话框"""

    transaction_saved = pyqtSignal(Transaction)

    def __init__(self, parent=None, transaction=None):
        super().__init__(parent)
        self.transaction = transaction
        self.init_ui()
        if transaction:
            self.load_transaction()

    def init_ui(self):
        """初始化UI"""
        # 标题
        title_text = "" if self.transaction else ""
        self.titleLabel = SubtitleLabel(title_text, self)
        self.titleLabel.setFont(Theme.font(Theme.FONT_TITLE, True))
        
        # 主体内容：增大边距，避免内容贴边
        self.viewLayout.setSpacing(Theme.SPACING_MEDIUM)
        self.viewLayout.setContentsMargins(
            Theme.SPACING_LARGE,  # left
            Theme.SPACING_MEDIUM, # top
            Theme.SPACING_LARGE,  # right
            Theme.SPACING_LARGE,  # bottom
        )
        # 若上层容器存在布局，也增加整体留白
        if self.widget and self.widget.layout():
            self.widget.layout().setContentsMargins(
                Theme.SPACING_MEDIUM,
                Theme.SPACING_MEDIUM,
                Theme.SPACING_MEDIUM,
                Theme.SPACING_MEDIUM,
            )
        
        # 交易类型
        type_widget = self.create_form_row("交易类型")
        self.type_combo = ComboBox()
        self.type_combo.addItems(['支出', '收入'])
        self.type_combo.setFont(Theme.font(Theme.FONT_BODY))
        self.type_combo.setFixedHeight(42)
        type_widget.layout().addWidget(self.type_combo)
        self.viewLayout.addWidget(type_widget)
        
        # 金额
        amount_widget = self.create_form_row("金额 (¥)")
        self.amount_spinbox = DoubleSpinBox()
        self.amount_spinbox.setRange(0, 9999999.99)
        self.amount_spinbox.setDecimals(2)
        self.amount_spinbox.setFont(Theme.font(Theme.FONT_BODY))
        self.amount_spinbox.setFixedHeight(42)
        amount_widget.layout().addWidget(self.amount_spinbox)
        self.viewLayout.addWidget(amount_widget)
        
        # 日期
        date_widget = self.create_form_row("日期")
        self.date_edit = DateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setFont(Theme.font(Theme.FONT_BODY))
        self.date_edit.setFixedHeight(42)
        date_widget.layout().addWidget(self.date_edit)
        self.viewLayout.addWidget(date_widget)
        
        # 描述
        desc_label = QLabel("描述")
        desc_label.setFont(Theme.font(Theme.FONT_BODY, True))
        desc_label.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_SECONDARY)};")
        self.viewLayout.addWidget(desc_label)
        
        self.description_edit = TextEdit()
        self.description_edit.setPlaceholderText("简要描述此笔交易...")
        self.description_edit.setFont(Theme.font(Theme.FONT_BODY))
        self.description_edit.setFixedHeight(120)
        self.viewLayout.addWidget(self.description_edit)
        
        # 标签
        tag_widget = self.create_form_row("标签")
        self.tag_edit = LineEdit()
        self.tag_edit.setPlaceholderText("用逗号分隔多个标签")
        self.tag_edit.setFont(Theme.font(Theme.FONT_BODY))
        self.tag_edit.setFixedHeight(42)
        tag_widget.layout().addWidget(self.tag_edit)
        self.viewLayout.addWidget(tag_widget)
        
        # 按钮
        self.yesButton.setText("保存")
        self.yesButton.setFont(Theme.font(Theme.FONT_BODY, True))
        self.yesButton.setFixedHeight(42)
        self.cancelButton.setText("取消")
        self.cancelButton.setFont(Theme.font(Theme.FONT_BODY))
        self.cancelButton.setFixedHeight(42)
        
        # 绑定事件
        self.yesButton.clicked.connect(self.save_transaction)

        # 对话框尺寸
        self.widget.setMinimumWidth(640)
    
    def create_form_row(self, label_text: str) -> QWidget:
        """创建表单行"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(Theme.SPACING_XSMALL)
        
        label = QLabel(label_text)
        label.setFont(Theme.font(Theme.FONT_BODY, True))
        label.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_SECONDARY)};")
        layout.addWidget(label)
        
        return widget

    def load_transaction(self):
        """加载交易信息到表单"""
        self.type_combo.setCurrentText('收入' if self.transaction.transaction_type == 'INCOME' else '支出')
        self.amount_spinbox.setValue(self.transaction.amount)
        self.date_edit.setDate(QDate(self.transaction.date.year, 
                                      self.transaction.date.month, 
                                      self.transaction.date.day))
        self.description_edit.setPlainText(self.transaction.description)
        self.tag_edit.setText(', '.join(self.transaction.tags))

    def save_transaction(self):
        """保存交易"""
        # 验证
        if not self.amount_spinbox.value():
            InfoBar.warning(
                title="警告",
                content="金额不能为空",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        if not self.description_edit.toPlainText().strip():
            InfoBar.warning(
                title="警告",
                content="描述不能为空",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 构建数据
        transaction_type = 'INCOME' if self.type_combo.currentText() == '收入' else 'EXPENSE'
        date = datetime.combine(self.date_edit.date().toPyDate(), datetime.min.time())
        tags = [tag.strip() for tag in self.tag_edit.text().split(',') if tag.strip()]

        if self.transaction:
            # 编辑模式
            self.transaction.transaction_type = transaction_type
            self.transaction.amount = self.amount_spinbox.value()
            self.transaction.date = date
            self.widget.setMinimumWidth(640)
            self.transaction.tags = tags
        else:
            # 新建模式
            self.transaction = Transaction(
                amount=self.amount_spinbox.value(),
                transaction_type=transaction_type,
                description=self.description_edit.toPlainText(),
                date=date,
                tags=tags
            )

        self.transaction_saved.emit(self.transaction)
        self.accept()
