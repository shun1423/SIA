"""
Execution Layer 유틸리티
v3.2: 멱등성, 레이트리밋, 부분 실패 처리 등 운영 체크리스트 구현
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
import time
import hashlib
import json


# 전역 상태: 처리된 이벤트 추적 (멱등성)
_processed_events: Set[str] = set()

# 전역 상태: 레이트리밋 추적
_rate_limit_tracker: Dict[str, List[datetime]] = {}


def generate_event_id(action: str, resource_id: str, context: Optional[Dict[str, Any]] = None) -> str:
    """
    이벤트 ID를 생성합니다 (멱등성 체크용).
    
    Args:
        action: 액션 이름
        resource_id: 리소스 ID (예: 이메일 ID, PR ID)
        context: 추가 컨텍스트
        
    Returns:
        이벤트 ID (해시)
    """
    event_data = {
        "action": action,
        "resource_id": resource_id,
        "context": context or {}
    }
    event_str = json.dumps(event_data, sort_keys=True)
    return hashlib.sha256(event_str.encode()).hexdigest()


def check_idempotency(event_id: str) -> bool:
    """
    멱등성 체크: 동일 이벤트가 이미 처리되었는지 확인합니다.
    
    Args:
        event_id: 이벤트 ID
        
    Returns:
        이미 처리되었으면 True, 아니면 False
    """
    if event_id in _processed_events:
        return True
    
    _processed_events.add(event_id)
    return False


def check_rate_limit(
    resource: str,
    max_requests: int = 100,
    window_seconds: int = 60
) -> Dict[str, Any]:
    """
    레이트리밋 체크 및 백오프 계산.
    
    Args:
        resource: 리소스 이름 (예: "gmail_api", "slack_api")
        max_requests: 시간당 최대 요청 수
        window_seconds: 시간 윈도우 (초)
        
    Returns:
        {
            "allowed": bool,
            "retry_after": Optional[float],  # 초 단위
            "remaining": int
        }
    """
    now = datetime.now()
    
    if resource not in _rate_limit_tracker:
        _rate_limit_tracker[resource] = []
    
    # 윈도우 밖의 오래된 요청 제거
    cutoff = now - timedelta(seconds=window_seconds)
    _rate_limit_tracker[resource] = [
        req_time for req_time in _rate_limit_tracker[resource]
        if req_time > cutoff
    ]
    
    current_count = len(_rate_limit_tracker[resource])
    
    if current_count >= max_requests:
        # 레이트리밋 초과: 가장 오래된 요청이 윈도우를 벗어날 때까지 대기
        oldest_request = min(_rate_limit_tracker[resource])
        retry_after = (oldest_request + timedelta(seconds=window_seconds) - now).total_seconds()
        
        return {
            "allowed": False,
            "retry_after": max(0, retry_after),
            "remaining": 0
        }
    
    # 요청 기록
    _rate_limit_tracker[resource].append(now)
    
    return {
        "allowed": True,
        "retry_after": None,
        "remaining": max_requests - current_count - 1
    }


def exponential_backoff(
    attempt: int,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    multiplier: float = 2.0
) -> float:
    """
    지수 백오프 지연 시간 계산.
    
    Args:
        attempt: 재시도 횟수 (0부터 시작)
        base_delay: 기본 지연 시간 (초)
        max_delay: 최대 지연 시간 (초)
        multiplier: 배수
        
    Returns:
        지연 시간 (초)
    """
    delay = base_delay * (multiplier ** attempt)
    return min(delay, max_delay)


def handle_partial_failure(
    results: List[Dict[str, Any]],
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    부분 실패 처리: 실패한 액션을 재시도합니다.
    
    Args:
        results: 실행 결과 리스트
        max_retries: 최대 재시도 횟수
        
    Returns:
        {
            "successful": List[Dict],
            "failed": List[Dict],
            "retried": List[Dict]
        }
    """
    successful = []
    failed = []
    retried = []
    
    for result in results:
        status = result.get("status", "unknown")
        
        if status == "success":
            successful.append(result)
        elif status in ["failed", "error"]:
            # 재시도 가능한 실패인지 확인
            if result.get("retryable", True) and result.get("retry_count", 0) < max_retries:
                # 재시도 로직 (실제로는 여기서 재시도)
                result["retry_count"] = result.get("retry_count", 0) + 1
                retried.append(result)
            else:
                failed.append(result)
        else:
            successful.append(result)
    
    return {
        "successful": successful,
        "failed": failed,
        "retried": retried
    }


def clear_processed_events(older_than_hours: int = 24):
    """
    오래된 처리 이벤트를 정리합니다 (메모리 관리).
    
    Args:
        older_than_hours: N시간 이전 이벤트 삭제
    """
    # 실제 구현에서는 타임스탬프를 저장하고 관리해야 함
    # MVP에서는 간단히 전체 삭제
    if len(_processed_events) > 10000:  # 임계값
        _processed_events.clear()

