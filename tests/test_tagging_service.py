import pytest
from unittest.mock import MagicMock, patch
from ledger.services.tagging_service import TaggingService
from ledger.config import Config

@pytest.fixture
def tagging_service():
    return TaggingService()

def test_suggest_tags_by_keywords(tagging_service):
    # 1. 餐饮关键词
    assert "餐饮" in tagging_service.suggest_tags("美团外卖")
    # 2. 住房关键词
    assert "住房" in tagging_service.suggest_tags("交房租")
    # 3. 水电煤关键词
    assert "水电煤" in tagging_service.suggest_tags("缴电费")
    # 4. 出行关键词
    assert "出行" in tagging_service.suggest_tags("打车去公司")
    # 5. 购物关键词
    assert "购物" in tagging_service.suggest_tags("京东买东西")
    # 6. 健康关键词
    assert "健康" in tagging_service.suggest_tags("去健身房")
    # 7. 医疗关键词
    assert "医疗" in tagging_service.suggest_tags("买感冒药")
    # 8. 工资关键词
    assert "工资" in tagging_service.suggest_tags("发薪水了")
    # 9. 兼职关键词
    assert "兼职" in tagging_service.suggest_tags("周末兼职")

def test_suggest_tags_by_type(tagging_service):
    # 10. 仅根据类型建议（无关键词匹配）
    assert tagging_service.suggest_tags("其他", "INCOME") == ["收入"]
    # 11. 支出类型无默认标签
    assert tagging_service.suggest_tags("其他", "EXPENSE") == []

def test_suggest_tags_case_insensitive(tagging_service):
    # 12. 大小写不敏感 (针对可能存在的英文关键词)
    # 暂时没有英文关键词，我们模拟一个
    tagging_service.RULES["Test"] = ["Apple"]
    assert "Test" in tagging_service.suggest_tags("apple")

def test_suggest_tags_limit(tagging_service):
    # 13. 标签数量限制为 3
    tags = tagging_service.suggest_tags("美团外卖打车去京东")
    assert len(tags) <= 3

@patch('ledger.config.Config.AI_ENABLED', True)
@patch('ledger.config.Config.AI_AUTO_TAG_WITH_LLM', True)
@patch('openai.OpenAI')
def test_suggest_tags_with_llm(mock_openai, tagging_service):
    # 14. Mock LLM 返回
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_resp = MagicMock()
    mock_resp.choices = [MagicMock(message=MagicMock(content="美食, 快乐"))]
    mock_client.chat.completions.create.return_value = mock_resp

    tags = tagging_service.suggest_tags("吃大餐")
    assert "美食" in tags
    assert "快乐" in tags

def test_suggest_tags_empty_description(tagging_service):
    # 15. 空描述处理
    assert tagging_service.suggest_tags(None) == []
    assert tagging_service.suggest_tags("") == []
