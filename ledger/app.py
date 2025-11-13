#!/usr/bin/env python3
"""
个人记账本系统 - 主应用入口 (Fluent Design版本)
"""

import sys
import os
import logging
import traceback

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = logging.getLogger(__name__)

def _configure_logging():
    """配置应用级日志（控制台 + 文件），避免在服务层重复配置。

    使用 Config 中的 LOG_LEVEL 与 LOG_FILE；仅在根 logger 无 handler 时配置，
    防止重复添加 handler 导致重复输出。
    """
    from ledger.config.settings import Config  # 延迟导入，避免模块初始化顺序问题

    root = logging.getLogger()
    if root.handlers:
        return

    level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
    root.setLevel(level)

    fmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # 控制台
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root.addHandler(sh)

    # 文件
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(Config.LOG_FILE), exist_ok=True)
        fh = logging.FileHandler(Config.LOG_FILE, encoding='utf-8')
        fh.setFormatter(fmt)
        root.addHandler(fh)
    except Exception as e:  # pylint: disable=broad-except
        # 文件日志配置失败不影响应用启动
        logger.warning("文件日志初始化失败: %s", e)

try:
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from PyQt5.QtGui import QFont
    from qfluentwidgets import setTheme, Theme, setThemeColor
    from ledger.ui.main_window import MainWindow
    logger.info("成功导入PyQt5和qfluentwidgets")
except ImportError as e:
    logger.error("导入错误: %s", e)
    logger.error("请确保已安装依赖: pip install PyQt5 PyQt-Fluent-Widgets")
    sys.exit(1)


def main():
    """主函数"""
    try:
        _configure_logging()
        logger.info("启动个人记账本系统 (Fluent Design)...")

        # 启用高DPI缩放
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        app = QApplication(sys.argv)

        # 设置应用属性
        app.setApplicationName("个人记账本")
        app.setOrganizationName("LedgerApp")

        # 设置全局字体
        font = QFont("Microsoft YaHei UI", 10)
        app.setFont(font)

        # 设置主题
        setTheme(Theme.LIGHT)
        setThemeColor('#1976d2')

        logger.info("创建主窗口...")
        window = MainWindow()

        logger.info("显示窗口...")
        window.show()

        logger.info("进入应用循环...")
        exit_code = app.exec_()
        logger.info("应用正常退出 (代码: %s)", exit_code)

        return exit_code

    except Exception as e:
        logger.error("应用启动失败: %s", e, exc_info=True)
        # 打印错误信息
        print(f"错误: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())