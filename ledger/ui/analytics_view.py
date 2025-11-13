"""
统计分析界面 - 基本报表生成
- 月度汇总（收入/支出/净额/笔数）
- 标签汇总（金额/笔数）
- 日期范围与类型筛选
- 导出CSV
"""

from typing import List
from datetime import datetime

import os
import pathlib
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QSizePolicy, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QPainter
try:
    from PyQt5.QtChart import (
        QChart, QChartView, QPieSeries, QBarSeries, QBarSet,
        QBarCategoryAxis, QValueAxis
    )
    HAS_QT_CHARTS = True
except Exception:
    # 尝试动态加入 Qt5/bin 到 DLL 搜索路径后再次导入（兼容某些 Windows 环境）
    try:
        import PyQt5  # type: ignore
        qt_bin = pathlib.Path(PyQt5.__file__).parent / 'Qt5' / 'bin'
        if qt_bin.exists():
            try:
                os.add_dll_directory(str(qt_bin))  # Python 3.8+
            except Exception:
                os.environ['PATH'] = str(qt_bin) + os.pathsep + os.environ.get('PATH', '')
        from PyQt5.QtChart import (
            QChart, QChartView, QPieSeries, QBarSeries, QBarSet,
            QBarCategoryAxis, QValueAxis
        )
        HAS_QT_CHARTS = True
    except Exception:
        HAS_QT_CHARTS = False
from qfluentwidgets import (
    CardWidget, TableWidget, PrimaryPushButton, PushButton,
    ComboBox, DateEdit, InfoBar, InfoBarPosition, FluentIcon
)

from ledger.models.transaction import Transaction
from ledger.services.transaction_service import TransactionService
from ledger.services.analytics_service import AnalyticsService, MonthlySummary, TagSummary
from ledger.ui.theme import Theme


