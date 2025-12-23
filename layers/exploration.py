"""
Exploration Layer: 문제에 대한 솔루션을 탐색하는 계층
"""

import json
import os
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv
from anthropic import Anthropic

# 환경 변수 로드
load_dotenv()


def _init_anthropic_client() -> Optional[Anthropic]:
    """Anthropic 클라이언트를 초기화합니다."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def explore_solutions(
    problem: Dict[str, Any],
    anthropic_client: Optional[Anthropic] = None
) -> List[Dict[str, Any]]:
    """
    문제에 대한 가능한 솔루션들을 탐색합니다.
    Claude API를 사용하여 문제별로 3개의 솔루션을 생성합니다.
    
    Args:
        problem: Interpretation Layer에서 정의한 문제
        anthropic_client: Anthropic 클라이언트 (None이면 자동 초기화)
        
    Returns:
        솔루션 후보 리스트 (3개)
    """
    # Anthropic 클라이언트 초기화
    if anthropic_client is None:
        anthropic_client = _init_anthropic_client()
    
    # Claude API를 사용하여 솔루션 탐색
    if anthropic_client:
        try:
            problem_str = json.dumps(problem, ensure_ascii=False, indent=2)
            
            prompt = f"""다음 문제를 해결할 수 있는 솔루션 3개를 제안해주세요.

## 문제 정보:
{problem_str}

## 요청사항:
1. 이 문제를 해결할 수 있는 구체적인 솔루션 3개를 제안하세요
2. 각 솔루션의 장점(pros)과 단점(cons)을 명시하세요
3. 구현 복잡도(complexity)를 low, medium, high 중 하나로 평가하세요
4. 각 솔루션에 필요한 도구(required_tools)를 리스트로 제공하세요

다음 JSON 형식으로 응답해주세요:
[
    {{
        "id": "sol_1",
        "name": "솔루션 이름",
        "description": "솔루션 상세 설명",
        "pros": ["장점1", "장점2", "장점3"],
        "cons": ["단점1", "단점2"],
        "complexity": "low|medium|high",
        "required_tools": ["도구1", "도구2"]
    }},
    {{
        "id": "sol_2",
        "name": "솔루션 이름",
        "description": "솔루션 상세 설명",
        "pros": ["장점1", "장점2"],
        "cons": ["단점1", "단점2"],
        "complexity": "low|medium|high",
        "required_tools": ["도구1", "도구2"]
    }},
    {{
        "id": "sol_3",
        "name": "솔루션 이름",
        "description": "솔루션 상세 설명",
        "pros": ["장점1", "장점2"],
        "cons": ["단점1", "단점2"],
        "complexity": "low|medium|high",
        "required_tools": ["도구1", "도구2"]
    }}
]

JSON만 반환하고 다른 설명은 포함하지 마세요."""

            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # 응답 파싱
            response_text = response.content[0].text.strip()
            
            # JSON 추출
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            solutions = json.loads(response_text)
            
            # 리스트가 아닌 경우 리스트로 변환
            if not isinstance(solutions, list):
                solutions = [solutions] if solutions else []
            
            # 최대 3개로 제한
            return solutions[:3]
            
        except Exception as e:
            print(f"Claude API 호출 실패, 폴백 로직 사용: {e}")
    
    # 폴백: 하드코딩된 템플릿 사용
    problem_name = problem.get("name", "")
    
    solution_templates = {
        "중요 메일 가시성 문제": [
            {
                "id": "sol_1",
                "name": "자동 분류 시스템",
                "description": "발신자와 키워드 패턴을 분석하여 중요 메일을 자동으로 분류하고 상단에 표시",
                "pros": ["근본적 해결", "한 번 설정하면 지속 작동", "알림 피로도 없음"],
                "cons": ["초기 설정 필요", "분류 정확도 학습 시간 필요"],
                "complexity": "medium",
                "required_tools": ["email_reader", "classifier", "label_applier"]
            },
            {
                "id": "sol_2",
                "name": "중요 메일 실시간 알림",
                "description": "중요 메일이 도착하면 즉시 알림을 보내어 확인하도록 유도",
                "pros": ["즉시 적용 가능", "구현 간단"],
                "cons": ["알림 피로도 증가 가능", "근본적 해결 아님"],
                "complexity": "low",
                "required_tools": ["email_reader", "notification"]
            },
            {
                "id": "sol_3",
                "name": "아침 요약 리포트",
                "description": "매일 아침 중요 메일 요약을 자동 생성하여 제공",
                "pros": ["비침습적", "한눈에 파악 가능"],
                "cons": ["실시간성 부족", "리포트 생성 시간 필요"],
                "complexity": "medium",
                "required_tools": ["email_reader", "summarizer", "report_generator"]
            }
        ],
        "중요 메일 응답 지연 문제": [
            {
                "id": "sol_4",
                "name": "우선순위 기반 정렬",
                "description": "메일함을 우선순위 순으로 자동 정렬하여 중요 메일을 상단에 표시",
                "pros": ["즉시 효과", "사용자 개입 최소"],
                "cons": ["우선순위 판단 로직 필요"],
                "complexity": "medium",
                "required_tools": ["email_reader", "priority_scorer", "sorter"]
            }
        ]
    }
    
    solutions = solution_templates.get(problem_name, [
        {
            "id": "sol_default",
            "name": "일반적인 해결 방안",
            "description": "문제를 분석하여 적절한 해결책을 제시합니다.",
            "pros": ["적용 가능"],
            "cons": ["구체화 필요"],
            "complexity": "medium",
            "required_tools": []
        }
    ])
    
    # 최대 3개로 제한
    return solutions[:3]

