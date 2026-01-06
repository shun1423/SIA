"""
Comparison Layer 프롬프트 템플릿
"""

COMPARISON_PROMPT_TEMPLATE = """현재 상태와 이상적 상태를 비교하여 Gap(차이)을 찾아주세요.

## 현재 상태:
{current_state_str}

## 이상적 상태 (Expectation):
{expectation_str}

## 요청사항:
1. 현재 상태와 이상적 상태를 비교하여 차이점(Gap)을 찾으세요
2. 각 Gap의 중요도(severity)를 high, medium, low로 평가하세요
3. Gap이 발견되지 않으면 빈 리스트를 반환하세요
4. 각 Gap에 다음 정보를 포함하세요:
   - type: gap 타입 (예: visibility, response_time, priority 등)
   - domain: 도메인 (예: email, calendar, task 등)
   - evidence: 증거 데이터 (현재값, 기대값, 추세 등)

다음 JSON 형식으로 응답해주세요:
[
    {{
        "id": "gap_1",
        "type": "gap 타입 (예: visibility, response_time, priority 등)",
        "domain": "도메인",
        "description": "Gap 설명",
        "severity": "high|medium|low",
        "current": "현재 상태 설명",
        "expected": "기대 상태 설명",
        "affected_items": ["영향받는 항목 ID 리스트"],
        "evidence": {{
            "current_value": "현재값",
            "expected_value": "기대값",
            "trend": "increasing|decreasing|stable",
            "recurrence_count": 0
        }}
    }}
]

JSON만 반환하고 다른 설명은 포함하지 마세요."""


def format_comparison_prompt(
    current_state: dict,
    expectation: dict
) -> str:
    """
    Comparison 프롬프트를 포맷팅합니다.
    
    Args:
        current_state: 현재 상태 딕셔너리
        expectation: 기대 상태 딕셔너리
        
    Returns:
        포맷팅된 프롬프트 문자열
    """
    import json
    current_state_str = json.dumps(current_state, ensure_ascii=False, indent=2)
    expectation_str = json.dumps(expectation, ensure_ascii=False, indent=2)
    
    return COMPARISON_PROMPT_TEMPLATE.format(
        current_state_str=current_state_str,
        expectation_str=expectation_str
    )

