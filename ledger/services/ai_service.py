"""AI 指令解析与执行服务。

支持通过 OpenAI 兼容接口解析自然语言为账单操作（新增/修改/删除）。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
import re

from ledger.config import Config
from ledger.models import Transaction
from .transaction_service import TransactionService
from .tagging_service import TaggingService

logger = logging.getLogger(__name__)


@dataclass
class AIOperation:
    op_type: str  # ADD | UPDATE | DELETE
    amount: Optional[float] = None
    transaction_type: Optional[str] = None  # INCOME | EXPENSE
    date: Optional[str] = None  # YYYY-MM-DD
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    transaction_id: Optional[str] = None
    filter: Optional[Dict[str, Any]] = None


class AICommandService:
    """封装与 LLM 的交互与结果执行。"""

    SYSTEM_PROMPT = (
        "你是一个财务助手，负责把中文自然语言转换成严格 JSON 指令，且只输出 JSON，不要包含任何解释或代码块标记。\n"
        "支持的操作：ADD(新增)、UPDATE(修改)、DELETE(删除)。\n"
        "字段规范：\n"
        "- type: 字符串，取值 'ADD' | 'UPDATE' | 'DELETE'\n"
        "- amount: 数字，单位元；不要带货币符号或中文单位\n"
        "- transaction_type: 'INCOME' | 'EXPENSE'（中文‘收入’/‘支出’需转换）\n"
        "- date: 'YYYY-MM-DD'；出现‘今天/昨天/上周三/本月’等相对日期时，必须先换算成具体日期\n"
        "- description: 字符串\n"
        "- tags: 字符串数组，可为空\n"
        "- transaction_id: 如直接指定 ID\n"
        "- filter: 对象，用于 UPDATE/DELETE 的匹配；支持键：date、transaction_type、description_contains、tags（数组，需全部包含）\n"
        "输出 JSON 结构：{\"operations\": [{ ... }]}，不要输出其他任何内容。\n"
    )

    FEW_SHOT = (
        "示例：\n"
        "用户：今天中午吃饭花了36.5元，标签餐饮；把昨天的星巴克支出改为45元；删除上周三的兼职收入。\n"
        "输出：{\n"
        "  \"operations\": [\n"
        "    {\n"
        "      \"type\": \"ADD\", \"amount\": 36.5, \"transaction_type\": \"EXPENSE\",\n"
        "      \"date\": \"<用具体日期替换>\", \"description\": \"午餐-餐饮\", \"tags\": [\"餐饮\"]\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"UPDATE\", \"filter\": {\n"
        "        \"date\": \"<用具体日期替换>\", \"transaction_type\": \"EXPENSE\", \"description_contains\": \"星巴克\"\n"
        "      }, \"amount\": 45.0\n"
        "    },\n"
        "    {\n"
        "      \"type\": \"DELETE\", \"filter\": {\n"
        "        \"date\": \"<用具体日期替换>\", \"transaction_type\": \"INCOME\", \"description_contains\": \"兼职\"\n"
        "      }\n"
        "    }\n"
        "  ]\n"
        "}\n"
    )

    def __init__(self, ts: TransactionService):
        self.ts = ts
        self.tagger = TaggingService()

    def _ensure_client(self):
        if not Config.AI_ENABLED:
            raise RuntimeError("AI 功能未启用，请在 .env 中设置 AI_ENABLED=true")
        if not (Config.OPENAI_API_KEY and Config.OPENAI_MODEL):
            raise RuntimeError("缺少 OPENAI_API_KEY 或 OPENAI_MODEL 配置")
        try:
            # 延迟导入，避免未配置也报错
            from openai import OpenAI  # type: ignore
        except Exception as exc:  # pylint: disable=broad-except
            raise RuntimeError("openai 依赖未安装，请在 requirements 中安装 openai") from exc

        base_url = Config.OPENAI_BASE_URL or None
        client = OpenAI(api_key=Config.OPENAI_API_KEY, base_url=base_url)
        return client

    def _build_context(self) -> str:
        """构建日期上下文，提供今天的日期与星期，帮助模型解析相对日期。"""
        today = datetime.now()
        weekday_map = {0: "一", 1: "二", 2: "三", 3: "四", 4: "五", 5: "六", 6: "日"}
        return (
            f"今天是 {today.strftime('%Y-%m-%d')} 星期{weekday_map[today.weekday()]}，"
            f"当前时间 {today.strftime('%H:%M')}。请将相对日期换算成具体日期。"
        )

    def call_llm(self, text: str) -> Dict[str, Any]:
        """调用 LLM 并返回解析后的 JSON（dict）。"""
        client = self._ensure_client()

        try:
            resp = client.chat.completions.create(
                model=Config.OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "system", "content": self.FEW_SHOT},
                    {"role": "system", "content": self._build_context()},
                    {"role": "user", "content": text},
                ],
                temperature=0.0,
            )
            content = resp.choices[0].message.content or "{}"
        except Exception as e:  # pylint: disable=broad-except
            logger.error("调用 AI 失败: %s", e)
            raise

        # 解析 JSON（容错：截取首尾大括号）
        try:
            return json.loads(content)
        except Exception:  # pylint: disable=broad-except
            try:
                start = content.find("{")
                end = content.rfind("}") + 1
                return json.loads(content[start:end])
            except Exception as e:  # pylint: disable=broad-except
                logger.error("解析 AI 返回失败: %s", e)
                raise

    # ---------------- 执行逻辑 ----------------
    @staticmethod
    def _parse_date(date_str: Optional[str]) -> datetime:
        if not date_str:
            return datetime.now()
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        # 回退为 now
        return datetime.now()

    @staticmethod
    def _coerce_amount(val: Any) -> float:
        """将多样的数值表达转为 float，例如 '¥36.5' 或 '36.5元'。"""
        if val is None:
            return 0.0
        if isinstance(val, (int, float)):
            return float(val)
        s = str(val)
        m = re.search(r"-?\d+(?:\.\d+)?", s)
        return float(m.group(0)) if m else 0.0

    def _filter_transactions(self, flt: Dict[str, Any]) -> List[Transaction]:
        start = end = None
        desc = flt.get("description_contains")
        ttype = flt.get("transaction_type")
        date_str = flt.get("date")
        if date_str:
            d = self._parse_date(date_str)
            start = datetime.combine(d.date(), datetime.min.time())
            end = datetime.combine(d.date(), datetime.max.time())

        tags = flt.get("tags")
        results = self.ts.search_transactions(
            start_date=start, end_date=end, transaction_type=ttype, description=desc
        )
        if tags:
            results = [t for t in results if set(tags).issubset(set(t.tags))]
        return results

    def execute_operations(self, operations: List[AIOperation]) -> Dict[str, Any]:
        """执行解析得到的操作，返回统计结果。"""
        added: List[str] = []
        updated: List[str] = []
        deleted: List[str] = []

        for op in operations:
            t = op.op_type.upper()
            if t == "ADD":
                # 若未显式提供标签且开启自动打标，则基于描述/类型建议标签
                auto_tags: List[str] = []
                if Config.AI_AUTO_TAG and not (op.tags or []):
                    auto_tags = self.tagger.suggest_tags(
                        op.description or "",
                        self._normalize_type(op.transaction_type),
                    )
                trans = Transaction(
                    amount=self._coerce_amount(op.amount),
                    transaction_type=self._normalize_type(op.transaction_type),
                    description=op.description or "",
                    date=self._parse_date(op.date),
                    tags=(op.tags or auto_tags),
                )
                self.ts.add_transaction(trans)
                added.append(trans.transaction_id)

            elif t == "UPDATE":
                targets: List[Transaction] = []
                if op.transaction_id:
                    found = self.ts.get_transaction(op.transaction_id)
                    if found:
                        targets = [found]
                elif op.filter:
                    targets = self._filter_transactions(op.filter)

                for trg in targets:
                    kwargs: Dict[str, Any] = {}
                    if op.amount is not None:
                        kwargs["amount"] = self._coerce_amount(op.amount)
                    if op.transaction_type:
                        kwargs["transaction_type"] = self._normalize_type(op.transaction_type)
                    if op.description is not None:
                        kwargs["description"] = op.description
                    if op.tags is not None:
                        kwargs["tags"] = op.tags
                    if op.date is not None:
                        kwargs["date"] = self._parse_date(op.date)
                    # 若未显式提供 tags，且描述发生变化且原先无标签，可尝试自动打标签
                    if (
                        Config.AI_AUTO_TAG
                        and op.tags is None
                        and op.description is not None
                        and not trg.tags
                    ):
                        tx_type = kwargs.get("transaction_type", trg.transaction_type)
                        auto_tags = self.tagger.suggest_tags(op.description or "", tx_type)
                        if auto_tags:
                            kwargs["tags"] = auto_tags
                    if kwargs:
                        self.ts.update_transaction(trg.transaction_id, **kwargs)
                        updated.append(trg.transaction_id)

            elif t == "DELETE":
                targets: List[Transaction] = []
                if op.transaction_id:
                    found = self.ts.get_transaction(op.transaction_id)
                    if found:
                        targets = [found]
                elif op.filter:
                    targets = self._filter_transactions(op.filter)
                for trg in targets:
                    if self.ts.delete_transaction(trg.transaction_id):
                        deleted.append(trg.transaction_id)

        return {"added": added, "updated": updated, "deleted": deleted}

    def parse(self, text: str) -> List[AIOperation]:
        data = self.call_llm(text)
        ops = []
        for item in data.get("operations", []):
            # 兼容不同键名：type/op/action
            raw_type = item.get("type") or item.get("op") or item.get("action") or ""
            tx_type = item.get("transaction_type") or item.get("tx_type") or item.get("kind")
            tx_type = self._normalize_type(tx_type)
            ops.append(
                AIOperation(
                    op_type=str(raw_type).upper(),
                    amount=item.get("amount"),
                    transaction_type=tx_type,
                    date=item.get("date"),
                    description=item.get("description"),
                    tags=item.get("tags"),
                    transaction_id=item.get("transaction_id"),
                    filter=item.get("filter"),
                )
            )
        return ops

    def parse_and_execute(self, text: str) -> Tuple[List[AIOperation], Dict[str, Any]]:
        ops = self.parse(text)
        result = self.execute_operations(ops)
        return ops, result

    # ---------------- 规范化辅助 ----------------
    @staticmethod
    def _normalize_type(val: Optional[str]) -> str:
        if not val:
            return "EXPENSE"
        v = str(val).strip().upper()
        mapping = {
            "INCOME": "INCOME",
            "EXPENSE": "EXPENSE",
            "收入": "INCOME",
            "支出": "EXPENSE",
        }
        return mapping.get(v, "INCOME" if v in {"INCOME", "收入"} else "EXPENSE")
