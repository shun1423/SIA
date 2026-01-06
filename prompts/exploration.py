"""
Exploration Layer 프롬프트 템플릿
"""

EXPLORATION_PROMPT_TEMPLATE = """다음 문제를 해결할 수 있는 솔루션 3개를 제안해주세요.

## 문제 정보:
{problem_str}

## 요청사항:
1. 이 문제를 해결할 수 있는 구체적인 솔루션 3개를 제안하세요
2. 각 솔루션의 장점(pros)과 단점(cons)을 명시하세요
3. 구현 복잡도(complexity)를 low, medium, high 중 하나로 평가하세요
4. 각 솔루션에 필요한 도구(required_tools)를 리스트로 제공하세요
5. 각 솔루션의 리스크 레벨(risk_level)을 low, medium, high로 평가하세요

다음 JSON 형식으로 응답해주세요:
[
    {{
        "id": "sol_1",
        "name": "솔루션 이름",
        "description": "솔루션 상세 설명",
        "pros": ["장점1", "장점2", "장점3"],
        "cons": ["단점1", "단점2"],
        "complexity": "low|medium|high",
        "risk_level": "low|medium|high",
        "required_tools": ["도구1", "도구2"]
    }},
    {{
        "id": "sol_2",
        "name": "솔루션 이름",
        "description": "솔루션 상세 설명",
        "pros": ["장점1", "장점2"],
        "cons": ["단점1", "단점2"],
        "complexity": "low|medium|high",
        "risk_level": "low|medium|high",
        "required_tools": ["도구1", "도구2"]
    }},
    {{
        "id": "sol_3",
        "name": "솔루션 이름",
        "description": "솔루션 상세 설명",
        "pros": ["장점1", "장점2"],
        "cons": ["단점1", "단점2"],
        "complexity": "low|medium|high",
        "risk_level": "low|medium|high",
        "required_tools": ["도구1", "도구2"]
    }}
]

JSON만 반환하고 다른 설명은 포함하지 마세요."""


def format_exploration_prompt(problem: dict) -> str:
    """
    Exploration 프롬프트를 포맷팅합니다.
    
    Args:
        problem: 문제 딕셔너리
        
    Returns:
        포맷팅된 프롬프트 문자열
    """
    import json
    problem_str = json.dumps(problem, ensure_ascii=False, indent=2)
    
    return EXPLORATION_PROMPT_TEMPLATE.format(problem_str=problem_str)

