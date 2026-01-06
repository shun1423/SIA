"""
Expectation Layer: World Model을 기반으로 이상적인 상태를 생성하는 계층
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
from prompts.expectation import format_expectation_prompt


def load_world_model(data_path: str = "data/world_model.json") -> Dict[str, Any]:
    """
    World Model 데이터를 로드합니다.
    
    Args:
        data_path: World Model 파일 경로
        
    Returns:
        World Model 딕셔너리
    """
    file_path = Path(data_path)
    if not file_path.exists():
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _init_anthropic_client() -> Optional[Anthropic]:
    """Anthropic 클라이언트를 초기화합니다."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def generate_expectation(
    world_model: Dict[str, Any] = None,
    current_context: Dict[str, Any] = None,
    domain: str = "email",
    anthropic_client: Optional[Anthropic] = None
) -> Dict[str, Any]:
    """
    현재 맥락에서 이상적인 상태를 생성합니다.
    v3.2 업데이트: 다양한 도메인 지원
    Claude API를 사용하여 World Model과 현재 상황을 분석하여 이상적 상태를 생성합니다.
    
    Args:
        world_model: World Model 데이터
        current_context: 현재 맥락 (시간, 요일 등)
        domain: 도메인 ("email", "github", "health", "finance")
        anthropic_client: Anthropic 클라이언트 (None이면 자동 초기화)
        
    Returns:
        기대 상태 딕셔너리
    """
    if world_model is None:
        world_model = load_world_model()
    
    if current_context is None:
        from datetime import datetime
        now = datetime.now()
        current_context = {
            "day": now.strftime("%A").lower(),
            "time": now.strftime("%H:%M"),
            "timestamp": now.isoformat()
        }
    
    # Anthropic 클라이언트 초기화
    if anthropic_client is None:
        anthropic_client = _init_anthropic_client()
    
    # Claude API를 사용하여 이상적 상태 생성
    if anthropic_client:
        try:
            # 프롬프트 템플릿 사용 (도메인 정보 포함)
            prompt = format_expectation_prompt(world_model, current_context, domain=domain)

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
            
            # JSON 추출 (마크다운 코드 블록 제거)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            expectation = json.loads(response_text)
            return expectation
            
        except Exception as e:
            # API 호출 실패 시 폴백: 기존 로직 사용
            print(f"Claude API 호출 실패, 폴백 로직 사용: {e}")
    
    # 폴백: World Model의 Ideal States를 기반으로 생성
    ideal_states = world_model.get("ideal_states", [])
    relevant_ideals = [
        ideal for ideal in ideal_states
        if ideal.get("domain") == domain
    ]
    
    # 도메인별 기본 기대 상태 (ideal_states가 없는 경우)
    if not relevant_ideals:
        relevant_ideals = _get_default_ideal_states(domain)
    
    return {
        "domain": domain,
        "context": current_context,
        "ideal_states": relevant_ideals,
        "expectations": [
            {
                "id": f"exp_{i}",
                "description": ideal.get("description", ""),
                "criterion": ideal.get("criterion", ""),
                "target_value": ideal.get("target_value"),
                "priority": ideal.get("priority", "medium")
            }
            for i, ideal in enumerate(relevant_ideals)
        ]
    }


def _get_default_ideal_states(domain: str) -> List[Dict[str, Any]]:
    """
    도메인별 기본 이상적 상태를 반환합니다.
    
    Args:
        domain: 도메인
        
    Returns:
        이상적 상태 리스트
    """
    if domain == "email":
        return [
            {
                "id": "ideal_email_1",
                "domain": "email",
                "condition": "important_email_received",
                "criterion": "response_time_minutes",
                "target_value": 30,
                "description": "중요 메일은 30분 내 확인",
                "priority": "high"
            },
            {
                "id": "ideal_email_2",
                "domain": "email",
                "condition": "inbox_state",
                "criterion": "important_emails_visible",
                "target_value": True,
                "description": "중요 메일이 상단에 보여야 함",
                "priority": "medium"
            }
        ]
    elif domain == "github" or domain == "개발":
        return [
            {
                "id": "ideal_github_1",
                "domain": "github",
                "condition": "pr_created",
                "criterion": "review_time_hours",
                "target_value": 24,
                "description": "PR은 24시간 내 리뷰",
                "priority": "high"
            },
            {
                "id": "ideal_github_2",
                "domain": "github",
                "condition": "release_pr",
                "criterion": "review_time_hours",
                "target_value": 12,
                "description": "릴리스 PR은 12시간 내 리뷰",
                "priority": "high"
            }
        ]
    elif domain == "health" or domain == "건강":
        return [
            {
                "id": "ideal_health_1",
                "domain": "health",
                "condition": "sleep_pattern",
                "criterion": "sleep_duration_hours",
                "target_value": 7,
                "description": "평균 수면 시간 7시간 이상",
                "priority": "high"
            },
            {
                "id": "ideal_health_2",
                "domain": "health",
                "condition": "sleep_pattern",
                "criterion": "bedtime_variance_hours",
                "target_value": 1,
                "description": "취침 시간 편차 1시간 이내",
                "priority": "medium"
            }
        ]
    elif domain == "finance" or domain == "재정":
        return [
            {
                "id": "ideal_finance_1",
                "domain": "finance",
                "condition": "category_spending",
                "criterion": "weekly_spending_limit",
                "target_value": 50000,
                "description": "주간 배달앱 지출 5만원 이하",
                "priority": "medium"
            },
            {
                "id": "ideal_finance_2",
                "domain": "finance",
                "condition": "subscription_usage",
                "criterion": "unused_subscription_days",
                "target_value": 90,
                "description": "90일 미사용 구독 서비스 감지",
                "priority": "low"
            }
        ]
    else:
        return []

