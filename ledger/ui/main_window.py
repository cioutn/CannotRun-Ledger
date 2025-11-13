"""
主应用窗口 - 现代化Fluent Design风格

使用qfluentwidgets组件库实现Material Design风格界面
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidgetItem, QHeaderView, QFrame
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition,
    PushButton, PrimaryPushButton, ToolButton,
    SearchLineEdit, ComboBox, DateEdit, TableWidget, CardWidget,
    InfoBar, InfoBarPosition, MessageBox, FluentIcon
)
from ledger.services.transaction_service import TransactionService
from ledger.models.transaction import Transaction
from ledger.ui.dialogs import AddTransactionDialog
from ledger.ui.ai_dialog import AICommandDialog
from ledger.ui.theme import Theme
from ledger.ui.analytics_view import AnalyticsInterface


class StatCard(CardWidget):
    """统计卡片组件"""
    
    def __init__(self, title: str, value: str, color: QColor, parent=None):
        super().__init__(parent)
        self.setFixedHeight(140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Theme.SPACING_LARGE, Theme.SPACING_LARGE, 
                                 Theme.SPACING_LARGE, Theme.SPACING_LARGE)
        layout.setSpacing(Theme.SPACING_SMALL)
        
        # 标题
        self.title_label = QLabel(title)
        self.title_label.setFont(Theme.font(Theme.FONT_BODY, False))
        self.title_label.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_SECONDARY)};")
        
        # 数值
        self.value_label = QLabel(value)
        self.value_label.setFont(Theme.font(Theme.FONT_XLARGE, True))
        self.value_label.setStyleSheet(f"color: {Theme.color_to_str(color)};")
        self.value_color = color  # 保存颜色供后续更新
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.value_label)
        layout.addStretch()
    
    def update_value(self, value: str, color: QColor = None):
        """更新数值"""
        self.value_label.setText(value)
        if color:
            self.value_label.setStyleSheet(f"color: {Theme.color_to_str(color)};")


class TransactionTableWidget(TableWidget):
    """交易记录表格组件"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
    
    def setup_table(self):
        """设置表格"""
        # 列设置
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels(['日期', '类型', '金额', '描述', '标签', '操作'])
        
        # 表头样式
        header = self.horizontalHeader()
        header.setFont(Theme.font(Theme.FONT_SUBTITLE, True))
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setMinimumHeight(60)
        
        # 列宽设置
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        # 操作列需要足够的宽度容纳“编辑/删除”两个中文按钮与图标
        self.setColumnWidth(5, 240)
        
        # 垂直表头
        v_header = self.verticalHeader()
        v_header.setDefaultSectionSize(80)
        v_header.setMinimumWidth(44)
        
        # 表格样式
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(TableWidget.SelectionBehavior.SelectRows)
        self.setSelectionMode(TableWidget.SelectionMode.SingleSelection)
        # 现代风格：去除密集网格线
        self.setShowGrid(False)


