import pytest
from hypothesis import given, strategies as st
from ledger.models.transaction import Transaction
from datetime import datetime

# 定义随机交易数据的策略
transaction_dict_strategy = st.fixed_dictionaries({
    'transaction_id': st.uuids().map(str),
    'amount': st.floats(allow_nan=False, allow_infinity=False, min_value=0, max_value=1e9),
    'transaction_type': st.sampled_from(['INCOME', 'EXPENSE']),
    'date': st.datetimes().map(lambda d: d.isoformat()),
    'description': st.text(min_size=0, max_size=1000),
    'is_recurring': st.booleans(),
    'auto_labeled': st.booleans(),
    'tags': st.lists(st.text(min_size=1, max_size=50), max_size=10)
})

@given(transaction_dict_strategy)
def test_transaction_from_dict_fuzz(data):
    # 模糊测试：确保从随机字典创建 Transaction 不会崩溃，且能正确还原
    try:
        t = Transaction.from_dict(data)
        assert isinstance(t, Transaction)
        assert t.amount == data['amount']
        assert t.transaction_type == data['transaction_type']
        # 还原为字典应与原数据基本一致（日期格式可能略有差异，但 isoformat 应一致）
        # 注意：Transaction.to_dict() 也会调用 isoformat()
        assert t.to_dict()['transaction_id'] == data['transaction_id']
    except Exception as e:
        # 如果抛出异常，打印数据以便调试
        print(f"Failed with data: {data}")
        raise e

@given(st.dictionaries(st.text(), st.text()))
def test_transaction_from_dict_robustness(data):
    # 健壮性测试：输入完全随机的字典，不应导致未捕获的系统级崩溃
    # 预期的行为是抛出 KeyError 或 ValueError，而不是 Segfault
    try:
        Transaction.from_dict(data)
    except (KeyError, ValueError, TypeError):
        pass
    except Exception as e:
        pytest.fail(f"Unexpected exception {type(e).__name__}: {e}")
