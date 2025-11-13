#!/usr/bin/env python3
"""
个人记账本系统 - 模块入口
允许通过 `python -m ledger` 运行应用。
"""

import sys
from .app import main

if __name__ == "__main__":
    sys.exit(main())