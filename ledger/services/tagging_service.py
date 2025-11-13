"""规则与可选 LLM 的标签建议服务。

优先使用简单的关键词规则；当配置允许时可调用 LLM 进行补充（默认关闭）。
"""

from __future__ import annotations

from typing import List
from ledger.config import Config


class TaggingService:
    """根据描述/类型建议标签。"""

    # 非穷尽，后续可在 .env 或外部文件扩展
    RULES = {
        "餐饮": ["餐", "午餐", "晚餐", "早餐", "饭", "外卖", "美团", "饿了么", "奶茶", "咖啡", "星巴克"],
        "住房": ["房租", "租金"],
        "水电煤": ["水电", "电费", "水费", "燃气", "煤气"],
        "出行": ["地铁", "公交", "打车", "滴滴", "网约车", "高铁", "火车", "机票"],
        "购物": ["购物", "京东", "淘宝", "拼多多"],
        "健康": ["健身", "运动"],
        "医疗": ["医院", "药"],
        "工资": ["工资", "薪资", "薪水", "发薪"],
        "兼职": ["兼职", "外快"],
    }

    def suggest_tags(self, description: str, transaction_type: str | None = None) -> List[str]:
        desc = (description or "").lower()
        tags: List[str] = []
        for tag, keywords in self.RULES.items():
            for kw in keywords:
                if kw.lower() in desc:
                    tags.append(tag)
                    break
        # 类型导向的标签（仅在未命中规则时补充）
        if not tags and transaction_type:
            if transaction_type.upper() == "INCOME":
                tags = ["收入"]
            else:
                tags = []
        # 可选：调用 LLM 做补充（默认关闭）
        if Config.AI_ENABLED and Config.AI_AUTO_TAG_WITH_LLM:
            try:
                from openai import OpenAI  # type: ignore
                client = OpenAI(api_key=Config.OPENAI_API_KEY, base_url=(Config.OPENAI_BASE_URL or None))
                prompt = (
                    "请基于中文描述为一笔账单生成不超过3个简短标签，只返回以逗号分隔的标签，不要解释。\n"
                    f"描述：{description}\n"
                )
                resp = client.chat.completions.create(
                    model=Config.OPENAI_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                )
                content = (resp.choices[0].message.content or "").strip()
                llm_tags = [t.strip() for t in content.split("，") if t.strip()]
                # 兼容英文逗号
                if len(llm_tags) <= 1:
                    llm_tags = [t.strip() for t in content.split(",") if t.strip()]
                for t in llm_tags:
                    if t and t not in tags:
                        tags.append(t)
            except Exception:  # pylint: disable=broad-except
                # LLM 失败忽略，保留规则标签
                pass
        return tags[:3]
