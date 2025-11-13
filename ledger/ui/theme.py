"""
主题配置 - 统一的颜色、字体、间距常量
"""

from PyQt5.QtGui import QColor, QFont


class Theme:
    """应用主题配置"""
    
    # 颜色方案
    PRIMARY = QColor(25, 118, 210)  # 主色调 - 蓝色
    PRIMARY_HOVER = QColor(21, 101, 192)
    PRIMARY_PRESSED = QColor(13, 71, 161)
    
    SUCCESS = QColor(76, 175, 80)  # 成功 - 绿色
    SUCCESS_LIGHT = QColor(129, 199, 132)
    
    WARNING = QColor(255, 152, 0)  # 警告 - 橙色
    WARNING_LIGHT = QColor(255, 183, 77)
    
    ERROR = QColor(244, 67, 54)  # 错误 - 红色
    ERROR_LIGHT = QColor(239, 83, 80)
    
    BACKGROUND = QColor(250, 250, 250)
    SURFACE = QColor(255, 255, 255)
    
    TEXT_PRIMARY = QColor(33, 33, 33)
    TEXT_SECONDARY = QColor(117, 117, 117)
    TEXT_DISABLED = QColor(189, 189, 189)
    
    BORDER = QColor(224, 224, 224)
    BORDER_HOVER = QColor(189, 189, 189)
    DIVIDER = QColor(238, 238, 238)
    
    # 字体大小
    FONT_XLARGE = 40
    FONT_LARGE = 24
    FONT_TITLE = 18
    FONT_SUBTITLE = 16
    FONT_BODY = 14
    FONT_CAPTION = 12
    FONT_SMALL = 11
    
    # 间距
    SPACING_XLARGE = 32
    SPACING_LARGE = 24
    SPACING_MEDIUM = 16
    SPACING_SMALL = 12
    SPACING_XSMALL = 8
    
    # 圆角
    RADIUS_LARGE = 12
    RADIUS_MEDIUM = 8
    RADIUS_SMALL = 6
    
    # 阴影
    SHADOW_LIGHT = "0 2px 4px rgba(0, 0, 0, 0.1)"
    SHADOW_MEDIUM = "0 4px 8px rgba(0, 0, 0, 0.12)"
    SHADOW_HEAVY = "0 8px 16px rgba(0, 0, 0, 0.16)"
    
    @staticmethod
    def font(size: int, bold: bool = False, family: str = "Microsoft YaHei UI") -> QFont:
        """创建字体"""
        f = QFont(family)
        f.setPointSize(size)
        f.setBold(bold)
        return f
    
    @staticmethod
    def color_to_str(color: QColor) -> str:
        """QColor转字符串"""
        return f"rgb({color.red()}, {color.green()}, {color.blue()})"
