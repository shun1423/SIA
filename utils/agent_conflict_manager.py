"""
다중 에이전트 충돌 관리 모듈
v3.2: 리소스 락, 우선순위 중재자, 사전 프리뷰 구현
"""

from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from enum import Enum


class ConflictType(Enum):
    """충돌 타입"""
    RESOURCE_LOCK = "resource_lock"  # 동일 리소스에 대한 쓰기 작업
    LABEL_CONFLICT = "label_conflict"  # 라벨링 정책 충돌
    ACTION_CONFLICT = "action_conflict"  # 액션 충돌


class AgentConflictManager:
    """에이전트 충돌 관리자"""
    
    def __init__(self):
        self.active_locks: Dict[str, Dict[str, Any]] = {}  # resource_id -> lock_info
        self.agent_priorities: Dict[str, int] = {}  # agent_id -> priority
    
    def check_conflict(
        self,
        agent_id: str,
        action: Dict[str, Any],
        resource_id: str,
        world_model: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        충돌을 확인합니다.
        
        Args:
            agent_id: 에이전트 ID
            action: 실행하려는 액션
            resource_id: 리소스 ID
            world_model: World Model 데이터
            
        Returns:
            {
                "has_conflict": bool,
                "conflict_type": Optional[ConflictType],
                "conflicting_agent": Optional[str],
                "resolution": Optional[str]
            }
        """
        action_type = action.get("type", "")
        
        # 쓰기 작업인 경우 리소스 락 확인
        if action_type in ["write", "delete"]:
            if resource_id in self.active_locks:
                lock_info = self.active_locks[resource_id]
                locked_by = lock_info.get("agent_id")
                
                if locked_by != agent_id:
                    # 우선순위 중재
                    resolution = self._resolve_priority(agent_id, locked_by, world_model)
                    
                    return {
                        "has_conflict": True,
                        "conflict_type": ConflictType.RESOURCE_LOCK.value,
                        "conflicting_agent": locked_by,
                        "resolution": resolution
                    }
        
        # 라벨링 충돌 확인 (이메일 도메인)
        if action.get("do", "").startswith("gmail.apply_label"):
            # 동일 리소스에 다른 라벨을 적용하려는 다른 에이전트가 있는지 확인
            for locked_resource, lock_info in self.active_locks.items():
                if locked_resource == resource_id:
                    locked_action = lock_info.get("action", {})
                    if locked_action.get("do", "").startswith("gmail.apply_label"):
                        if locked_action.get("do") != action.get("do"):
                            return {
                                "has_conflict": True,
                                "conflict_type": ConflictType.LABEL_CONFLICT.value,
                                "conflicting_agent": lock_info.get("agent_id"),
                                "resolution": "priority_based"
                            }
        
        return {
            "has_conflict": False,
            "conflict_type": None,
            "conflicting_agent": None,
            "resolution": None
        }
    
    def acquire_lock(
        self,
        agent_id: str,
        resource_id: str,
        action: Dict[str, Any],
        priority: int = 5
    ) -> bool:
        """
        리소스 락을 획득합니다.
        
        Args:
            agent_id: 에이전트 ID
            resource_id: 리소스 ID
            action: 실행하려는 액션
            priority: 우선순위 (1-10, 높을수록 우선)
            
        Returns:
            락 획득 성공 여부
        """
        if resource_id in self.active_locks:
            existing_lock = self.active_locks[resource_id]
            existing_priority = self.agent_priorities.get(existing_lock["agent_id"], 5)
            
            # 우선순위가 더 높으면 기존 락을 대체
            if priority > existing_priority:
                self.release_lock(resource_id)
            else:
                return False
        
        self.active_locks[resource_id] = {
            "agent_id": agent_id,
            "action": action,
            "acquired_at": datetime.now().isoformat()
        }
        self.agent_priorities[agent_id] = priority
        
        return True
    
    def release_lock(self, resource_id: str) -> None:
        """리소스 락을 해제합니다."""
        if resource_id in self.active_locks:
            agent_id = self.active_locks[resource_id].get("agent_id")
            del self.active_locks[resource_id]
            if agent_id in self.agent_priorities:
                del self.agent_priorities[agent_id]
    
    def _resolve_priority(
        self,
        agent1_id: str,
        agent2_id: str,
        world_model: Dict[str, Any]
    ) -> str:
        """
        우선순위 중재: 목표 중요도, 리스크 등급, 사용자 선호 기반 우선순위 결정.
        
        Args:
            agent1_id: 첫 번째 에이전트 ID
            agent2_id: 두 번째 에이전트 ID
            world_model: World Model 데이터
            
        Returns:
            "agent1_wins" 또는 "agent2_wins"
        """
        # 간단한 구현: 에이전트 ID 기반 (실제로는 더 정교한 로직 필요)
        # 실제 구현에서는:
        # 1. 에이전트의 목표 중요도 확인
        # 2. 리스크 등급 확인
        # 3. 사용자 선호 확인
        
        priority1 = self.agent_priorities.get(agent1_id, 5)
        priority2 = self.agent_priorities.get(agent2_id, 5)
        
        if priority1 > priority2:
            return "agent1_wins"
        elif priority2 > priority1:
            return "agent2_wins"
        else:
            # 동일 우선순위면 먼저 요청한 에이전트 승리
            return "agent1_wins"  # 간단한 구현
    
    def generate_preview(
        self,
        agent_id: str,
        actions: List[Dict[str, Any]],
        resources: List[str]
    ) -> Dict[str, Any]:
        """
        사전 프리뷰: 충돌 가능 작업의 변경 요약을 생성합니다.
        
        Args:
            agent_id: 에이전트 ID
            actions: 실행하려는 액션 리스트
            resources: 영향받는 리소스 리스트
            
        Returns:
            {
                "summary": str,
                "conflicts": List[Dict],
                "changes": List[Dict]
            }
        """
        conflicts = []
        changes = []
        
        for action, resource in zip(actions, resources):
            conflict_check = self.check_conflict(agent_id, action, resource, {})
            if conflict_check["has_conflict"]:
                conflicts.append({
                    "resource": resource,
                    "conflict_type": conflict_check["conflict_type"],
                    "conflicting_agent": conflict_check["conflicting_agent"]
                })
            
            changes.append({
                "resource": resource,
                "action": action.get("do", ""),
                "type": action.get("type", "")
            })
        
        summary = f"에이전트 {agent_id}가 {len(actions)}개 액션을 실행하려고 합니다. "
        if conflicts:
            summary += f"{len(conflicts)}개 충돌이 감지되었습니다."
        else:
            summary += "충돌이 없습니다."
        
        return {
            "summary": summary,
            "conflicts": conflicts,
            "changes": changes
        }


# 전역 인스턴스
_conflict_manager = AgentConflictManager()


def get_conflict_manager() -> AgentConflictManager:
    """충돌 관리자 인스턴스를 반환합니다."""
    return _conflict_manager