class AnalyticsInterface(QWidget):
    """统计分析界面"""

    def __init__(self, service: TransactionService, parent=None):
        super().__init__(parent)
        self.service = service
        self.analytics = AnalyticsService(service)
        self.transactions: List[Transaction] = []
        self.init_ui()
        self.refresh()

    # -------------------- UI --------------------
    def init_ui(self):
        # 根布局：使用滚动区域包裹内容，避免页面高度受限
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(Theme.SPACING_LARGE, Theme.SPACING_LARGE,
                                  Theme.SPACING_LARGE, Theme.SPACING_LARGE)
        layout.setSpacing(Theme.SPACING_LARGE)
        scroll.setWidget(content)
        root.addWidget(scroll)

        # 标题与导出
        title_row = QHBoxLayout()
        title = QLabel("统计分析")
        title.setFont(Theme.font(Theme.FONT_LARGE, True))
        export_btn = PrimaryPushButton(FluentIcon.SAVE, "导出CSV")
        export_btn.setFixedSize(120, 40)
        export_btn.clicked.connect(self.export_csv)
        title_row.addWidget(title)
        title_row.addStretch()
        title_row.addWidget(export_btn)
        layout.addLayout(title_row)

        # 筛选行
        filter_row = QHBoxLayout()
        filter_row.setSpacing(Theme.SPACING_MEDIUM)

        type_label = QLabel("类型:")
        type_label.setFont(Theme.font(Theme.FONT_BODY, True))
        self.type_filter = ComboBox()
        self.type_filter.addItems(["全部", "收入", "支出"]) 
        self.type_filter.currentTextChanged.connect(self.refresh)
        self.type_filter.setFixedSize(120, 40)

        start_label = QLabel("起始日期:")
        start_label.setFont(Theme.font(Theme.FONT_BODY, True))
        self.start_date = DateEdit()
        self.start_date.setDate(QDate.currentDate().addMonths(-6))
        self.start_date.setDisplayFormat("yyyy-MM-dd")
        self.start_date.setFixedHeight(40)
        self.start_date.setMinimumWidth(230)
        self.start_date.dateChanged.connect(self.refresh)

        end_label = QLabel("结束日期:")
        end_label.setFont(Theme.font(Theme.FONT_BODY, True))
        self.end_date = DateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setDisplayFormat("yyyy-MM-dd")
        self.end_date.setFixedHeight(40)
        self.end_date.setMinimumWidth(230)
        self.end_date.dateChanged.connect(self.refresh)

        refresh_btn = PushButton(FluentIcon.SYNC, "刷新")
        refresh_btn.setFixedSize(96, 40)
        refresh_btn.clicked.connect(self.refresh)

        filter_row.addWidget(type_label)
        filter_row.addWidget(self.type_filter)
        filter_row.addWidget(start_label)
        filter_row.addWidget(self.start_date)
        filter_row.addWidget(end_label)
        filter_row.addWidget(self.end_date)
        filter_row.addWidget(refresh_btn)
        layout.addLayout(filter_row)

    # 顶部汇总卡片（总收入/总支出/净额/笔数）
        self.summary_card = CardWidget()
        sum_layout = QHBoxLayout(self.summary_card)
        sum_layout.setContentsMargins(
            Theme.SPACING_LARGE,
            Theme.SPACING_LARGE,
            Theme.SPACING_LARGE,
            Theme.SPACING_LARGE,
        )
        sum_layout.setSpacing(Theme.SPACING_LARGE)

        def build_metric(title_text: str):
            w = QWidget()
            v = QVBoxLayout(w)
            v.setContentsMargins(0, 0, 0, 0)
            v.setSpacing(Theme.SPACING_XSMALL)
            v.setAlignment(Qt.AlignHCenter)
            title = QLabel(title_text)
            title.setFont(Theme.font(Theme.FONT_BODY, True))
            title.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_SECONDARY)};")
            title.setAlignment(Qt.AlignHCenter)
            value = QLabel("-")
            value.setFont(Theme.font(Theme.FONT_TITLE, True))
            value.setAlignment(Qt.AlignHCenter)
            # 统一最小宽度，保证留白
            w.setMinimumWidth(180)
            v.addWidget(title)
            v.addWidget(value)
            return w, value

        def v_divider():
            line = QFrame()
            line.setFrameShape(QFrame.VLine)
            line.setFixedWidth(1)
            line.setStyleSheet(f"background-color: {Theme.color_to_str(Theme.DIVIDER)};")
            return line

        w_income, self.lbl_income = build_metric("总收入")
        w_expense, self.lbl_expense = build_metric("总支出")
        w_net, self.lbl_net = build_metric("净额")
        w_count, self.lbl_count = build_metric("笔数")

        sum_layout.addWidget(w_income)
        sum_layout.addWidget(v_divider())
        sum_layout.addWidget(w_expense)
        sum_layout.addWidget(v_divider())
        sum_layout.addWidget(w_net)
        sum_layout.addWidget(v_divider())
        sum_layout.addWidget(w_count)
        sum_layout.addStretch()
        layout.addWidget(self.summary_card)

        # 图表卡片（若支持 Qt Charts）
        if HAS_QT_CHARTS:
            # 两图并排：放到同一张卡片的水平布局里
            self.charts_row_card = CardWidget()
            charts_layout = QHBoxLayout(self.charts_row_card)
            charts_layout.setContentsMargins(
                Theme.SPACING_MEDIUM,
                Theme.SPACING_MEDIUM,
                Theme.SPACING_MEDIUM,
                Theme.SPACING_MEDIUM,
            )
            charts_layout.setSpacing(Theme.SPACING_MEDIUM)

            # 左：月度柱状图
            month_wrap = QWidget()
            month_v = QVBoxLayout(month_wrap)
            month_v.setContentsMargins(0, 0, 0, 0)
            month_title = QLabel("月度收入/支出柱状图")
            month_title.setFont(Theme.font(Theme.FONT_TITLE, True))
            self.month_chart_view = QChartView()
            self.month_chart_view.setMinimumHeight(360)
            self.month_chart_view.setMinimumWidth(420)
            self.month_chart_view.setRenderHint(QPainter.Antialiasing)
            self.month_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            month_v.addWidget(month_title)
            month_v.addWidget(self.month_chart_view)

            # 右：标签饼图
            tag_wrap = QWidget()
            tag_v = QVBoxLayout(tag_wrap)
            tag_v.setContentsMargins(0, 0, 0, 0)
            tag_title = QLabel("标签支出占比饼图")
            tag_title.setFont(Theme.font(Theme.FONT_TITLE, True))
            self.tag_chart_view = QChartView()
            self.tag_chart_view.setMinimumHeight(360)
            self.tag_chart_view.setMinimumWidth(420)
            self.tag_chart_view.setRenderHint(QPainter.Antialiasing)
            self.tag_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            tag_v.addWidget(tag_title)
            tag_v.addWidget(self.tag_chart_view)

            charts_layout.addWidget(month_wrap, 1)
            charts_layout.addWidget(tag_wrap, 1)
            layout.addWidget(self.charts_row_card)
        else:
            # 提示缺少图表依赖
            self.chart_placeholder = CardWidget()
            p_layout = QVBoxLayout(self.chart_placeholder)
            tip = QLabel("未启用图表组件（PyQtChart 未加载），仅显示表格汇总。")
            tip.setFont(Theme.font(Theme.FONT_BODY, True))
            tip.setStyleSheet(f"color: {Theme.color_to_str(Theme.TEXT_SECONDARY)};")
            p_layout.addWidget(tip)
            layout.addWidget(self.chart_placeholder)

        # 月度汇总卡片
        self.month_card = CardWidget()
        month_layout = QVBoxLayout(self.month_card)
        month_title = QLabel("月度汇总")
        month_title.setFont(Theme.font(Theme.FONT_TITLE, True))
        self.month_table = TableWidget()
        self.month_table.setColumnCount(5)
        self.month_table.setHorizontalHeaderLabels(["月份", "收入", "支出", "净额", "笔数"])
        self.month_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.month_table.verticalHeader().setDefaultSectionSize(40)
        self.month_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.month_table.verticalHeader().setFixedWidth(40)
        self.month_table.horizontalHeader().setStretchLastSection(True)
        # 现代风格：去除密集网格线
        self.month_table.setShowGrid(False)
        self.month_table.setSortingEnabled(True)
        month_layout.addWidget(month_title)
        month_layout.addWidget(self.month_table)
        layout.addWidget(self.month_card)

        # 标签汇总卡片
        self.tag_card = CardWidget()
        tag_layout = QVBoxLayout(self.tag_card)
        tag_title = QLabel("标签汇总")
        tag_title.setFont(Theme.font(Theme.FONT_TITLE, True))
        self.tag_table = TableWidget()
        self.tag_table.setColumnCount(3)
        self.tag_table.setHorizontalHeaderLabels(["标签", "金额", "笔数"])
        self.tag_table.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.tag_table.verticalHeader().setDefaultSectionSize(40)
        self.tag_table.verticalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.tag_table.verticalHeader().setFixedWidth(40)
        self.tag_table.horizontalHeader().setStretchLastSection(True)
        # 现代风格：去除密集网格线
        self.tag_table.setShowGrid(False)
        self.tag_table.setSortingEnabled(True)
        tag_layout.addWidget(tag_title)
        tag_layout.addWidget(self.tag_table)
        layout.addWidget(self.tag_card)

    # -------------------- Data --------------------
    def refresh(self):
        # 拉取数据并筛选
        self.transactions = self.service.get_all_transactions()
        start = datetime.combine(self.start_date.date().toPyDate(), datetime.min.time())
        end = datetime.combine(self.end_date.date().toPyDate(), datetime.max.time())
        text = self.type_filter.currentText()
        ttype = None
        if text == '收入':
            ttype = 'INCOME'
        elif text == '支出':
            ttype = 'EXPENSE'

        filtered: List[Transaction] = self.analytics.filter_transactions(start, end, ttype)

        # 顶部总览
        totals = self.analytics.compute_totals(filtered)
        self.lbl_income.setText(f"¥{totals['income']:,.2f}")
        self.lbl_expense.setText(f"¥{totals['expense']:,.2f}")
        self.lbl_net.setText(f"¥{totals['net']:,.2f}")
        self.lbl_count.setText(f"{int(totals['count'])}")

        # 明细表
        month_rows = self.analytics.compute_monthly_summary(filtered)
        self.populate_month_table(month_rows)
        tag_rows = self.analytics.compute_tag_summary(filtered)
        self.populate_tag_table(tag_rows)

        # 图表
        if HAS_QT_CHARTS:
            self.update_month_bar_chart(month_rows)
            self.update_tag_pie_chart(tag_rows)

    def populate_month_table(self, rows: List[MonthlySummary]):
        self.month_table.setSortingEnabled(False)
        self.month_table.setRowCount(len(rows))
        for r, m in enumerate(rows):
            self.month_table.setItem(r, 0, self._item(m.month, align=Qt.AlignCenter))
            self.month_table.setItem(r, 1, self._money_item(m.income, True))
            self.month_table.setItem(r, 2, self._money_item(m.expense, False))
            self.month_table.setItem(r, 3, self._money_item(m.net, m.net >= 0))
            it_cnt = self._item(str(m.count), align=Qt.AlignCenter)
            it_cnt.setData(Qt.EditRole, int(m.count))
            self.month_table.setItem(r, 4, it_cnt)
        self.month_table.resizeColumnsToContents()
        self.month_table.setSortingEnabled(True)

    def populate_tag_table(self, rows: List[TagSummary]):
        self.tag_table.setSortingEnabled(False)
        self.tag_table.setRowCount(len(rows))
        for r, t in enumerate(rows):
            self.tag_table.setItem(r, 0, self._item(t.label, align=Qt.AlignLeft))
            it_amt = self._money_item(t.amount, False)
            it_amt.setData(Qt.EditRole, float(t.amount))
            self.tag_table.setItem(r, 1, it_amt)
            it_cnt = self._item(str(t.count), align=Qt.AlignCenter)
            it_cnt.setData(Qt.EditRole, int(t.count))
            self.tag_table.setItem(r, 2, it_cnt)
        self.tag_table.resizeColumnsToContents()
        self.tag_table.setSortingEnabled(True)

    # -------------------- Charts --------------------
    def update_month_bar_chart(self, rows: List[MonthlySummary]):
        if not HAS_QT_CHARTS:
            return
        categories = [r.month for r in rows]
        income_set = QBarSet("收入")
        expense_set = QBarSet("支出")
        for r in rows:
            income_set.append(float(r.income))
            expense_set.append(float(r.expense))
        series = QBarSeries()
        series.append(income_set)
        series.append(expense_set)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("月度收入/支出")
        chart.createDefaultAxes()

        axisX = QBarCategoryAxis()
        axisX.append(categories)
        chart.setAxisX(axisX, series)
        axisY = QValueAxis()
        axisY.setLabelFormat("%.0f")
        chart.setAxisY(axisY, series)

        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setAnimationOptions(QChart.SeriesAnimations)

        self.month_chart_view.setChart(chart)

    def update_tag_pie_chart(self, rows: List[TagSummary]):
        if not HAS_QT_CHARTS:
            return
        # 仅显示前8个，其他合并为“其他”
        top = rows[:8]
        other_sum = sum(r.amount for r in rows[8:])
        series = QPieSeries()
        for r in top:
            series.append(f"{r.label} ({r.amount:,.0f})", float(r.amount))
        if other_sum > 0:
            series.append(f"其他 ({other_sum:,.0f})", float(other_sum))

        for sl in series.slices():
            sl.setLabelVisible(True)

        chart = QChart()
        chart.addSeries(series)
        chart.setTitle("标签支出占比")
        chart.legend().setAlignment(Qt.AlignBottom)
        chart.setAnimationOptions(QChart.SeriesAnimations)
        self.tag_chart_view.setChart(chart)

    # -------------------- Export --------------------
    def export_csv(self):
        directory = QFileDialog.getExistingDirectory(self, "选择导出目录")
        if not directory:
            return
        try:
            # 导出月度
            month_path = os.path.join(directory, 'monthly_summary.csv')
            with open(month_path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write('月份,收入,支出,净额,笔数\n')
                for row in range(self.month_table.rowCount()):
                    cols = [self.month_table.item(row, c).text() for c in range(5)]
                    f.write(','.join(cols) + '\n')

            # 导出标签
            tag_path = os.path.join(directory, 'tag_summary.csv')
            with open(tag_path, 'w', encoding='utf-8-sig', newline='') as f:
                f.write('标签,金额,笔数\n')
                for row in range(self.tag_table.rowCount()):
                    cols = [self.tag_table.item(row, c).text() for c in range(3)]
                    f.write(','.join(cols) + '\n')

            InfoBar.success(
                title="导出成功",
                content=f"文件已导出到: {directory}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2500,
                parent=self
            )
        except Exception as e:
            InfoBar.error(
                title="导出失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    # -------------------- Helpers --------------------
    def _item(self, text: str, align=Qt.AlignLeft):
        from PyQt5.QtWidgets import QTableWidgetItem
        it = QTableWidgetItem(text)
        it.setFont(Theme.font(Theme.FONT_BODY))
        it.setTextAlignment(align)
        return it

    def _money_item(self, value: float, positive: bool):
        from PyQt5.QtWidgets import QTableWidgetItem
        it = QTableWidgetItem(f"¥{value:,.2f}")
        it.setFont(Theme.font(Theme.FONT_BODY, True))
        it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        it.setForeground(Theme.SUCCESS if positive else Theme.ERROR)
        # 数值用于排序
        it.setData(Qt.EditRole, float(value))
        return it
