"""
Interpretation Layer: Gap을 문제로 정의하고 해석하는 계층
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
            gap_str = json.dumps(gap, ensure_ascii=False, indent=2)
            
            prompt = f"""다음 Gap을 분석하여 문제로 정의하고, 원인(Cause)과 영향(Impact)을 분석해주세요.

## Gap 정보:
{gap_str}

## 요청사항:
1. 이 Gap을 명확한 문제 이름으로 정의하세요
2. 문제의 원인(Cause)을 분석하세요
3. 이 문제를 해결하지 않을 경우의 영향(Impact)을 예측하세요

다음 JSON 형식으로 응답해주세요:
{{
    "id": "problem_{gap.get('id', 'unknown')}",
    "gap_id": "{gap.get('id', 'unknown')}",
    "name": "문제 이름 (한 줄)",
    "description": "문제 상세 설명",
    "cause": "원인 분석",
    "impact": "영향 분석",
    "severity": "{gap.get('severity', 'medium')}",
    "affected_items": {json.dumps(gap.get('affected_items', []))}
}}

JSON만 반환하고 다른 설명은 포함하지 마세요."""

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
            return problem
            
        except Exception as e:
            print(f"Claude API 호출 실패, 폴백 로직 사용: {e}")
    
    # 폴백: 하드코딩된 템플릿 사용
    gap_type = gap.get("type", "unknown")
    
    problem_templates = {
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
    }
    
    template = problem_templates.get(gap_type, {
        "name": "알 수 없는 문제",
        "description": gap.get("description", ""),
        "cause": "원인 분석 필요",
        "impact": "영향 분석 필요"
    })
    
    return {
        "id": f"problem_{gap['id']}",
        "gap_id": gap["id"],
        "name": template["name"],
        "description": template["description"],
        "cause": template["cause"],
        "impact": template["impact"],
        "severity": gap.get("severity", "medium"),
        "affected_items": gap.get("affected_items", [])
    }


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

