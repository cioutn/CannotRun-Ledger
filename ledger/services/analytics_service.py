from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from ledger.models.transaction import Transaction
from ledger.services.transaction_service import TransactionService


@dataclass(frozen=True)
class MonthlySummary:
    month: str  # YYYY-MM
    income: float
    expense: float
    net: float
    count: int


@dataclass(frozen=True)
class TagSummary:
    label: str
    amount: float  # 仅统计支出金额，收入不计入标签金额
    count: int


class AnalyticsService:
    """统计分析服务：只做纯业务计算，不涉及 UI。"""

    def __init__(self, transaction_service: TransactionService):
        self.ts = transaction_service

    def filter_transactions(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        transaction_type: Optional[str] = None,
    ) -> List[Transaction]:
        """按日期区间与类型筛选交易。

        transaction_type: INCOME | EXPENSE | None
        """
        return self.ts.search_transactions(
            start_date=start,
            end_date=end,
            transaction_type=transaction_type,
        )

    def compute_monthly_summary(self, items: List[Transaction]) -> List[MonthlySummary]:
        """生成按月汇总（收入/支出/净额/笔数）。"""
        agg: Dict[str, Dict[str, float]] = defaultdict(lambda: {
            "income": 0.0,
            "expense": 0.0,
            "count": 0,
        })

        for t in items:
            key = t.date.strftime("%Y-%m")
            agg[key]["count"] += 1
            if t.transaction_type == "INCOME":
                agg[key]["income"] += float(t.amount)
            else:
                agg[key]["expense"] += float(t.amount)

        months = sorted(agg.keys())
        results: List[MonthlySummary] = []
        for m in months:
            income = float(agg[m]["income"])
            expense = float(agg[m]["expense"])
            net = income - expense
            count = int(agg[m]["count"])
            results.append(MonthlySummary(month=m, income=income, expense=expense, net=net, count=count))
        return results

    def compute_tag_summary(self, items: List[Transaction]) -> List[TagSummary]:
        """生成按标签汇总（仅统计支出金额）。"""
        tag_amount: Dict[str, float] = defaultdict(float)
        tag_count: Dict[str, int] = defaultdict(int)

        for t in items:
            labels = t.tags if t.tags else ["-"]
            for lb in labels:
                if t.transaction_type == "EXPENSE":
                    tag_amount[lb] += float(t.amount)
                tag_count[lb] += 1

        # 按金额倒序
        sorted_labels = sorted(tag_amount.items(), key=lambda kv: kv[1], reverse=True)
        return [TagSummary(label=k, amount=float(v), count=tag_count[k]) for k, v in sorted_labels]

    def compute_totals(self, items: List[Transaction]) -> Dict[str, float]:
        """计算筛选后的总收入/总支出/净额/笔数。"""
        income = sum(float(t.amount) for t in items if t.transaction_type == "INCOME")
        expense = sum(float(t.amount) for t in items if t.transaction_type == "EXPENSE")
        net = income - expense
        return {
            "income": income,
            "expense": expense,
            "net": net,
            "count": int(len(items)),
        }
