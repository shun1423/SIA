"""
개인 베이스라인 계산 모듈
v3.2: 개인 베이스라인 우선 원칙 구현
과거 2-4주 데이터를 기반으로 개인 베이스라인을 계산합니다.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json


def calculate_baseline(
    domain: str,
    current_state: Dict[str, Any],
    world_model: Optional[Dict[str, Any]] = None,
    weeks: int = 3
) -> Optional[Dict[str, Any]]:
    """
    개인 베이스라인을 계산합니다.
    과거 N주간의 데이터를 기반으로 평균값을 계산합니다.
    
    Args:
        domain: 도메인 ("email", "github", "health", "finance")
        current_state: 현재 상태 데이터
        world_model: World Model 데이터 (히스토리 저장용)
        weeks: 계산할 주 수 (기본값: 3주, 2-4주 권장)
        
    Returns:
        베이스라인 데이터 딕셔너리
        {
            "baseline_value": float,
            "baseline_period": f"{weeks}주",
            "calculated_at": str,
            "metrics": {...}
        }
    """
    # MVP에서는 샘플 데이터를 사용하지만, 실제로는 히스토리 데이터를 로드해야 함
    # World Model에 히스토리가 저장되어 있다고 가정
    
    if world_model is None:
        from layers.expectation import load_world_model
        world_model = load_world_model()
    
    # 히스토리 데이터 로드 (실제 구현에서는 별도 저장소에서 로드)
    history = world_model.get("history", {})
    domain_history = history.get(domain, [])
    
    # 도메인별 베이스라인 계산
    if domain == "email":
        return _calculate_email_baseline(current_state, domain_history, weeks)
    elif domain == "github":
        return _calculate_github_baseline(current_state, domain_history, weeks)
    elif domain == "health":
        return _calculate_health_baseline(current_state, domain_history, weeks)
    elif domain == "finance":
        return _calculate_finance_baseline(current_state, domain_history, weeks)
    
    return None


def _calculate_email_baseline(
    current_state: Dict[str, Any],
    history: List[Dict[str, Any]],
    weeks: int
) -> Dict[str, Any]:
    """이메일 도메인 베이스라인 계산"""
    # 현재 상태에서 중요 메일 응답 시간 추출
    emails = current_state.get("data", {}).get("emails", [])
    important_emails = [e for e in emails if e.get("hidden_priority") == "high"]
    
    # 히스토리에서 평균 응답 시간 계산 (실제로는 히스토리 데이터 필요)
    # MVP에서는 현재 데이터를 기반으로 추정
    if important_emails:
        # 중요 메일 평균 응답 시간 (시간 단위)
        # 실제로는 히스토리에서 계산해야 함
        avg_response_time = 1.5  # 기본값: 1.5시간
        
        # 히스토리가 있으면 실제 평균 계산
        if history:
            response_times = []
            for entry in history[-weeks*7:]:  # 최근 N주 데이터
                if "avg_response_time" in entry:
                    response_times.append(entry["avg_response_time"])
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
        
        return {
            "baseline_value": avg_response_time,
            "baseline_period": f"{weeks}주",
            "calculated_at": datetime.now().isoformat(),
            "metrics": {
                "avg_response_time_hours": avg_response_time,
                "important_email_count": len(important_emails),
                "sample_size": len(history) if history else 0
            }
        }
    
    return {
        "baseline_value": 0,
        "baseline_period": f"{weeks}주",
        "calculated_at": datetime.now().isoformat(),
        "metrics": {}
    }


def _calculate_github_baseline(
    current_state: Dict[str, Any],
    history: List[Dict[str, Any]],
    weeks: int
) -> Dict[str, Any]:
    """GitHub 도메인 베이스라인 계산"""
    prs = current_state.get("data", {}).get("prs", [])
    
    # 평균 PR 리뷰 시간 계산
    avg_review_time = 24.0  # 기본값: 24시간
    
    if history:
        review_times = []
        for entry in history[-weeks*7:]:
            if "avg_review_time_hours" in entry:
                review_times.append(entry["avg_review_time_hours"])
        if review_times:
            avg_review_time = sum(review_times) / len(review_times)
    
    return {
        "baseline_value": avg_review_time,
        "baseline_period": f"{weeks}주",
        "calculated_at": datetime.now().isoformat(),
        "metrics": {
            "avg_review_time_hours": avg_review_time,
            "pr_count": len(prs),
            "sample_size": len(history) if history else 0
        }
    }


def _calculate_health_baseline(
    current_state: Dict[str, Any],
    history: List[Dict[str, Any]],
    weeks: int
) -> Dict[str, Any]:
    """건강 도메인 베이스라인 계산"""
    records = current_state.get("data", {}).get("records", [])
    avg_sleep = current_state.get("data", {}).get("average_sleep_hours", 0)
    
    # 히스토리에서 평균 수면 시간 계산
    if history:
        sleep_hours = []
        for entry in history[-weeks*7:]:
            if "avg_sleep_hours" in entry:
                sleep_hours.append(entry["avg_sleep_hours"])
        if sleep_hours:
            avg_sleep = sum(sleep_hours) / len(sleep_hours)
    
    return {
        "baseline_value": avg_sleep,
        "baseline_period": f"{weeks}주",
        "calculated_at": datetime.now().isoformat(),
        "metrics": {
            "avg_sleep_hours": avg_sleep,
            "record_count": len(records),
            "sample_size": len(history) if history else 0
        }
    }


def _calculate_finance_baseline(
    current_state: Dict[str, Any],
    history: List[Dict[str, Any]],
    weeks: int
) -> Dict[str, Any]:
    """재정 도메인 베이스라인 계산"""
    category_spending = current_state.get("data", {}).get("category_spending", {})
    delivery_spending = category_spending.get("배달앱", 0)
    
    # 히스토리에서 평균 지출 계산
    avg_spending = delivery_spending  # 기본값: 현재 값
    
    if history:
        spending_values = []
        for entry in history[-weeks*7:]:
            if "delivery_spending" in entry:
                spending_values.append(entry["delivery_spending"])
        if spending_values:
            avg_spending = sum(spending_values) / len(spending_values)
    
    return {
        "baseline_value": avg_spending,
        "baseline_period": f"{weeks}주",
        "calculated_at": datetime.now().isoformat(),
        "metrics": {
            "avg_delivery_spending": avg_spending,
            "current_spending": delivery_spending,
            "sample_size": len(history) if history else 0
        }
    }

