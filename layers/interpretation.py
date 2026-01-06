"""
Interpretation Layer: Gap을 문제로 정의하고 해석하는 계층
v3.2 업데이트: 문제 상태 머신 통합, 프롬프트 템플릿 사용
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

# 환경 변수 로드
load_dotenv()

# 유틸리티 임포트
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.problem_state_machine import ProblemStateMachine, ProblemStatus
from prompts.interpretation import format_interpretation_prompt


def _init_anthropic_client() -> Optional[Anthropic]:
    """Anthropic 클라이언트를 초기화합니다."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def interpret_gap(
    gap: Dict[str, Any],
    anthropic_client: Optional[Anthropic] = None
) -> Dict[str, Any]:
    """
    Gap을 문제로 정의하고 해석합니다.
    Claude API를 사용하여 Gap을 문제로 정의하고 원인과 영향을 분석합니다.
    
    Args:
        gap: Comparison Layer에서 발견한 Gap
        anthropic_client: Anthropic 클라이언트 (None이면 자동 초기화)
        
    Returns:
        문제 정의 딕셔너리
    """
    # Anthropic 클라이언트 초기화
    if anthropic_client is None:
        anthropic_client = _init_anthropic_client()
    
    # Claude API를 사용하여 문제 정의
    if anthropic_client:
        try:
            # 프롬프트 템플릿 사용
            prompt = format_interpretation_prompt(gap)

            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
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
            
            problem = json.loads(response_text)
            
            # 문제 상태 머신 적용: CANDIDATE 상태로 초기화
            problem["status"] = ProblemStatus.CANDIDATE.value
            problem["detected_at"] = json.dumps({"timestamp": "2025-01-15T09:00:00Z"})
            problem["problem_score"] = gap.get("problem_score", 0.5)
            
            return problem
            
        except Exception as e:
            print(f"Claude API 호출 실패, 폴백 로직 사용: {e}")
    
    # 폴백: 도메인별 템플릿 사용
    gap_type = gap.get("type", "unknown")
    domain = gap.get("domain", "email")
    
    # 도메인별 문제 템플릿
    problem_templates = {
        "email": {
            "visibility": {
                "name": "중요 메일 가시성 문제",
                "description": "중요한 업무 메일이 메일함 상단에 보이지 않아 놓칠 위험이 있습니다.",
                "cause": "메일함이 시간순 정렬로 고정되어 있어 우선순위가 반영되지 않음",
                "impact": "중요 메일 응답 지연 → 업무 차질 → 프로젝트 일정 지연 가능성"
            },
            "response_time": {
                "name": "중요 메일 응답 지연 문제",
                "description": "중요 메일이 확인되지 않아 응답이 지연되고 있습니다.",
                "cause": "메일함에 많은 메일이 쌓여 있어 중요 메일을 찾기 어려움",
                "impact": "상사/팀원과의 커뮤니케이션 지연 → 신뢰도 하락"
            }
        },
        "github": {
            "review_delay": {
                "name": "PR 리뷰 지연 문제",
                "description": "리뷰 대기 중인 PR이 48시간 이상 지연되고 있습니다.",
                "cause": "PR 리뷰 프로세스가 체계화되지 않아 리뷰가 누적됨",
                "impact": "코드 병합 지연 → 배포 일정 지연 → 팀 생산성 저하"
            }
        },
        "health": {
            "sleep_deficit": {
                "name": "수면 부족 문제",
                "description": "평균 수면 시간이 권장 시간(7시간)보다 부족합니다.",
                "cause": "업무 스트레스나 불규칙한 생활 패턴으로 인한 수면 부족",
                "impact": "집중력 저하 → 업무 효율 저하 → 건강 악화"
            }
        },
        "finance": {
            "overspending": {
                "name": "과도한 지출 문제",
                "description": "배달앱 지출이 설정한 한도를 초과했습니다.",
                "cause": "편의성 추구로 인한 무의식적 지출 증가",
                "impact": "예산 초과 → 재정 계획 어긋남 → 저축 목표 달성 어려움"
            }
        }
    }
    
    domain_templates = problem_templates.get(domain, {})
    template = domain_templates.get(gap_type, {
        "name": f"{domain} 도메인 문제",
        "description": gap.get("description", ""),
        "cause": "원인 분석 필요",
        "impact": "영향 분석 필요"
    })
    
    problem = {
        "id": f"problem_{gap['id']}",
        "gap_id": gap["id"],
        "domain": gap.get("domain", "email"),
        "name": template["name"],
        "description": template["description"],
        "cause": template["cause"],
        "impact": template["impact"],
        "severity": gap.get("severity", "medium"),
        "affected_items": gap.get("affected_items", []),
        "status": ProblemStatus.CANDIDATE.value,
        "detected_at": "2025-01-15T09:00:00Z",
        "problem_score": gap.get("problem_score", 0.5)
    }
    
    return problem


def interpret_gaps(
    gaps: List[Dict[str, Any]],
    anthropic_client: Optional[Anthropic] = None
) -> List[Dict[str, Any]]:
    """
    여러 Gap을 문제로 해석합니다.
    
    Args:
        gaps: Gap 리스트
        anthropic_client: Anthropic 클라이언트 (None이면 자동 초기화)
        
    Returns:
        문제 정의 리스트
    """
    return [interpret_gap(gap, anthropic_client) for gap in gaps]

