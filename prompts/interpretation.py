"""
Interpretation Layer 프롬프트 템플릿
"""

INTERPRETATION_PROMPT_TEMPLATE = """다음 Gap을 분석하여 문제로 정의하고, 원인(Cause)과 영향(Impact)을 분석해주세요.

## Gap 정보:
{gap_str}

## 요청사항:
1. 이 Gap을 명확한 문제 이름으로 정의하세요
2. 문제의 원인(Cause)을 분석하세요
3. 이 문제를 해결하지 않을 경우의 영향(Impact)을 예측하세요
4. 도메인 정보를 포함하세요

다음 JSON 형식으로 응답해주세요:
{{
    "id": "problem_{gap_id}",
    "gap_id": "{gap_id}",
    "domain": "도메인",
    "name": "문제 이름 (한 줄)",
    "description": "문제 상세 설명",
    "cause": "원인 분석",
    "impact": "영향 분석",
    "severity": "{severity}",
    "affected_items": {affected_items_json}
}}

JSON만 반환하고 다른 설명은 포함하지 마세요."""


def format_interpretation_prompt(gap: dict) -> str:
    """
    Interpretation 프롬프트를 포맷팅합니다.
    
    Args:
        gap: Gap 딕셔너리
        
    Returns:
        포맷팅된 프롬프트 문자열
    """
    import json
    gap_str = json.dumps(gap, ensure_ascii=False, indent=2)
    gap_id = gap.get("id", "unknown")
    severity = gap.get("severity", "medium")
    affected_items = gap.get("affected_items", [])
    affected_items_json = json.dumps(affected_items, ensure_ascii=False)
    
    return INTERPRETATION_PROMPT_TEMPLATE.format(
        gap_str=gap_str,
        gap_id=gap_id,
        severity=severity,
        affected_items_json=affected_items_json
    )

