"""SymptomCollectorAgent — 引导问诊 Agent（纯规则引擎，无 LLM 依赖）

基于当前已知症状生成追问问题，引导用户补充更多信息，
支持多轮问答，自动判断信息充分性并决定下一步动作。
"""

from __future__ import annotations

import uuid
from typing import Any


class SymptomCollectorAgent:
    """引导问诊 Agent — 基于已知症状生成追问问题"""

    # ------------------------------------------------------------------
    # 症状 → 类别 映射关键词
    # ------------------------------------------------------------------
    _DIGESTIVE_KWS = {"呕吐", "腹泻", "软便", "拒食", "食欲下降", "吐毛球"}
    _RESPIRATORY_KWS = {"打喷嚏", "咳嗽", "流鼻涕", "呼吸困难", "鼻塞"}
    _URINARY_KWS = {"尿频", "尿血", "排尿困难", "乱尿", "尿少"}
    _SKIN_KWS = {"掉毛", "抓挠", "红疹", "皮屑", "流泪", "耳垢"}
    _BEHAVIOR_KWS = {"行为问题", "踩奶", "躲藏", "攻击性", "过度舔毛", "叫唤"}

    def __init__(self):
        # 问题模板库 — 按症状类别分类
        self.question_templates: dict[str, list[dict[str, Any]]] = {
            "消化系统": [
                {
                    "id": "digestive_1",
                    "question": "症状持续多久了？",
                    "type": "choice",
                    "options": ["不到1天", "1-3天", "3-7天", "超过1周"],
                },
                {
                    "id": "digestive_2",
                    "question": "最近饮食有变化吗？",
                    "type": "choice",
                    "options": ["换了新粮", "吃了零食/人食", "饮食正常", "不确定"],
                },
                {
                    "id": "digestive_3",
                    "question": "有没有接触其他生病的猫？",
                    "type": "yes_no",
                    "options": [],
                },
                {
                    "id": "digestive_4",
                    "question": "大便的形状和颜色？",
                    "type": "choice",
                    "options": ["成形正常", "软便", "水样", "带血", "黑色"],
                },
                {
                    "id": "digestive_5",
                    "question": "呕吐物是什么？",
                    "type": "choice",
                    "options": ["食物", "黄绿色液体", "白色泡沫", "带血", "毛球"],
                },
            ],
            "呼吸系统": [
                {
                    "id": "respiratory_1",
                    "question": "症状是突然开始的还是逐渐加重的？",
                    "type": "choice",
                    "options": ["突然", "逐渐"],
                },
                {
                    "id": "respiratory_2",
                    "question": "家里有没有使用新清洁产品或香水？",
                    "type": "yes_no",
                    "options": [],
                },
                {
                    "id": "respiratory_3",
                    "question": "猫咪精神状态如何？",
                    "type": "choice",
                    "options": ["活泼如常", "比平时安静", "明显萎靡"],
                },
                {
                    "id": "respiratory_4",
                    "question": "有没有发烧？",
                    "type": "yes_no",
                    "options": [],
                },
            ],
            "泌尿系统": [
                {
                    "id": "urinary_1",
                    "question": "猫咪多久去一次猫砂盆？",
                    "type": "choice",
                    "options": ["正常", "比以前频繁", "很少去", "一直在尝试"],
                },
                {
                    "id": "urinary_2",
                    "question": "尿的颜色？",
                    "type": "choice",
                    "options": ["正常黄色", "很黄", "带血/粉红", "浑浊"],
                },
                {
                    "id": "urinary_3",
                    "question": "排尿时有痛苦表现吗？（如叫唤、蹲很久）",
                    "type": "yes_no",
                    "options": [],
                },
            ],
            "皮肤/毛发": [
                {
                    "id": "skin_1",
                    "question": "症状出现在身体哪个部位？",
                    "type": "choice",
                    "options": ["全身", "头部/耳朵", "背部", "腹部", "四肢"],
                },
                {
                    "id": "skin_2",
                    "question": "最近有没有驱虫？",
                    "type": "choice",
                    "options": ["1月内", "1-3月", "超过3月", "不确定"],
                },
                {
                    "id": "skin_3",
                    "question": "家里是否新添植物/地毯/洗涤剂？",
                    "type": "yes_no",
                    "options": [],
                },
            ],
            "行为/精神": [
                {
                    "id": "behavior_1",
                    "question": "这种情况持续多久了？",
                    "type": "choice",
                    "options": ["不到1周", "1-4周", "1-3月", "超过3月"],
                },
                {
                    "id": "behavior_2",
                    "question": "家里最近有变化吗？",
                    "type": "choice",
                    "options": ["搬家/装修", "新宠物", "新家人", "无变化"],
                },
                {
                    "id": "behavior_3",
                    "question": "猫咪平时独处时间多吗？",
                    "type": "choice",
                    "options": ["很少独处", "每天几小时", "白天基本独处", "全天独处"],
                },
            ],
            "通用": [
                {
                    "id": "general_1",
                    "question": "猫咪最近体重有变化吗？",
                    "type": "choice",
                    "options": ["没变化", "变轻了", "变重了", "不清楚"],
                },
                {
                    "id": "general_2",
                    "question": "有没有按时打疫苗和驱虫？",
                    "type": "yes_no",
                    "options": [],
                },
                {
                    "id": "general_3",
                    "question": "猫咪今年多大了？",
                    "type": "text",
                    "options": [],
                },
            ],
        }

        self.max_rounds = 3

    # ------------------------------------------------------------------
    # 公共接口
    # ------------------------------------------------------------------
    def collect(
        self,
        current_symptoms: list[str],
        known_info: dict | None = None,
        round_num: int = 1,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        """
        输入:
          - current_symptoms: list[str], 当前已知的症状关键词列表
          - known_info: dict, 已收集的信息（上一轮答案）
          - round_num: int, 当前轮次（1-N）
          - session_id: str, 会话ID（可传 None 时自动生成 UUID）
        输出:
          dict: {
            "session_id": str,
            "round_num": int,
            "questions": list[dict],
            "collected_summary": str,
            "is_sufficient": bool,
            "next_action": "continue_collecting" | "ready_for_diagnosis" | "needs_vitals"
          }
        """
        known_info = known_info or {}
        if session_id is None:
            session_id = str(uuid.uuid4())

        # 1. 分类症状
        categories = self._classify_symptoms(current_symptoms)

        # 2. 选择本轮问题
        questions = self._select_questions(categories, round_num, known_info)

        # 3. 生成摘要
        collected_summary = self._generate_summary(known_info)

        # 4. 判断充分性
        is_sufficient, next_action = self._check_sufficiency(known_info, round_num, current_symptoms)

        return {
            "session_id": session_id,
            "round_num": round_num,
            "questions": questions,
            "collected_summary": collected_summary,
            "is_sufficient": is_sufficient,
            "next_action": next_action,
        }

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    def _classify_symptoms(self, symptoms: list[str]) -> list[str]:
        """根据症状关键词返回匹配的类别列表"""
        matched: set[str] = set()
        for s in symptoms:
            if s in self._DIGESTIVE_KWS:
                matched.add("消化系统")
            if s in self._RESPIRATORY_KWS:
                matched.add("呼吸系统")
            if s in self._URINARY_KWS:
                matched.add("泌尿系统")
            if s in self._SKIN_KWS:
                matched.add("皮肤/毛发")
            if s in self._BEHAVIOR_KWS:
                matched.add("行为/精神")
        # 如果没有任何特定类别匹配，也加入通用类别
        if not matched:
            matched.add("通用")
        # 通用问题始终追加（每轮可选1-2个）
        matched.add("通用")
        return list(matched)

    def _select_questions(
        self,
        categories: list[str],
        round_num: int,
        known_info: dict,
    ) -> list[dict[str, Any]]:
        """从匹配类别中选择本轮要问的问题（每轮最多 3 个）"""
        questions: list[dict[str, Any]] = []
        known_ids = {k for k in known_info.keys() if k.startswith("q_")}

        # 按轮次取问题
        if round_num == 1:
            # Round 1: 每个匹配类别取前 2 个问题
            for cat in categories:
                if cat == "通用":
                    continue
                templates = self.question_templates.get(cat, [])
                for q in templates[:2]:
                    if q["id"] not in known_ids:
                        questions.append(dict(q))
        elif round_num == 2:
            # Round 2: 取每个类别接下来的 1-2 个问题
            for cat in categories:
                if cat == "通用":
                    continue
                templates = self.question_templates.get(cat, [])
                for q in templates[2:4]:
                    if q["id"] not in known_ids:
                        questions.append(dict(q))
        else:
            # Round 3+: 只取通用问题或追问关键缺失信息
            pass

        # 如果问题不足 3 个，用通用问题补足
        if len(questions) < 3:
            for q in self.question_templates["通用"]:
                if q["id"] not in known_ids:
                    questions.append(dict(q))
                if len(questions) >= 3:
                    break

        # 硬限制最多 3 个
        return questions[:3]

    def _generate_summary(self, known_info: dict) -> str:
        """生成已收集信息的摘要"""
        if not known_info:
            return "暂未收集到详细信息。"

        pieces: list[str] = []
        # 时间
        duration = known_info.get("digestive_1") or known_info.get("behavior_1")
        if duration:
            pieces.append(f"症状持续 {duration}")

        # 饮食
        diet = known_info.get("digestive_2")
        if diet:
            if diet in ("换了新粮", "吃了零食/人食"):
                pieces.append(f"最近{diet}")
            elif diet == "饮食正常":
                pieces.append("饮食正常")

        # 精神状态
        spirit = known_info.get("respiratory_3")
        if spirit:
            if spirit == "活泼如常":
                pieces.append("精神状态尚可")
            elif spirit == "比平时安静":
                pieces.append("精神比平时安静")
            else:
                pieces.append("精神明显萎靡")

        # 发烧
        fever = known_info.get("respiratory_4")
        if fever is not None:
            pieces.append("无发热" if fever in ("否", "no", "No", False, "false") else "有发热")

        # 大小便
        stool = known_info.get("digestive_4")
        if stool and stool != "成形正常":
            pieces.append(f"大便{stool}")

        urine_color = known_info.get("urinary_2")
        if urine_color and urine_color != "正常黄色":
            pieces.append(f"尿液{urine_color}")

        # 其他
        contact = known_info.get("digestive_3")
        if contact is not None:
            pieces.append("接触过病猫" if contact in ("是", "yes", "Yes", True, "true") else "未接触其他病猫")

        if not pieces:
            return "已收集部分信息，但关键细节尚不完整。"
        return "猫咪" + "，".join(pieces) + "。"

    def _check_sufficiency(
        self,
        known_info: dict,
        round_num: int,
        current_symptoms: list[str],
    ) -> tuple[bool, str]:
        """判断信息是否足够，返回 (is_sufficient, next_action)"""
        # 超过最大轮次 → 强制结束
        if round_num >= self.max_rounds:
            return True, "ready_for_diagnosis"

        # 关键维度计数
        key_dimensions = {
            "时间": bool(
                known_info.get("digestive_1") or known_info.get("behavior_1")
            ),
            "饮食": bool(known_info.get("digestive_2")),
            "环境": bool(
                known_info.get("digestive_3")
                or known_info.get("respiratory_2")
                or known_info.get("skin_3")
                or known_info.get("behavior_2")
            ),
            "体征": bool(
                known_info.get("digestive_4")
                or known_info.get("digestive_5")
                or known_info.get("urinary_2")
                or known_info.get("respiratory_4")
            ),
            "精神状态": bool(known_info.get("respiratory_3")),
        }
        covered = sum(1 for v in key_dimensions.values() if v)

        # 有紧急体征 → 直接判定需要 vitals
        urgent_signs = {"尿血", "呼吸困难", "带血", "黑色"}
        has_urgent = any(s in str(known_info.values()) for s in urgent_signs)

        if covered >= 3 or has_urgent:
            # 有体征信息 或 3 轮结束 → ready
            if has_urgent:
                return True, "needs_vitals"
            return True, "ready_for_diagnosis"

        # 信息不够 → 继续收集
        return False, "continue_collecting"


# ------------------------------------------------------------------
# Self-test
# ------------------------------------------------------------------
if __name__ == "__main__":
    agent = SymptomCollectorAgent()

    # 测试：呕吐 + 腹泻
    result = agent.collect(current_symptoms=["呕吐", "腹泻"], round_num=1)
    print(f"Round {result['round_num']}: {len(result['questions'])} questions")
    for q in result["questions"]:
        print(f"  - {q['question']} ({q['type']})")
    print(f"Sufficient: {result['is_sufficient']}, Next: {result['next_action']}")
    print(f"Summary: {result['collected_summary']}")
    print()

    # 测试：第二轮（带入已知信息）
    known = {
        "digestive_1": "2天",
        "digestive_2": "换了新粮",
        "digestive_3": "否",
    }
    result2 = agent.collect(
        current_symptoms=["呕吐", "腹泻"],
        known_info=known,
        round_num=2,
        session_id=result["session_id"],
    )
    print(f"Round {result2['round_num']}: {len(result2['questions'])} questions")
    for q in result2["questions"]:
        print(f"  - {q['question']} ({q['type']})")
    print(f"Sufficient: {result2['is_sufficient']}, Next: {result2['next_action']}")
    print(f"Summary: {result2['collected_summary']}")
