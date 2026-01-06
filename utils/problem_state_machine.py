"""
문제 상태 머신 모듈
v3.2에서 도입된 문제 상태 전이 시스템을 구현합니다.

상태 전이:
[Candidate] → (제안) → [Proposed] → (승인) → [Confirmed] → (해결/종료) → [Archived]
                     ├────────(거절)────────→ [Rejected]
                     └────────(보류)────────→ [Snoozed] → (재평가) → [Candidate]
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum


class ProblemStatus(Enum):
    """문제 상태 열거형"""
    CANDIDATE = "candidate"  # 시스템 감지, 미확정
    PROPOSED = "proposed"  # 사용자에게 제안됨
    CONFIRMED = "confirmed"  # 사용자 승인
    REJECTED = "rejected"  # 사용자 거절
    SNOOZED = "snoozed"  # 보류 (나중에 재평가)
    ARCHIVED = "archived"  # 해결 완료 또는 종료


class ProblemStateMachine:
    """문제 상태 머신 클래스"""
    
    # 허용된 상태 전이
    ALLOWED_TRANSITIONS = {
        ProblemStatus.CANDIDATE: [ProblemStatus.PROPOSED],
        ProblemStatus.PROPOSED: [
            ProblemStatus.CONFIRMED,
            ProblemStatus.REJECTED,
            ProblemStatus.SNOOZED
        ],
        ProblemStatus.CONFIRMED: [ProblemStatus.ARCHIVED],
        ProblemStatus.REJECTED: [],  # 거절된 문제는 더 이상 전이 불가
        ProblemStatus.SNOOZED: [ProblemStatus.CANDIDATE, ProblemStatus.REJECTED],
        ProblemStatus.ARCHIVED: []  # 아카이브된 문제는 종료
    }
    
    @staticmethod
    def can_transition(
        current_status: str,
        target_status: str
    ) -> bool:
        """
        상태 전이가 가능한지 확인합니다.
        
        Args:
            current_status: 현재 상태
            target_status: 목표 상태
            
        Returns:
            전이 가능 여부
        """
        try:
            current = ProblemStatus(current_status)
            target = ProblemStatus(target_status)
            
            allowed = ProblemStateMachine.ALLOWED_TRANSITIONS.get(current, [])
            return target in allowed
        except ValueError:
            return False
    
    @staticmethod
    def transition(
        problem: Dict[str, Any],
        target_status: str,
        user_action: Optional[str] = None,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        문제 상태를 전이합니다.
        
        Args:
            problem: 문제 딕셔너리
            target_status: 목표 상태
            user_action: 사용자 액션 (approve, reject, snooze 등)
            reason: 전이 사유
            
        Returns:
            업데이트된 문제 딕셔너리
            
        Raises:
            ValueError: 허용되지 않은 상태 전이인 경우
        """
        current_status = problem.get("status", ProblemStatus.CANDIDATE.value)
        
        if not ProblemStateMachine.can_transition(current_status, target_status):
            raise ValueError(
                f"상태 전이 불가: {current_status} → {target_status}"
            )
        
        # 상태 업데이트
        problem["status"] = target_status
        problem["updated_at"] = datetime.now().isoformat()
        
        # 상태 전이 히스토리 추가
        if "transition_history" not in problem:
            problem["transition_history"] = []
        
        problem["transition_history"].append({
            "from": current_status,
            "to": target_status,
            "user_action": user_action,
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        })
        
        # 상태별 추가 처리
        if target_status == ProblemStatus.PROPOSED.value:
            problem["proposed_at"] = datetime.now().isoformat()
        
        elif target_status == ProblemStatus.CONFIRMED.value:
            problem["confirmed_at"] = datetime.now().isoformat()
            problem["confirmed_by"] = user_action
        
        elif target_status == ProblemStatus.REJECTED.value:
            problem["rejected_at"] = datetime.now().isoformat()
            problem["rejection_reason"] = reason
        
        elif target_status == ProblemStatus.SNOOZED.value:
            problem["snoozed_at"] = datetime.now().isoformat()
            # 기본 보류 기간: 7일
            problem["snooze_until"] = (
                datetime.now() + timedelta(days=7)
            ).isoformat()
            if reason:
                problem["snooze_reason"] = reason
        
        elif target_status == ProblemStatus.ARCHIVED.value:
            problem["archived_at"] = datetime.now().isoformat()
            if reason:
                problem["archive_reason"] = reason
        
        return problem
    
    @staticmethod
    def promote_candidate_to_proposed(
        problem_candidate: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        문제 후보를 제안 상태로 승격합니다.
        
        Args:
            problem_candidate: 문제 후보 딕셔너리
            
        Returns:
            제안 상태로 전이된 문제 딕셔너리
        """
        return ProblemStateMachine.transition(
            problem_candidate,
            ProblemStatus.PROPOSED.value,
            user_action="system_propose"
        )
    
    @staticmethod
    def confirm_problem(
        problem: Dict[str, Any],
        user_action: str = "user_approve"
    ) -> Dict[str, Any]:
        """
        문제를 확정 상태로 전이합니다.
        
        Args:
            problem: 문제 딕셔너리
            user_action: 사용자 액션
            
        Returns:
            확정 상태로 전이된 문제 딕셔너리
        """
        return ProblemStateMachine.transition(
            problem,
            ProblemStatus.CONFIRMED.value,
            user_action=user_action
        )
    
    @staticmethod
    def reject_problem(
        problem: Dict[str, Any],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        문제를 거절 상태로 전이합니다.
        
        Args:
            problem: 문제 딕셔너리
            reason: 거절 사유
            
        Returns:
            거절 상태로 전이된 문제 딕셔너리
        """
        return ProblemStateMachine.transition(
            problem,
            ProblemStatus.REJECTED.value,
            user_action="user_reject",
            reason=reason
        )
    
    @staticmethod
    def snooze_problem(
        problem: Dict[str, Any],
        days: int = 7,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        문제를 보류 상태로 전이합니다.
        
        Args:
            problem: 문제 딕셔너리
            days: 보류 기간 (일)
            reason: 보류 사유
            
        Returns:
            보류 상태로 전이된 문제 딕셔너리
        """
        problem = ProblemStateMachine.transition(
            problem,
            ProblemStatus.SNOOZED.value,
            user_action="user_snooze",
            reason=reason
        )
        
        # 보류 기간 설정
        problem["snooze_until"] = (
            datetime.now() + timedelta(days=days)
        ).isoformat()
        
        return problem
    
    @staticmethod
    def archive_problem(
        problem: Dict[str, Any],
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        문제를 아카이브 상태로 전이합니다.
        
        Args:
            problem: 문제 딕셔너리
            reason: 아카이브 사유 (예: "해결 완료", "더 이상 관련 없음")
            
        Returns:
            아카이브 상태로 전이된 문제 딕셔너리
        """
        return ProblemStateMachine.transition(
            problem,
            ProblemStatus.ARCHIVED.value,
            user_action="user_archive",
            reason=reason
        )
    
    @staticmethod
    def check_snoozed_problems(
        world_model: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        보류 기간이 만료된 문제를 찾아 후보 상태로 되돌립니다.
        
        Args:
            world_model: World Model 데이터
            
        Returns:
            재평가 대상 문제 리스트
        """
        now = datetime.now()
        problem_candidates = world_model.get("problem_candidates", [])
        confirmed_problems = world_model.get("confirmed_problems", [])
        
        all_problems = problem_candidates + confirmed_problems
        ready_for_reevaluation = []
        
        for problem in all_problems:
            if problem.get("status") == ProblemStatus.SNOOZED.value:
                snooze_until = problem.get("snooze_until")
                if snooze_until:
                    try:
                        until = datetime.fromisoformat(snooze_until.replace("Z", "+00:00"))
                        if now >= until:
                            # 보류 기간 만료, 후보 상태로 복귀
                            problem = ProblemStateMachine.transition(
                                problem,
                                ProblemStatus.CANDIDATE.value,
                                user_action="system_reevaluate",
                                reason="보류 기간 만료"
                            )
                            ready_for_reevaluation.append(problem)
                    except (ValueError, TypeError):
                        pass
        
        return ready_for_reevaluation

