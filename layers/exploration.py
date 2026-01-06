"""
Exploration Layer: 문제에 대한 솔루션을 탐색하는 계층
v3.2 업데이트: 프롬프트 템플릿 사용
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

# 환경 변수 로드
load_dotenv()

# 프롬프트 템플릿 임포트
import sys
sys.path.append(str(Path(__file__).parent.parent))
from prompts.exploration import format_exploration_prompt


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
            # 프롬프트 템플릿 사용
            prompt = format_exploration_prompt(problem)

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
    
    # 폴백: 도메인별 템플릿 사용
    problem_name = problem.get("name", "")
    domain = problem.get("domain", "email")
    
    # 도메인별 솔루션 템플릿
    solution_templates = {
        "email": {
            "중요 메일 가시성 문제": [
                {
                    "id": "sol_1",
                    "name": "자동 분류 시스템",
                    "description": "발신자와 키워드 패턴을 분석하여 중요 메일을 자동으로 분류하고 상단에 표시",
                    "pros": ["근본적 해결", "한 번 설정하면 지속 작동", "알림 피로도 없음"],
                    "cons": ["초기 설정 필요", "분류 정확도 학습 시간 필요"],
                    "complexity": "medium",
                    "required_tools": ["email_reader", "classifier", "label_applier"],
                    "risk_level": "low"
                },
                {
                    "id": "sol_2",
                    "name": "중요 메일 실시간 알림",
                    "description": "중요 메일이 도착하면 즉시 알림을 보내어 확인하도록 유도",
                    "pros": ["즉시 적용 가능", "구현 간단"],
                    "cons": ["알림 피로도 증가 가능", "근본적 해결 아님"],
                    "complexity": "low",
                    "required_tools": ["email_reader", "notification"],
                    "risk_level": "low"
                },
                {
                    "id": "sol_3",
                    "name": "아침 요약 리포트",
                    "description": "매일 아침 중요 메일 요약을 자동 생성하여 제공",
                    "pros": ["비침습적", "한눈에 파악 가능"],
                    "cons": ["실시간성 부족", "리포트 생성 시간 필요"],
                    "complexity": "medium",
                    "required_tools": ["email_reader", "summarizer", "report_generator"],
                    "risk_level": "low"
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
                    "required_tools": ["email_reader", "priority_scorer", "sorter"],
                    "risk_level": "low"
                }
            ]
        },
        "github": {
            "PR 리뷰 지연 문제": [
                {
                    "id": "sol_github_1",
                    "name": "PR 리뷰 알림 시스템",
                    "description": "리뷰가 필요한 PR을 자동으로 감지하고 팀에 알림",
                    "pros": ["즉시 적용 가능", "리뷰 지연 방지"],
                    "cons": ["알림 피로도 가능"],
                    "complexity": "low",
                    "required_tools": ["pr_reader", "notifier"],
                    "risk_level": "low"
                },
                {
                    "id": "sol_github_2",
                    "name": "PR 우선순위 자동 분류",
                    "description": "PR의 중요도(릴리스, 핫픽스 등)를 자동으로 판단하여 우선순위 부여",
                    "pros": ["근본적 해결", "리뷰 효율 향상"],
                    "cons": ["우선순위 판단 로직 필요"],
                    "complexity": "medium",
                    "required_tools": ["pr_reader", "reviewer", "priority_scorer"],
                    "risk_level": "low"
                }
            ]
        },
        "health": {
            "수면 부족 문제": [
                {
                    "id": "sol_health_1",
                    "name": "수면 패턴 분석 및 알림",
                    "description": "수면 패턴을 분석하고 목표 시간 미달 시 알림",
                    "pros": ["의식 개선", "건강 관리"],
                    "cons": ["알림 피로도 가능"],
                    "complexity": "low",
                    "required_tools": ["health_reader", "analyzer", "notifier"],
                    "risk_level": "low"
                },
                {
                    "id": "sol_health_2",
                    "name": "수면 목표 추적 시스템",
                    "description": "일일 수면 목표를 설정하고 달성률을 추적",
                    "pros": ["동기 부여", "장기적 개선"],
                    "cons": ["목표 설정 필요"],
                    "complexity": "medium",
                    "required_tools": ["health_reader", "analyzer"],
                    "risk_level": "low"
                }
            ]
        },
        "finance": {
            "과도한 지출 문제": [
                {
                    "id": "sol_finance_1",
                    "name": "지출 한도 알림",
                    "description": "카테고리별 지출이 한도를 초과하면 알림",
                    "pros": ["즉시 적용 가능", "지출 제어"],
                    "cons": ["알림 피로도 가능"],
                    "complexity": "low",
                    "required_tools": ["transaction_reader", "analyzer", "notifier"],
                    "risk_level": "low"
                },
                {
                    "id": "sol_finance_2",
                    "name": "지출 패턴 분석 및 리포트",
                    "description": "주간/월간 지출 패턴을 분석하여 리포트 제공",
                    "pros": ["의식 개선", "장기적 계획"],
                    "cons": ["리포트 생성 시간 필요"],
                    "complexity": "medium",
                    "required_tools": ["transaction_reader", "analyzer", "report_generator"],
                    "risk_level": "low"
                }
            ]
        }
    }
    
    # 도메인별 템플릿에서 찾기
    domain_templates = solution_templates.get(domain, {})
    solutions = domain_templates.get(problem_name, [
        {
            "id": f"sol_default_{domain}",
            "name": f"{domain} 도메인 일반 해결 방안",
            "description": "문제를 분석하여 적절한 해결책을 제시합니다.",
            "pros": ["적용 가능"],
            "cons": ["구체화 필요"],
            "complexity": "medium",
            "required_tools": [],
            "risk_level": "medium"
        }
    ])
    
    # 최대 3개로 제한
    return solutions[:3]

