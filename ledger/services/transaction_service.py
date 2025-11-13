import json
import os
import logging
from typing import List, Optional
from datetime import datetime
from ledger.models.transaction import Transaction
from ledger.config.settings import Config

# 确保目录存在
Config.ensure_directories()

logger = logging.getLogger(__name__)

class TransactionService:
    """交易管理服务类"""

    def __init__(self):
        self.data_file = Config.DATABASE_PATH
        self.transactions = self._load_transactions()

    def _load_transactions(self) -> List[Transaction]:
        """从文件加载交易数据"""
        if not os.path.exists(self.data_file):
            return []

        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [Transaction.from_dict(item) for item in data]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.error("加载交易数据失败: %s", e)
            return []

    def _save_transactions(self):
        """保存交易数据到文件"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                data = [transaction.to_dict() for transaction in self.transactions]
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info("保存了 %s 条交易记录", len(self.transactions))
        except Exception as e:
            logger.error("保存交易数据失败: %s", e)
            raise

    def add_transaction(self, transaction: Transaction) -> str:
        """添加新交易"""
        self.transactions.append(transaction)
        self._save_transactions()
        logger.info("添加交易: %s", transaction)
        return transaction.transaction_id

    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """根据ID获取交易"""
        for transaction in self.transactions:
            if transaction.transaction_id == transaction_id:
                return transaction
        return None

    def get_all_transactions(self) -> List[Transaction]:
        """获取所有交易"""
        return self.transactions.copy()

    def update_transaction(self, transaction_id: str, **kwargs) -> bool:
        """更新交易信息"""
        transaction = self.get_transaction(transaction_id)
        if not transaction:
            logger.warning("未找到交易: %s", transaction_id)
            return False

        # 更新属性
        for key, value in kwargs.items():
            if hasattr(transaction, key):
                setattr(transaction, key, value)

        self._save_transactions()
        logger.info("更新交易: %s", transaction_id)
        return True

    def delete_transaction(self, transaction_id: str) -> bool:
        """删除交易"""
        for i, transaction in enumerate(self.transactions):
            if transaction.transaction_id == transaction_id:
                deleted_transaction = self.transactions.pop(i)
                self._save_transactions()
                logger.info("删除交易: %s", deleted_transaction)
                return True

        logger.warning("未找到交易: %s", transaction_id)
        return False

    def search_transactions(self,
                          start_date: Optional[datetime] = None,
                          end_date: Optional[datetime] = None,
                          transaction_type: Optional[str] = None,
                          min_amount: Optional[float] = None,
                          max_amount: Optional[float] = None,
                          description: Optional[str] = None) -> List[Transaction]:
        """搜索交易"""
        results = self.transactions.copy()

        if start_date:
            results = [t for t in results if t.date >= start_date]
        if end_date:
            results = [t for t in results if t.date <= end_date]
        if transaction_type:
            results = [t for t in results if t.transaction_type == transaction_type]
        if min_amount is not None:
            results = [t for t in results if t.amount >= min_amount]
        if max_amount is not None:
            results = [t for t in results if t.amount <= max_amount]
        if description:
            results = [t for t in results if description.lower() in t.description.lower()]

        return results

    def get_transaction_summary(self) -> dict:
        """获取交易汇总信息"""
        total_income = sum(t.amount for t in self.transactions if t.transaction_type == 'INCOME')
        total_expense = sum(t.amount for t in self.transactions if t.transaction_type == 'EXPENSE')
        net_amount = total_income - total_expense

        return {
            'total_transactions': len(self.transactions),
            'total_income': total_income,
            'total_expense': total_expense,
            'net_amount': net_amount
        }