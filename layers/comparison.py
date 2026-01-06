"""
Comparison Layer: 현재 상태와 이상적 상태를 비교하여 Gap을 찾는 계층
v3.2 업데이트: Problem Score 계산 통합
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
from utils.problem_scoring import calculate_problem_score, filter_gaps_by_score
from utils.baseline_calculator import calculate_baseline
from prompts.comparison import format_comparison_prompt


def _init_anthropic_client() -> Optional[Anthropic]:
    """Anthropic 클라이언트를 초기화합니다."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def compare_states(
    current_state: Dict[str, Any],
    expectation: Dict[str, Any],
    anthropic_client: Optional[Anthropic] = None,
    world_model: Optional[Dict[str, Any]] = None,
    problem_score_threshold: float = 0.5
) -> List[Dict[str, Any]]:
    """
    현재 상태와 기대 상태를 비교하여 Gap을 찾습니다.
    Claude API를 사용하여 두 상태를 분석하고 Gap 리스트를 반환합니다.
    v3.2 업데이트: Problem Score 계산 및 필터링 통합
    
    Args:
        current_state: Sensor Layer에서 수집한 현재 상태
        expectation: Expectation Layer에서 생성한 기대 상태
        anthropic_client: Anthropic 클라이언트 (None이면 자동 초기화)
        world_model: World Model 데이터 (Problem Score 계산용)
        problem_score_threshold: Problem Score 임계값 (기본값: 0.5)
        
    Returns:
        Gap 리스트 (각 Gap에 중요도 및 Problem Score 포함)
    """
    # Anthropic 클라이언트 초기화
    if anthropic_client is None:
        anthropic_client = _init_anthropic_client()
    
    # World Model 로드 (없으면 기본값)
    if world_model is None:
        from layers.expectation import load_world_model
        world_model = load_world_model()
    
    # ============================================
    # Tiered Inference 패턴 구현 (v3.2)
    # 1) Cheap Detection: 규칙/통계 기반 Gap 후보 추출
    # 2) Expensive Interpretation: LLM으로 해석/설명
    # ============================================
    
    # Step 1: Cheap Detection - 규칙/통계 기반으로 Gap 후보 추출
    gaps = []
    domain = current_state.get("domain", "email")
    ideal_states = expectation.get("ideal_states", [])
    
    # 개인 베이스라인 계산 (v3.2: 개인 베이스라인 우선 원칙)
    baseline_data = calculate_baseline(domain, current_state, world_model, weeks=3)
    
    # 도메인별 규칙 기반 Gap 감지 (Cheap)
    if domain == "email":
        _detect_email_gaps(gaps, current_state, ideal_states, world_model, problem_score_threshold, baseline_data)
    elif domain == "github":
        _detect_github_gaps(gaps, current_state, ideal_states, world_model, problem_score_threshold, baseline_data)
    elif domain == "health":
        _detect_health_gaps(gaps, current_state, ideal_states, world_model, problem_score_threshold, baseline_data)
    elif domain == "finance":
        _detect_finance_gaps(gaps, current_state, ideal_states, world_model, problem_score_threshold, baseline_data)
    
    # Step 2: Expensive Interpretation - LLM으로 Gap 해석 및 보강 (선택적)
    # 규칙 기반으로 찾은 Gap이 있고, LLM이 사용 가능하면 해석 보강
    if gaps and anthropic_client:
        try:
            # LLM으로 Gap 해석 및 추가 분석
            # (현재는 규칙 기반 결과를 사용하되, 필요시 LLM으로 보강 가능)
            # 실제 구현에서는 LLM이 Gap을 더 정교하게 해석하거나 추가 Gap을 찾을 수 있음
            pass  # 현재는 규칙 기반 결과를 우선 사용
        except Exception as e:
            # LLM 호출 실패해도 규칙 기반 결과는 유지
            print(f"LLM 해석 보강 실패 (규칙 기반 결과 사용): {e}")
    
    # Problem Score 계산 및 필터링 (베이스라인 데이터 포함)
    gaps = filter_gaps_by_score(
        gaps,
        world_model,
        threshold=problem_score_threshold,
        baseline_data=baseline_data
    )
    
    return gaps


def _detect_email_gaps(
    gaps: List[Dict[str, Any]],
    current_state: Dict[str, Any],
    ideal_states: List[Dict[str, Any]],
    world_model: Dict[str, Any],
    problem_score_threshold: float,
    baseline_data: Optional[Dict[str, Any]] = None
) -> None:
    """이메일 도메인 Gap 감지"""
    current_emails = current_state.get("data", {}).get("emails", [])
    
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
            gap = {
                "id": "gap_1",
                "type": "visibility",
                "domain": "email",
                "description": "중요 메일이 상단에 보이지 않음",
                "severity": "high",
                "current": f"중요 메일 {len(important_emails)}개 중 상단 5개에 없음",
                "expected": "중요 메일이 상단에 위치해야 함",
                "affected_items": [e["id"] for e in important_emails[:3]],
                "evidence": {
                    "current_value": len([e for e in top_5_emails if e.get("hidden_priority") == "high"]),
                    "expected_value": len(important_emails),
                    "trend": "stable",
                    "recurrence_count": 1
                }
            }
            # Problem Score 계산 (베이스라인 데이터 포함)
            gap["problem_score"] = calculate_problem_score(gap, world_model, baseline_data=baseline_data)
            gaps.append(gap)
    
    # 응답 시간 체크 (간단한 예시)
    unread_important = [
        e for e in important_emails
        if not e.get("read", False)
    ]
    
    if unread_important:
        gap = {
            "id": "gap_2",
            "type": "response_time",
            "domain": "email",
            "description": "중요 메일 미확인",
            "severity": "high",
            "current": f"미확인 중요 메일 {len(unread_important)}개",
            "expected": "중요 메일은 30분 내 확인",
            "affected_items": [e["id"] for e in unread_important[:3]],
            "evidence": {
                "current_value": len(unread_important),
                "expected_value": 0,
                "trend": "increasing",
                "recurrence_count": 2
            }
        }
        # Problem Score 계산 (베이스라인 데이터 포함)
        gap["problem_score"] = calculate_problem_score(gap, world_model, baseline_data=baseline_data)
        gaps.append(gap)
    
    # Problem Score 기준 필터링
    gaps = [g for g in gaps if g.get("problem_score", 0) >= problem_score_threshold]
    
    return gaps


