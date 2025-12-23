"""
Comparison Layer: 현재 상태와 이상적 상태를 비교하여 Gap을 찾는 계층
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


def compare_states(
    current_state: Dict[str, Any],
    expectation: Dict[str, Any],
    anthropic_client: Optional[Anthropic] = None
) -> List[Dict[str, Any]]:
    """
    현재 상태와 기대 상태를 비교하여 Gap을 찾습니다.
    Claude API를 사용하여 두 상태를 분석하고 Gap 리스트를 반환합니다.
    
    Args:
        current_state: Sensor Layer에서 수집한 현재 상태
        expectation: Expectation Layer에서 생성한 기대 상태
        anthropic_client: Anthropic 클라이언트 (None이면 자동 초기화)
        
    Returns:
        Gap 리스트 (각 Gap에 중요도 포함)
    """
    # Anthropic 클라이언트 초기화
    if anthropic_client is None:
        anthropic_client = _init_anthropic_client()
    
    # Claude API를 사용하여 Gap 분석
    if anthropic_client:
        try:
            # 프롬프트 구성
            current_state_str = json.dumps(current_state, ensure_ascii=False, indent=2)
            expectation_str = json.dumps(expectation, ensure_ascii=False, indent=2)
            
            prompt = f"""현재 상태와 이상적 상태를 비교하여 Gap(차이)을 찾아주세요.

## 현재 상태:
{current_state_str}

## 이상적 상태 (Expectation):
{expectation_str}

## 요청사항:
1. 현재 상태와 이상적 상태를 비교하여 차이점(Gap)을 찾으세요
2. 각 Gap의 중요도(severity)를 high, medium, low로 평가하세요
3. Gap이 발견되지 않으면 빈 리스트를 반환하세요

다음 JSON 형식으로 응답해주세요:
[
    {{
        "id": "gap_1",
        "type": "gap 타입 (예: visibility, response_time, priority 등)",
        "description": "Gap 설명",
        "severity": "high|medium|low",
        "current": "현재 상태 설명",
        "expected": "기대 상태 설명",
        "affected_items": ["영향받는 항목 ID 리스트"]
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
            
            # JSON 추출 (마크다운 코드 블록 제거)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            gaps = json.loads(response_text)
            
            # 리스트가 아닌 경우 리스트로 변환
            if not isinstance(gaps, list):
                gaps = [gaps] if gaps else []
            
            return gaps
            
        except Exception as e:
            # API 호출 실패 시 폴백: 기존 로직 사용
            print(f"Claude API 호출 실패, 폴백 로직 사용: {e}")
    
    # 폴백: 하드코딩된 Gap 감지 로직
    gaps = []
    
    # 이메일 도메인에 대한 간단한 Gap 감지 로직
    current_emails = current_state.get("data", {}).get("emails", [])
    ideal_states = expectation.get("ideal_states", [])
    
    # 중요 메일 가시성 체크
    important_emails = [
        e for e in current_emails
        if e.get("hidden_priority") == "high"
    ]
    
    # 시간순 정렬로 가정 (실제로는 정렬 상태를 확인해야 함)
    if important_emails:
        # 첫 5개 이메일 중 중요 메일이 있는지 확인
        top_5_emails = current_emails[:5]
        important_in_top = any(
            e.get("hidden_priority") == "high" for e in top_5_emails
        )
        
        if not important_in_top:
            gaps.append({
                "id": "gap_1",
                "type": "visibility",
                "description": "중요 메일이 상단에 보이지 않음",
                "severity": "high",
                "current": f"중요 메일 {len(important_emails)}개 중 상단 5개에 없음",
                "expected": "중요 메일이 상단에 위치해야 함",
                "affected_items": [e["id"] for e in important_emails[:3]]
            })
    
    # 응답 시간 체크 (간단한 예시)
    unread_important = [
        e for e in important_emails
        if not e.get("read", False)
    ]
    
    if unread_important:
        gaps.append({
            "id": "gap_2",
            "type": "response_time",
            "description": "중요 메일 미확인",
            "severity": "high",
            "current": f"미확인 중요 메일 {len(unread_important)}개",
            "expected": "중요 메일은 30분 내 확인",
            "affected_items": [e["id"] for e in unread_important[:3]]
        })
    
    return gaps

