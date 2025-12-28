import pytest
import os
import json
from datetime import datetime
from ledger.services.transaction_service import TransactionService
from ledger.models.transaction import Transaction
from ledger.config.settings import Config

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_ledger.json"
    # Mock Config.DATABASE_PATH
    original_db_path = Config.DATABASE_PATH
    Config.DATABASE_PATH = str(db_file)
    yield str(db_file)
    Config.DATABASE_PATH = original_db_path

@pytest.fixture
def transaction_service(temp_db):
    return TransactionService()

def test_add_and_get_transaction(transaction_service):
    t = Transaction(
        amount=100.0,
        tags=["餐饮"],
        description="午餐",
        transaction_type="EXPENSE",
        date=datetime.now()
    )
    tid = transaction_service.add_transaction(t)
    retrieved = transaction_service.get_transaction(tid)
    assert retrieved is not None
    assert retrieved.amount == 100.0
    assert retrieved.description == "午餐"

def test_delete_transaction(transaction_service):
    t = Transaction(amount=50.0, tags=["交通"], description="打车", transaction_type="EXPENSE")
    tid = transaction_service.add_transaction(t)
    assert transaction_service.delete_transaction(tid) is True
    assert transaction_service.get_transaction(tid) is None

def test_update_transaction(transaction_service):
    t = Transaction(amount=50.0, tags=["交通"], description="打车", transaction_type="EXPENSE")
    tid = transaction_service.add_transaction(t)
    assert transaction_service.update_transaction(tid, amount=60.0, description="加班打车") is True
    updated = transaction_service.get_transaction(tid)
    assert updated.amount == 60.0
    assert updated.description == "加班打车"

def test_search_transactions(transaction_service):
    t1 = Transaction(amount=100.0, tags=["餐饮"], description="午餐", transaction_type="EXPENSE", date=datetime(2023, 1, 1))
    t2 = Transaction(amount=200.0, tags=["工资"], description="发工资", transaction_type="INCOME", date=datetime(2023, 1, 2))
    transaction_service.add_transaction(t1)
    transaction_service.add_transaction(t2)

    # 1. 按类型搜索
    assert len(transaction_service.search_transactions(transaction_type="EXPENSE")) == 1
    # 2. 按金额范围搜索
    assert len(transaction_service.search_transactions(min_amount=150)) == 1
    # 3. 按描述搜索
    assert len(transaction_service.search_transactions(description="工资")) == 1
    # 4. 按日期范围搜索
    results = transaction_service.search_transactions(start_date=datetime(2023, 1, 1), end_date=datetime(2023, 1, 1))
    assert len(results) == 1
    assert results[0].description == "午餐"

def test_get_transaction_summary(transaction_service):
    transaction_service.add_transaction(Transaction(amount=100.0, tags=["餐饮"], description="午餐", transaction_type="EXPENSE"))
    transaction_service.add_transaction(Transaction(amount=500.0, tags=["工资"], description="发工资", transaction_type="INCOME"))
    
    summary = transaction_service.get_transaction_summary()
    assert summary['total_transactions'] == 2
    assert summary['total_income'] == 500.0
    assert summary['total_expense'] == 100.0
    assert summary['net_amount'] == 400.0

def test_load_invalid_json(temp_db):
    with open(temp_db, 'w') as f:
        f.write("invalid json")
    service = TransactionService()
    assert len(service.get_all_transactions()) == 0
