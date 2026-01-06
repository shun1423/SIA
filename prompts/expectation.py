"""
Expectation Layer 프롬프트 템플릿
"""

EXPECTATION_PROMPT_TEMPLATE = """이 사용자의 World Model과 현재 상황을 분석하여 {domain_name} 도메인의 이상적 상태를 생성해주세요.

## World Model:
{world_model_str}

## 현재 상황:
{context_str}

## 도메인: {domain}

## 요청사항:
1. World Model의 Abstract Goals, Preferences, Patterns를 고려하세요
2. 현재 시간과 요일을 반영하세요
3. {domain_name} 도메인에 대한 이상적 상태를 JSON 형식으로 반환하세요
4. 도메인별 특성을 고려하여 적절한 이상적 상태를 생성하세요:
   - email: 이메일 관리, 응답 시간, 중요 메일 가시성
   - github: PR 리뷰 시간, 코드 품질, 개발 프로세스
   - health: 수면 패턴, 운동 습관, 건강 지표

다음 JSON 형식으로 응답해주세요:
{{
    "domain": "{domain}",
    "context": {context_str},
    "ideal_states": [
        {{
            "id": "ideal_1",
            "domain": "{domain}",
            "description": "이상적 상태 설명",
            "criterion": "기준",
            "target_value": "목표값",
            "priority": "high|medium|low"
        }}
    ],
    "expectations": [
        {{
            "id": "exp_1",
            "description": "기대 상태 설명",
            "criterion": "기준",
            "target_value": "목표값",
            "priority": "high|medium|low"
        }}
    ]
}}

JSON만 반환하고 다른 설명은 포함하지 마세요."""


def format_expectation_prompt(
    world_model: dict,
    context: dict,
    domain: str = "email"
) -> str:
    """
    Expectation 프롬프트를 포맷팅합니다.
    
    Args:
        world_model: World Model 딕셔너리
        context: 현재 맥락 딕셔너리
        domain: 도메인 ("email", "github", "health", "finance")
        
    Returns:
        포맷팅된 프롬프트 문자열
    """
    import json
    world_model_str = json.dumps(world_model, ensure_ascii=False, indent=2)
    context_str = json.dumps(context, ensure_ascii=False, indent=2)
    
    # 도메인별 이름 매핑
    domain_names = {
        "email": "이메일 관리",
        "github": "GitHub 개발 프로세스",
        "health": "건강 관리",
        "finance": "재정 관리"
    }
    domain_name = domain_names.get(domain, domain)
    
    return EXPECTATION_PROMPT_TEMPLATE.format(
        world_model_str=world_model_str,
        context_str=context_str,
        domain=domain,
        domain_name=domain_name
    )

