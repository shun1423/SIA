"""
도메인 헬퍼 유틸리티
모든 레이어에서 일관된 도메인을 사용하도록 도와주는 함수
"""

from typing import Optional, Dict, Any, List


def get_active_domain(
    world_model: Optional[Dict[str, Any]] = None,
    current_state: Optional[Dict[str, Any]] = None,
    session_state: Optional[Any] = None,
    default: str = "email"
) -> str:
    """
    활성 도메인을 결정합니다. 우선순위:
    1. session_state.selected_domain (데모에서 선택한 도메인)
    2. current_state.domain (현재 상태의 도메인)
    3. world_model의 첫 번째 활성 소스
    4. default (기본값)
    
    Args:
        world_model: World Model 데이터
        current_state: 현재 상태 데이터
        session_state: Streamlit session state
        default: 기본 도메인
        
    Returns:
        도메인 문자열
    """
    # 1순위: 세션 상태의 선택된 도메인 (데모에서 선택한 도메인)
    if session_state and hasattr(session_state, 'get'):
        selected_domain = session_state.get("selected_domain")
        if selected_domain:
            return selected_domain
    
    # 2순위: current_state의 도메인
    if current_state:
        domain = current_state.get("domain")
        if domain and domain != "multi":  # multi는 여러 도메인 조합이므로 제외
            return domain
    
    # 3순위: World Model의 첫 번째 활성 소스
    if world_model:
        source_to_domain = {
            "Gmail": "email",
            "GitHub": "github",
            "Apple Health": "health",
            "Finance App": "finance",
            "카드사": "finance",
            "은행": "finance"
        }
        connected_sources = world_model.get("connected_sources", [])
        active_sources = [s for s in connected_sources if s.get("status") == "active"]
        if active_sources:
            source_name = active_sources[0].get("name", "")
            domain = source_to_domain.get(source_name)
            if domain:
                return domain
    
    # 4순위: 기본값
    return default


def get_available_domains(
    world_model: Optional[Dict[str, Any]] = None,
    session_state: Optional[Any] = None
) -> List[str]:
    """
    사용 가능한 도메인 리스트를 반환합니다.
    
    Args:
        world_model: World Model 데이터
        session_state: Streamlit session state
        
    Returns:
        도메인 리스트
    """
    source_to_domain = {
        "Gmail": "email",
        "GitHub": "github",
        "Apple Health": "health",
        "Finance App": "finance",
        "카드사": "finance",
        "은행": "finance"
    }
    
    available = []
    
    # 세션 상태에 선택된 도메인이 있으면 우선
    if session_state and hasattr(session_state, 'get'):
        selected_domain = session_state.get("selected_domain")
        if selected_domain:
            available.append(selected_domain)
    
    # World Model에서 활성 소스의 도메인 추가
    if world_model:
        connected_sources = world_model.get("connected_sources", [])
        active_sources = [s for s in connected_sources if s.get("status") == "active"]
        for source in active_sources:
            source_name = source.get("name", "")
            domain = source_to_domain.get(source_name)
            if domain and domain not in available:
                available.append(domain)
    
    # 없으면 기본값
    if not available:
        available = ["email"]
    
    return available

