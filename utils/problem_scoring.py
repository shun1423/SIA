"""
Problem Score 계산 모듈
v3.2에서 도입된 Problem Score는 Gap을 문제로 단정하지 않고,
목표 대비 기대 손실(utility loss)을 근사하는 점수 기반 선별 시스템입니다.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import math


def calculate_problem_score(
    gap: Dict[str, Any],
    world_model: Dict[str, Any],
    baseline_data: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> float:
    """
    Problem Score를 계산합니다.
    
    Problem Score 구성 요소:
    1. 지속성(Persistence): 일회성 이벤트가 아닌 반복/추세인지
    2. 크기(Severity): 기대 대비 차이가 의미 있는 수준인지
    3. 맥락 중요도(Context): 마감/중요 미팅/휴가 등 상황에서의 중요도
    4. 선호 위반(Preference Violation): 알림 최소화 선호인데 알림이 과다한지 등
    5. 미해결 비용(Cost): 놓칠 위험, 지연이 초래하는 비용 추정
    
    Args:
        gap: Comparison Layer에서 발견한 Gap
        world_model: World Model 데이터
        baseline_data: 개인 베이스라인 데이터 (과거 2-4주 평균)
        context: 현재 맥락 (시간, 요일, 이벤트 등)
        
    Returns:
        Problem Score (0.0 ~ 1.0)
    """
    if context is None:
        from datetime import datetime
        now = datetime.now()
        context = {
            "day": now.strftime("%A").lower(),
            "time": now.strftime("%H:%M"),
            "timestamp": now.isoformat()
        }
    
    # 1. 지속성 점수 (0.0 ~ 0.25)
    persistence_score = _calculate_persistence(gap, baseline_data)
    
    # 2. 크기 점수 (0.0 ~ 0.25)
    severity_score = _calculate_severity(gap, baseline_data)
    
    # 3. 맥락 중요도 점수 (0.0 ~ 0.20)
    context_score = _calculate_context_importance(gap, context, world_model)
    
    # 4. 선호 위반 점수 (0.0 ~ 0.15)
    preference_violation_score = _calculate_preference_violation(gap, world_model)
    
    # 5. 미해결 비용 점수 (0.0 ~ 0.15)
    cost_score = _calculate_unsolved_cost(gap, world_model)
    
    # 총합 (최대 1.0)
    total_score = (
        persistence_score * 0.25 +
        severity_score * 0.25 +
        context_score * 0.20 +
        preference_violation_score * 0.15 +
        cost_score * 0.15
    )
    
    return min(1.0, max(0.0, total_score))


def _calculate_persistence(
    gap: Dict[str, Any],
    baseline_data: Optional[Dict[str, Any]]
) -> float:
    """
    지속성 점수를 계산합니다.
    반복/추세인지 확인합니다.
    """
    gap_type = gap.get("type", "")
    evidence = gap.get("evidence", {})
    
    # 추세 데이터가 있으면 지속성 높음
    if "trend" in evidence:
        trend = evidence.get("trend", "")
        if trend in ["increasing", "decreasing", "stable"]:
            return 0.8  # 추세가 있으면 높은 점수
    
    # 반복 패턴이 있는지 확인
    if "recurrence_count" in evidence:
        count = evidence.get("recurrence_count", 0)
        if count >= 3:
            return 0.9
        elif count >= 2:
            return 0.6
        else:
            return 0.3
    
    # 일회성 이벤트로 추정
    return 0.2


def _calculate_severity(
    gap: Dict[str, Any],
    baseline_data: Optional[Dict[str, Any]]
) -> float:
    """
    크기 점수를 계산합니다.
    기대 대비 차이가 의미 있는 수준인지 확인합니다.
    """
    severity = gap.get("severity", "medium")
    
    # Severity 기반 기본 점수
    severity_map = {
        "high": 0.9,
        "medium": 0.6,
        "low": 0.3
    }
    base_score = severity_map.get(severity, 0.5)
    
    # 베이스라인과 비교
    if baseline_data:
        evidence = gap.get("evidence", {})
        current_value = evidence.get("current_value")
        baseline_value = baseline_data.get("baseline_value")
        
        if current_value is not None and baseline_value is not None:
            try:
                # 차이 비율 계산
                if baseline_value > 0:
                    ratio = abs(current_value - baseline_value) / baseline_value
                    # 50% 이상 차이면 높은 점수
                    if ratio >= 0.5:
                        return min(1.0, base_score + 0.2)
                    elif ratio >= 0.2:
                        return base_score
                    else:
                        return max(0.3, base_score - 0.2)
            except (TypeError, ZeroDivisionError):
                pass
    
    return base_score


def _calculate_context_importance(
    gap: Dict[str, Any],
    context: Dict[str, Any],
    world_model: Dict[str, Any]
) -> float:
    """
    맥락 중요도 점수를 계산합니다.
    마감/중요 미팅/휴가 등 상황에서의 중요도를 확인합니다.
    """
    # 시간대 중요도
    current_time = context.get("time", "12:00")
    hour = int(current_time.split(":")[0])
    
    # 업무 시간대 (9시 ~ 18시)는 중요도 높음
    if 9 <= hour <= 18:
        time_score = 0.7
    else:
        time_score = 0.4
    
    # 요일 중요도
    day = context.get("day", "").lower()
    if day in ["monday", "tuesday", "wednesday", "thursday", "friday"]:
        day_score = 0.8
    else:
        day_score = 0.5
    
    # 도메인별 중요도
    gap_domain = gap.get("domain", "")
    confirmed_problems = world_model.get("confirmed_problems", [])
    
    # 같은 도메인의 확정 문제가 있으면 중요도 높음
    domain_importance = 0.5
    for problem in confirmed_problems:
        if problem.get("domain") == gap_domain:
            domain_importance = 0.8
            break
    
    # 평균 계산
    return (time_score + day_score + domain_importance) / 3


def _calculate_preference_violation(
    gap: Dict[str, Any],
    world_model: Dict[str, Any]
) -> float:
    """
    선호 위반 점수를 계산합니다.
    사용자 선호와 충돌하는지 확인합니다.
    """
    preferences = world_model.get("preferences", {})
    gap_type = gap.get("type", "")
    
    # 알림 최소화 선호인데 알림 관련 Gap인 경우
    notification_pref = preferences.get("notifications", {}).get("frequency", "moderate")
    if gap_type == "notification_overload" and notification_pref == "minimal":
        return 0.9  # 높은 위반 점수
    
    # 자동화 수용도 낮은데 자동화 관련 Gap인 경우
    automation_pref = preferences.get("automation", {}).get("acceptance", "moderate")
    if gap_type == "automation_needed" and automation_pref == "low":
        return 0.7
    
    # 선호 위반 없음
    return 0.1


def _calculate_unsolved_cost(
    gap: Dict[str, Any],
    world_model: Dict[str, Any]
) -> float:
    """
    미해결 비용 점수를 계산합니다.
    놓칠 위험, 지연이 초래하는 비용을 추정합니다.
    """
    severity = gap.get("severity", "medium")
    gap_type = gap.get("type", "")
    
    # Severity 기반 기본 비용
    cost_map = {
        "high": 0.8,
        "medium": 0.5,
        "low": 0.2
    }
    base_cost = cost_map.get(severity, 0.5)
    
    # Gap 타입별 추가 비용
    type_cost_map = {
        "response_time": 0.7,  # 응답 지연은 높은 비용
        "missed_deadline": 0.9,  # 마감 놓침은 매우 높은 비용
        "visibility": 0.6,  # 가시성 문제는 중간 비용
        "pattern_deviation": 0.4  # 패턴 이탈은 낮은 비용
    }
    type_cost = type_cost_map.get(gap_type, 0.5)
    
    # 평균 계산
    return (base_cost + type_cost) / 2


def filter_gaps_by_score(
    gaps: List[Dict[str, Any]],
    world_model: Dict[str, Any],
    threshold: float = 0.5,
    baseline_data: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Problem Score가 임계값 이상인 Gap만 필터링합니다.
    
    Args:
        gaps: Gap 리스트
        world_model: World Model 데이터
        threshold: Problem Score 임계값 (기본값: 0.5)
        baseline_data: 개인 베이스라인 데이터
        context: 현재 맥락
        
    Returns:
        필터링된 Gap 리스트 (Problem Score 포함)
    """
    filtered = []
    
    for gap in gaps:
        score = calculate_problem_score(gap, world_model, baseline_data, context)
        gap["problem_score"] = score
        
        if score >= threshold:
            filtered.append(gap)
    
    # Problem Score 순으로 정렬 (높은 순)
    filtered.sort(key=lambda x: x.get("problem_score", 0), reverse=True)
    
    return filtered