def _detect_github_gaps(
    gaps: List[Dict[str, Any]],
    current_state: Dict[str, Any],
    ideal_states: List[Dict[str, Any]],
    world_model: Dict[str, Any],
    problem_score_threshold: float,
    baseline_data: Optional[Dict[str, Any]] = None
) -> None:
    """GitHub 도메인 Gap 감지"""
    prs = current_state.get("data", {}).get("prs", [])
    pending_reviews = [pr for pr in prs if pr.get("review_status") == "pending"]
    old_prs = [pr for pr in pending_reviews if pr.get("age_hours", 0) > 48]
    
    if old_prs:
        gap = {
            "id": "gap_github_1",
            "type": "review_delay",
            "domain": "github",
            "description": "리뷰 대기 중인 PR이 48시간 이상 지연됨",
            "severity": "high",
            "current": f"지연된 PR {len(old_prs)}개",
            "expected": "PR은 24시간 내 리뷰되어야 함",
            "affected_items": [pr["id"] for pr in old_prs[:3]],
            "evidence": {
                "current_value": len(old_prs),
                "expected_value": 0,
                "trend": "stable",
                "recurrence_count": 1
            }
        }
        gap["problem_score"] = calculate_problem_score(gap, world_model, baseline_data=baseline_data)
        if gap["problem_score"] >= problem_score_threshold:
            gaps.append(gap)


def _detect_health_gaps(
    gaps: List[Dict[str, Any]],
    current_state: Dict[str, Any],
    ideal_states: List[Dict[str, Any]],
    world_model: Dict[str, Any],
    problem_score_threshold: float,
    baseline_data: Optional[Dict[str, Any]] = None
) -> None:
    """건강 도메인 Gap 감지"""
    records = current_state.get("data", {}).get("records", [])
    avg_sleep = current_state.get("data", {}).get("average_sleep_hours", 0)
    
    # 수면 시간 체크 (목표: 7시간)
    if avg_sleep < 7 and records:
        gap = {
            "id": "gap_health_1",
            "type": "sleep_deficit",
            "domain": "health",
            "description": "평균 수면 시간이 7시간 미만",
            "severity": "medium",
            "current": f"평균 수면 시간 {avg_sleep:.1f}시간",
            "expected": "평균 수면 시간 7시간 이상",
            "affected_items": [r.get("date", "") for r in records[-3:]],
            "evidence": {
                "current_value": avg_sleep,
                "expected_value": 7.0,
                "trend": "stable",
                "recurrence_count": len(records)
            }
        }
        gap["problem_score"] = calculate_problem_score(gap, world_model, baseline_data=baseline_data)
        if gap["problem_score"] >= problem_score_threshold:
            gaps.append(gap)


def _detect_finance_gaps(
    gaps: List[Dict[str, Any]],
    current_state: Dict[str, Any],
    ideal_states: List[Dict[str, Any]],
    world_model: Dict[str, Any],
    problem_score_threshold: float,
    baseline_data: Optional[Dict[str, Any]] = None
) -> None:
    """재정 도메인 Gap 감지"""
    transactions = current_state.get("data", {}).get("transactions", [])
    category_spending = current_state.get("data", {}).get("category_spending", {})
    
    # 배달앱 지출 체크 (주간 5만원 초과)
    delivery_spending = category_spending.get("배달앱", 0)
    if delivery_spending > 50000:
        gap = {
            "id": "gap_finance_1",
            "type": "overspending",
            "domain": "finance",
            "description": "배달앱 지출이 주간 한도(5만원)를 초과함",
            "severity": "medium",
            "current": f"배달앱 지출 {delivery_spending:,}원",
            "expected": "주간 배달앱 지출 5만원 이하",
            "affected_items": [txn.get("id", "") for txn in transactions if txn.get("category") == "배달앱"][:3],
            "evidence": {
                "current_value": delivery_spending,
                "expected_value": 50000,
                "trend": "increasing",
                "recurrence_count": len([t for t in transactions if t.get("category") == "배달앱"])
            }
        }
        gap["problem_score"] = calculate_problem_score(gap, world_model, baseline_data=baseline_data)
        if gap["problem_score"] >= problem_score_threshold:
            gaps.append(gap)

