from datetime import datetime
from typing import List, Optional
import uuid
# Removed unused import to satisfy linting

class Transaction:
    """交易记录模型"""

    def __init__(self,
                 amount: float,
                 transaction_type: str,
                 description: str,
                 date: Optional[datetime] = None,
                 transaction_id: Optional[str] = None,
                 is_recurring: bool = False,
                 auto_labeled: bool = False,
                 tags: Optional[List[str]] = None):
        self.transaction_id = transaction_id or str(uuid.uuid4())
        self.amount = amount
        self.transaction_type = transaction_type  # 'INCOME' or 'EXPENSE'
        self.date = date or datetime.now()
        self.description = description
        self.is_recurring = is_recurring
        self.auto_labeled = auto_labeled
        self.tags = tags or []

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'transaction_type': self.transaction_type,
            'date': self.date.isoformat(),
            'description': self.description,
            'is_recurring': self.is_recurring,
            'auto_labeled': self.auto_labeled,
            'tags': self.tags
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """从字典创建交易对象"""
        return cls(
            transaction_id=data['transaction_id'],
            amount=data['amount'],
            transaction_type=data['transaction_type'],
            date=datetime.fromisoformat(data['date']),
            description=data['description'],
            is_recurring=data.get('is_recurring', False),
            auto_labeled=data.get('auto_labeled', False),
            tags=data.get('tags', [])
        )

    def __str__(self) -> str:
        return f"Transaction({self.transaction_id}, {self.transaction_type}, {self.amount}, {self.description})"