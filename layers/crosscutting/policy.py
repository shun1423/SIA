"""
Policy & Consent Layer: 권한/승인/행동 정책을 중앙에서 강제하는 레이어
"""

from typing import Dict, Any, List, Optional
from enum import Enum


class ActionType(Enum):
    """액션 타입"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    NOTIFICATION = "notification"
    EXECUTE = "execute"


class RiskLevel(Enum):
    """리스크 레벨"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def check_permission(
    action: str,
    tool: Dict[str, Any],
    world_model: Dict[str, Any],
    agent_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    액션에 대한 권한을 확인합니다.
    
    Args:
        action: 수행하려는 액션
        tool: 사용하려는 도구
        world_model: World Model 데이터
        agent_config: 에이전트 구성 (선택적)
        
    Returns:
        권한 확인 결과 딕셔너리
        {
            "allowed": bool,
            "requires_approval": bool,
            "reason": str
        }
    """
    safety = world_model.get("safety", {})
    policy = safety.get("policy", {})
    
    # 기본 정책: 쓰기 작업은 기본 차단
    default_write_block = policy.get("default_write_block", True)
    
    # 액션 타입 판단
    action_type = _classify_action(action)
    
    # 쓰기 작업이고 기본 차단이 활성화되어 있으면 승인 필요
    if action_type in [ActionType.WRITE, ActionType.DELETE] and default_write_block:
        return {
            "allowed": False,
            "requires_approval": True,
            "reason": "쓰기 작업은 기본적으로 차단됩니다. 사용자 승인이 필요합니다."
        }
    
    # 허용 목록 확인
    allowlist = policy.get("action_allowlist", [])
    if action in allowlist:
        return {
            "allowed": True,
            "requires_approval": False,
            "reason": "허용 목록에 포함된 액션입니다."
        }
    
    # 금지 목록 확인
    forbidden = policy.get("forbidden_actions", [])
    if action in forbidden:
        return {
            "allowed": False,
            "requires_approval": False,
            "reason": "금지 목록에 포함된 액션입니다."
        }
    
    # 에이전트 리스크 레벨 확인
    if agent_config:
        risk_level = agent_config.get("risk_level", "medium")
        safety_policy = agent_config.get("safety", {})
        approval_policy = safety_policy.get("approval_policy", {})
        
        if action_type == ActionType.WRITE:
            write_policy = approval_policy.get("write_operations", "require_approval")
            if write_policy == "block":
                return {
                    "allowed": False,
                    "requires_approval": False,
                    "reason": f"리스크 레벨 {risk_level}에서는 쓰기 작업이 차단됩니다."
                }
            elif write_policy == "require_approval":
                return {
                    "allowed": True,
                    "requires_approval": True,
                    "reason": "쓰기 작업은 승인이 필요합니다."
                }
    
    # 기본값: 읽기 작업은 허용
    if action_type == ActionType.READ:
        return {
            "allowed": True,
            "requires_approval": False,
            "reason": "읽기 작업은 허용됩니다."
        }
    
    # 알 수 없는 액션은 승인 필요
    return {
        "allowed": True,
        "requires_approval": True,
        "reason": "알 수 없는 액션입니다. 승인이 필요합니다."
    }


def _classify_action(action: str) -> ActionType:
    """
    액션을 분류합니다.
    
    Args:
        action: 액션 문자열
        
    Returns:
        ActionType
    """
    action_lower = action.lower()
    
    if any(keyword in action_lower for keyword in ["read", "get", "fetch", "load"]):
        return ActionType.READ
    elif any(keyword in action_lower for keyword in ["write", "create", "update", "apply", "send"]):
        return ActionType.WRITE
    elif any(keyword in action_lower for keyword in ["delete", "remove", "drop"]):
        return ActionType.DELETE
    elif any(keyword in action_lower for keyword in ["notify", "notification", "alert"]):
        return ActionType.NOTIFICATION
    else:
        return ActionType.EXECUTE


def check_consent(
    action: str,
    tool: Dict[str, Any],
    world_model: Dict[str, Any]
) -> bool:
    """
    사용자 동의를 확인합니다.
    
    Args:
        action: 수행하려는 액션
        tool: 사용하려는 도구
        world_model: World Model 데이터
        
    Returns:
        동의 여부
    """
    # 연결된 소스 확인
    connected_sources = world_model.get("connected_sources", [])
    tool_name = tool.get("name", "")
    
    for source in connected_sources:
        if source.get("name", "").lower() == tool_name.lower():
            # 권한 범위 확인
            permissions = source.get("permissions", {})
            write_perms = permissions.get("write", [])
            
            # 쓰기 작업인데 권한이 없으면 False
            if _classify_action(action) == ActionType.WRITE:
                if not write_perms:
                    return False
            
            return True
    
    # 연결되지 않은 도구는 기본적으로 동의 없음
    return False


def validate_agent_config(
    agent_config: Dict[str, Any],
    world_model: Dict[str, Any]
) -> Dict[str, Any]:
    """
    에이전트 구성을 검증합니다.
    
    Args:
        agent_config: 에이전트 구성
        world_model: World Model 데이터
        
    Returns:
        검증 결과 딕셔너리
        {
            "valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    errors = []
    warnings = []
    
    # 필수 필드 확인
    required_fields = ["id", "trigger", "tools", "actions", "safety"]
    for field in required_fields:
        if field not in agent_config:
            errors.append(f"필수 필드 '{field}'가 없습니다.")
    
    # 도구 권한 확인
    tools = agent_config.get("tools", [])
    actions = agent_config.get("actions", [])
    
    for action in actions:
        action_type = action.get("type", "")
        if action_type == "write":
            # 쓰기 액션에 필요한 도구 권한 확인
            required_tool = action.get("tool", "")
            tool_found = False
            
            for tool in tools:
                if tool.get("name") == required_tool:
                    tool_found = True
                    permissions = tool.get("permissions", {})
                    write_perms = permissions.get("write", [])
                    
                    if not write_perms:
                        errors.append(
                            f"도구 '{required_tool}'에 쓰기 권한이 없습니다."
                        )
                    break
            
            if not tool_found:
                warnings.append(
                    f"액션에 필요한 도구 '{required_tool}'를 찾을 수 없습니다."
                )
    
    # 리스크 레벨 확인
    risk_level = agent_config.get("risk_level", "medium")
    if risk_level == "high" or risk_level == "critical":
        # 고위험 에이전트는 추가 검증 필요
        safety = agent_config.get("safety", {})
        if not safety.get("requires_approval", True):
            warnings.append(
                "고위험 에이전트는 승인이 필요합니다."
            )
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