class DashboardInterface(QWidget):
    """仪表盘界面 - 主视图"""
    
    def __init__(self, service: TransactionService, parent=None):
        super().__init__(parent)
        self.service = service
        self.transactions = []
        self.init_ui()
        
    def init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(Theme.SPACING_LARGE, Theme.SPACING_LARGE,
                                 Theme.SPACING_LARGE, Theme.SPACING_LARGE)
        layout.setSpacing(Theme.SPACING_LARGE)
        
        # 标题区域
        title_layout = QHBoxLayout()
        title = QLabel("个人记账本")
        title.setFont(Theme.font(Theme.FONT_LARGE, True))
        title.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_PRIMARY)};")

        add_btn = PrimaryPushButton(FluentIcon.ADD, "添加交易")
        add_btn.setFont(Theme.font(Theme.FONT_BODY, True))
        add_btn.setFixedSize(140, 46)
        add_btn.clicked.connect(self.add_transaction)

        ai_btn = PrimaryPushButton(FluentIcon.SEND, "AI记账")
        ai_btn.setFont(Theme.font(Theme.FONT_BODY, True))
        ai_btn.setFixedSize(160, 46)
        ai_btn.clicked.connect(self.open_ai_dialog)

        title_layout.addWidget(title)
        title_layout.addStretch()
        title_layout.addWidget(add_btn)
        title_layout.addWidget(ai_btn)
        layout.addLayout(title_layout)
        
        # 统计卡片区域
        self.stats_layout = QHBoxLayout()
        self.stats_layout.setSpacing(Theme.SPACING_MEDIUM)
        
        self.income_card = StatCard("总收入", "¥0.00", Theme.SUCCESS)
        self.expense_card = StatCard("总支出", "¥0.00", Theme.ERROR)
        self.balance_card = StatCard("净余额", "¥0.00", Theme.PRIMARY)
        
        self.stats_layout.addWidget(self.income_card)
        self.stats_layout.addWidget(self.expense_card)
        self.stats_layout.addWidget(self.balance_card)
        layout.addLayout(self.stats_layout)
        
        # 搜索筛选区域
        search_layout = self.create_search_layout()
        layout.addLayout(search_layout)
        
        # 分隔线
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"background-color: {Theme.color_to_str(Theme.DIVIDER)};")
        divider.setFixedHeight(1)
        layout.addWidget(divider)
        
        # 表格
        self.table = TransactionTableWidget()
        layout.addWidget(self.table)
        
    def create_search_layout(self) -> QHBoxLayout:
        """创建搜索筛选布局"""
        layout = QHBoxLayout()
        layout.setSpacing(Theme.SPACING_MEDIUM)
        
        # 搜索框
        self.search_input = SearchLineEdit()
        self.search_input.setPlaceholderText("搜索交易描述或标签...")
        self.search_input.setFont(Theme.font(Theme.FONT_BODY))
        self.search_input.setFixedHeight(42)
        self.search_input.textChanged.connect(self.filter_transactions)
        
        # 类型筛选
        type_label = QLabel("类型:")
        type_label.setFont(Theme.font(Theme.FONT_BODY, True))
        type_label.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_SECONDARY)};")
        
        self.type_filter = ComboBox()
        self.type_filter.addItems(['全部', '收入', '支出'])
        self.type_filter.setFont(Theme.font(Theme.FONT_BODY))
        self.type_filter.setFixedSize(120, 42)
        self.type_filter.currentTextChanged.connect(self.filter_transactions)
        
        # 日期筛选
        date_label = QLabel("起始日期:")
        date_label.setFont(Theme.font(Theme.FONT_BODY, True))
        date_label.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_SECONDARY)};")
        
        self.start_date = DateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.start_date.setFont(Theme.font(Theme.FONT_BODY))
        # 统一日期显示格式，并采用“固定高度+最小宽度”避免在高DPI下轻微遮挡
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setFixedHeight(42)
        self.start_date.setMinimumWidth(230)
        self.start_date.dateChanged.connect(self.filter_transactions)
        
        end_label = QLabel("结束日期:")
        end_label.setFont(Theme.font(Theme.FONT_BODY, True))
        end_label.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_SECONDARY)};")
        
        self.end_date = DateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setFont(Theme.font(Theme.FONT_BODY))
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setFixedHeight(42)
        self.end_date.setMinimumWidth(230)
        self.end_date.dateChanged.connect(self.filter_transactions)
        
        # 刷新按钮
        refresh_btn = ToolButton(FluentIcon.SYNC)
        refresh_btn.setFixedSize(42, 42)
        refresh_btn.clicked.connect(self.load_transactions)
        refresh_btn.setToolTip("刷新数据")
        
        layout.addWidget(self.search_input, 3)
        layout.addWidget(type_label)
        layout.addWidget(self.type_filter)
        layout.addWidget(date_label)
        layout.addWidget(self.start_date)
        layout.addWidget(end_label)
        layout.addWidget(self.end_date)
        layout.addWidget(refresh_btn)
        
        return layout
    
    def load_transactions(self):
        """加载交易数据"""
        self.transactions = self.service.get_all_transactions()
        self.update_stats()
        self.filter_transactions()
    
    def update_stats(self):
        """更新统计数据"""
        total_income = sum(t.amount for t in self.transactions if t.transaction_type == 'INCOME')
        total_expense = sum(t.amount for t in self.transactions if t.transaction_type == 'EXPENSE')
        balance = total_income - total_expense
        
        # 更新卡片
        self.income_card.update_value(f"¥{total_income:,.2f}")
        self.expense_card.update_value(f"¥{total_expense:,.2f}")
        
        # 余额颜色
        balance_color = Theme.SUCCESS if balance >= 0 else Theme.ERROR
        self.balance_card.update_value(f"¥{balance:,.2f}", balance_color)
    
    def filter_transactions(self):
        """筛选交易记录"""
        keyword = self.search_input.text().lower()
        trans_type = self.type_filter.currentText()
        start = self.start_date.date().toPyDate()
        end = self.end_date.date().toPyDate()
        
        filtered = []
        for t in self.transactions:
            # 类型筛选
            if trans_type == '收入' and t.transaction_type != 'INCOME':
                continue
            if trans_type == '支出' and t.transaction_type != 'EXPENSE':
                continue
            
            # 日期筛选
            t_date = t.date.date()
            if t_date < start or t_date > end:
                continue
            
            # 关键字筛选
            if keyword:
                if (keyword not in t.description.lower() and 
                    not any(keyword in tag.lower() for tag in t.tags)):
                    continue
            
            filtered.append(t)
        
        self.display_transactions(filtered)
    
    def display_transactions(self, transactions: list):
        """显示交易记录"""
        self.table.setRowCount(0)
        self.table.setRowCount(len(transactions))
        
        for row, trans in enumerate(transactions):
            # 日期
            date_item = QTableWidgetItem(trans.date.strftime('%Y-%m-%d'))
            date_item.setFont(Theme.font(Theme.FONT_BODY))
            date_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, date_item)
            
            # 类型
            type_text = '收入' if trans.transaction_type == 'INCOME' else '支出'
            type_item = QTableWidgetItem(type_text)
            type_item.setFont(Theme.font(Theme.FONT_BODY, True))
            type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            
            if trans.transaction_type == 'INCOME':
                type_item.setForeground(Theme.SUCCESS)
            else:
                type_item.setForeground(Theme.ERROR)
            
            self.table.setItem(row, 1, type_item)
            
            # 金额
            amount_item = QTableWidgetItem(f"¥{trans.amount:,.2f}")
            amount_item.setFont(Theme.font(Theme.FONT_SUBTITLE, True))
            amount_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            if trans.transaction_type == 'INCOME':
                amount_item.setForeground(Theme.SUCCESS)
            else:
                amount_item.setForeground(Theme.ERROR)
            
            self.table.setItem(row, 2, amount_item)
            
            # 描述
            desc_item = QTableWidgetItem(trans.description)
            desc_item.setFont(Theme.font(Theme.FONT_BODY))
            self.table.setItem(row, 3, desc_item)
            
            # 标签
            tags_item = QTableWidgetItem(', '.join(trans.tags) if trans.tags else '-')
            tags_item.setFont(Theme.font(Theme.FONT_CAPTION))
            tags_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            tags_item.setForeground(Theme.TEXT_SECONDARY)
            self.table.setItem(row, 4, tags_item)
            
            # 操作按钮
            self.add_action_buttons(row, trans)
    
    def add_action_buttons(self, row: int, transaction: Transaction):
        """添加操作按钮"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(Theme.SPACING_SMALL, Theme.SPACING_XSMALL, 
                                 Theme.SPACING_SMALL, Theme.SPACING_XSMALL)
        layout.setSpacing(Theme.SPACING_XSMALL)
        
        # 编辑按钮
        edit_btn = PushButton(FluentIcon.EDIT, "编辑")
        edit_btn.setFont(Theme.font(Theme.FONT_BODY))
        # 增加按钮宽度与高度，避免中文文本与图标被裁剪
        edit_btn.setFixedSize(96, 40)
        edit_btn.clicked.connect(lambda: self.edit_transaction(transaction))
        
        # 删除按钮
        delete_btn = PushButton(FluentIcon.DELETE, "删除")
        delete_btn.setFont(Theme.font(Theme.FONT_BODY))
        delete_btn.setFixedSize(96, 40)
        delete_btn.clicked.connect(lambda: self.delete_transaction(transaction))
        
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)
        layout.addStretch()
        
        self.table.setCellWidget(row, 5, widget)
    
    def add_transaction(self):
        """添加交易"""
        dialog = AddTransactionDialog(self)
        dialog.transaction_saved.connect(self.on_transaction_saved)
        dialog.exec()

    def open_ai_dialog(self):
        """打开 AI 自然语言录入对话框"""
        dialog = AICommandDialog(self.service, self)
        dialog.executed.connect(self.on_ai_executed)
        dialog.exec()

    def on_ai_executed(self, result: dict):
        """AI 执行完成后刷新视图并给予反馈。"""
        # 放宽过滤范围，避免新数据因过滤而不可见
        self.search_input.setText("")
        self.type_filter.setCurrentText('全部')
        self.start_date.setDate(QDate.currentDate().addMonths(-12))
        self.end_date.setDate(QDate.currentDate())

        self.load_transactions()

        added = len(result.get('added', []))
        updated = len(result.get('updated', []))
        deleted = len(result.get('deleted', []))
        InfoBar.success(
            title="AI 已应用",
            content=f"新增 {added}，更新 {updated}，删除 {deleted}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2500,
            parent=self,
        )
    
    def edit_transaction(self, transaction: Transaction):
        """编辑交易"""
        dialog = AddTransactionDialog(self, transaction)
        dialog.transaction_saved.connect(self.on_transaction_saved)
        dialog.exec()
    
    def delete_transaction(self, transaction: Transaction):
        """删除交易"""
        result = MessageBox(
            "确认删除",
            f"确定要删除这笔交易吗?\n\n{transaction.description} - ¥{transaction.amount:,.2f}",
            self
        ).exec()
        
        if result:
            # 使用模型中的 transaction_id
            self.service.delete_transaction(transaction.transaction_id)
            InfoBar.success(
                title="删除成功",
                content="交易记录已删除",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self.load_transactions()
    
    def on_transaction_saved(self, transaction: Transaction):
        """交易保存回调"""
        # 以 transaction_id 判断是否已存在记录
        exists = self.service.get_transaction(transaction.transaction_id) is not None
        if exists:
            # 显式调用服务层更新，避免引用更新未持久化
            self.service.update_transaction(
                transaction.transaction_id,
                amount=transaction.amount,
                transaction_type=transaction.transaction_type,
                date=transaction.date,
                description=transaction.description,
                is_recurring=transaction.is_recurring,
                auto_labeled=transaction.auto_labeled,
                tags=transaction.tags
            )
            msg = "更新成功"
        else:
            self.service.add_transaction(transaction)
            msg = "添加成功"
        
        InfoBar.success(
            title=msg,
            content="交易记录已保存",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )
        self.load_transactions()


class MainWindow(FluentWindow):
    """主窗口 - Fluent Design风格"""
    
    def __init__(self):
        super().__init__()
        self.service = TransactionService()
        self.init_window()
        self.init_navigation()
        
    def init_window(self):
        """初始化窗口"""
        self.setWindowTitle("个人记账本")
        self.resize(1400, 900)
        
        # 窗口样式
        self.setStyleSheet(f"""
            FluentWindow {{
                background-color: {Theme.color_to_str(Theme.BACKGROUND)};
            }}
        """)
    
    def init_navigation(self):
        """初始化导航"""
        # 仪表盘
        self.dashboard = DashboardInterface(self.service)
        self.dashboard.setObjectName("dashboard")
        self.addSubInterface(
            self.dashboard,
            FluentIcon.HOME,
            "仪表盘",
            NavigationItemPosition.TOP
        )
        # 统计分析
        self.analytics = AnalyticsInterface(self.service)
        self.analytics.setObjectName("analytics")
        # 使用安全的导航图标（CALENDAR 通常可用）
        self.addSubInterface(
            self.analytics,
            FluentIcon.CALENDAR,
            "统计分析",
            NavigationItemPosition.TOP
        )
        
        # 加载数据
        self.dashboard.load_transactions()
        
        # 设置默认界面
        self.stackedWidget.setCurrentWidget(self.dashboard)
