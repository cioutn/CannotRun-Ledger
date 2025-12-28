import pytest
import os
from datetime import datetime
from ledger.services.transaction_service import TransactionService
from ledger.services.analytics_service import AnalyticsService
from ledger.models.transaction import Transaction
from ledger.config.settings import Config

@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "integration_ledger.json"
    original_db_path = Config.DATABASE_PATH
    Config.DATABASE_PATH = str(db_file)
    yield str(db_file)
    Config.DATABASE_PATH = original_db_path

def test_transaction_persistence_integration(temp_db):
    # 场景 1: 交易持久化集成
    # 1. 初始化服务并添加交易
    service = TransactionService()
    t = Transaction(amount=100.0, tags=["餐饮"], description="集成测试午餐", transaction_type="EXPENSE")
    tid = service.add_transaction(t)
    
    # 2. 验证文件是否生成
    assert os.path.exists(temp_db)
    
    # 3. 重新实例化服务，验证数据是否加载
    new_service = TransactionService()
    loaded_t = new_service.get_transaction(tid)
    assert loaded_t is not None
    assert loaded_t.amount == 100.0
    assert loaded_t.description == "集成测试午餐"

def test_analytics_integration(temp_db):
    # 场景 2: 统计分析集成
    service = TransactionService()
    analytics = AnalyticsService(service)
    
    # 1. 注入交易数据
    service.add_transaction(Transaction(amount=1000.0, tags=["工资"], description="月薪", transaction_type="INCOME", date=datetime(2023, 1, 1)))
    service.add_transaction(Transaction(amount=200.0, tags=["餐饮"], description="晚餐", transaction_type="EXPENSE", date=datetime(2023, 1, 2)))
    service.add_transaction(Transaction(amount=300.0, tags=["购物"], description="买衣服", transaction_type="EXPENSE", date=datetime(2023, 1, 3)))
    
    # 2. 调用分析服务
    items = service.get_all_transactions()
    summary = analytics.compute_monthly_summary(items)
    
    # 3. 验证汇总结果
    assert len(summary) == 1
    assert summary[0].month == "2023-01"
    assert summary[0].income == 1000.0
    assert summary[0].expense == 500.0
    assert summary[0].net == 500.0
    assert summary[0].count == 3

    # 4. 验证标签汇总
    tag_summary = analytics.compute_tag_summary(items)
    # 餐饮和购物各 1 笔支出，工资是收入不计入金额但计入笔数
    assert any(s.label == "餐饮" and s.amount == 200.0 for s in tag_summary)
    assert any(s.label == "购物" and s.amount == 300.0 for s in tag_summary)
