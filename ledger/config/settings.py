import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class Config:
    """配置管理类"""

    # 数据库配置
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'ledger/data/transactions.json')
    DATA_FORMAT = os.getenv('DATA_FORMAT', 'json')

    # 默认设置
    DEFAULT_CURRENCY = os.getenv('DEFAULT_CURRENCY', 'CNY')
    DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'Asia/Shanghai')

    # 数据备份
    BACKUP_ENABLED = os.getenv('BACKUP_ENABLED', 'true').lower() == 'true'
    BACKUP_INTERVAL_DAYS = int(os.getenv('BACKUP_INTERVAL_DAYS', '7'))
    BACKUP_PATH = os.getenv('BACKUP_PATH', 'ledger/backups/')

    # 日志配置
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'ledger/logs/ledger.log')

    # AI配置
    AI_MODEL_PATH = os.getenv('AI_MODEL_PATH', 'ledger/models/')
    AI_ENABLED = os.getenv('AI_ENABLED', 'false').lower() == 'true'
    # AI 自动打标签开关（默认开启规则标签，LLM 参与可选）
    AI_AUTO_TAG = os.getenv('AI_AUTO_TAG', 'true').lower() == 'true'
    AI_AUTO_TAG_WITH_LLM = os.getenv('AI_AUTO_TAG_WITH_LLM', 'false').lower() == 'true'
    OPENAI_BASE_URL = os.getenv('OPENAI_BASE_URL', '')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', '')

    @classmethod
    def ensure_directories(cls):
        """确保必要的目录存在"""
        directories = [
            os.path.dirname(cls.DATABASE_PATH),
            cls.BACKUP_PATH,
            os.path.dirname(cls.LOG_FILE),
            cls.AI_MODEL_PATH
        ]
        for directory in directories:
            os.makedirs(directory, exist_ok=True)