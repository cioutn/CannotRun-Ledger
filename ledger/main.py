#!/usr/bin/env python3
"""
个人记账本系统 - 演示脚本
用于演示交易管理功能
"""

from ledger.models.transaction import Transaction
from ledger.services.transaction_service import TransactionService


def demo_cli():
    """命令行演示"""
    print("=" * 60)
    print("个人记账本系统 - CLI演示")
    print("=" * 60)

    # 初始化服务
    service = TransactionService()

    # 清空现有数据
    print("\n1. 清空现有数据...")
    for trans in service.get_all_transactions():
        service.delete_transaction(trans.transaction_id)

    # 添加示例数据
    print("\n2. 添加示例交易数据...")
    transactions_data = [
        {
            'amount': 50.0,
            'type': 'EXPENSE',
            'desc': '午餐 - 星巴克',
            'tags': ['餐饮', '日常']
        },
        {
            'amount': 3000.0,
            'type': 'INCOME',
            'desc': '工资收入',
            'tags': ['收入', '工资']
        },
        {
            'amount': 800.0,
            'type': 'EXPENSE',
            'desc': '月租房租',
            'tags': ['住房', '固定支出']
        },
        {
            'amount': 120.0,
            'type': 'EXPENSE',
            'desc': '健身房会员',
            'tags': ['健身', '健康']
        },
        {
            'amount': 500.0,
            'type': 'INCOME',
            'desc': '兼职报酬',
            'tags': ['收入', '兼职']
        },
    ]

    for data in transactions_data:
        trans = Transaction(
            amount=data['amount'],
            transaction_type=data['type'],
            description=data['desc'],
            tags=data['tags']
        )
        service.add_transaction(trans)
        print(f"  ✓ 添加: {data['desc']} - ¥{data['amount']}")

    # 显示所有交易
    print("\n3. 所有交易列表:")
    print("-" * 60)
    for trans in service.get_all_transactions():
        trans_type = "收入" if trans.transaction_type == "INCOME" else "支出"
        print(f"  {trans.date.strftime('%Y-%m-%d')} | {trans_type:2} | ¥{trans.amount:8.2f} | {trans.description}")
    print("-" * 60)

    # 显示统计信息
    print("\n4. 统计信息:")
    summary = service.get_transaction_summary()
    print(f"  总交易数: {summary['total_transactions']}")
    print(f"  总收入:   ¥{summary['total_income']:.2f}")
    print(f"  总支出:   ¥{summary['total_expense']:.2f}")
    print(f"  净金额:   ¥{summary['net_amount']:.2f}")

    # 搜索支出
    print("\n5. 搜索支出交易:")
    expenses = service.search_transactions(transaction_type='EXPENSE')
    print(f"  找到 {len(expenses)} 条支出:")
    for trans in expenses:
        print(f"    - {trans.description}: ¥{trans.amount}")

    print("\n" + "=" * 60)
    print("CLI演示完成！")
    print("运行 'python ledger/app.py' 启动GUI应用")
    print("=" * 60)


if __name__ == "__main__":
    demo_cli()