"""
Observability & Auditing Layer: 실행 로그·근거·효과를 기록/감사 가능하게 하는 레이어
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json


class AuditLogger:
    """감사 로그 기록 클래스"""
    
    def __init__(self, log_dir: str = "logs"):
        """
        AuditLogger 초기화
        
        Args:
            log_dir: 로그 디렉토리 경로
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
    
    def log_proposal(
        self,
        problem_candidate_id: str,
        evidence: Dict[str, Any],
        proposal_text: str,
        alternatives_shown: List[str],
        user_decision: str,
        timestamp: Optional[str] = None
    ) -> None:
        """
        제안 로그를 기록합니다.
        
        Args:
            problem_candidate_id: 문제 후보 ID
            evidence: 증거 데이터
            proposal_text: 제안 텍스트
            alternatives_shown: 제시된 대안 리스트
            user_decision: 사용자 결정 (approve/reject/snooze/edit)
            timestamp: 타임스탬프 (선택적)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        log_entry = {
            "type": "proposal",
            "timestamp": timestamp,
            "problem_candidate_id": problem_candidate_id,
            "evidence": evidence,
            "proposal_text": proposal_text,
            "alternatives_shown": alternatives_shown,
            "user_decision": user_decision
        }
        
        self._write_log("proposals", log_entry)
    
    def log_execution(
        self,
        agent_id: str,
        trigger_event_id: Optional[str],
        tool_calls: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        outcome_metrics: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> None:
        """
        실행 로그를 기록합니다.
        
        Args:
            agent_id: 에이전트 ID
            trigger_event_id: 트리거 이벤트 ID
            tool_calls: 도구 호출 리스트
            actions: 실행된 액션 리스트
            outcome_metrics: 결과 지표
            timestamp: 타임스탬프 (선택적)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        log_entry = {
            "type": "execution",
            "timestamp": timestamp,
            "agent_id": agent_id,
            "trigger_event_id": trigger_event_id,
            "tool_calls": tool_calls,
            "actions": actions,
            "outcome_metrics": outcome_metrics
        }
        
        self._write_log("executions", log_entry)
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        context: Dict[str, Any],
        timestamp: Optional[str] = None
    ) -> None:
        """
        에러 로그를 기록합니다.
        
        Args:
            error_type: 에러 타입
            error_message: 에러 메시지
            context: 컨텍스트
            timestamp: 타임스탬프 (선택적)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        log_entry = {
            "type": "error",
            "timestamp": timestamp,
            "error_type": error_type,
            "error_message": error_message,
            "context": context
        }
        
        self._write_log("errors", log_entry)
    
    def log_decision(
        self,
        decision_type: str,
        decision_data: Dict[str, Any],
        reasoning: Optional[str] = None,
        timestamp: Optional[str] = None
    ) -> None:
        """
        의사결정 로그를 기록합니다.
        
        Args:
            decision_type: 의사결정 타입
            decision_data: 의사결정 데이터
            reasoning: 추론 과정 (선택적)
            timestamp: 타임스탬프 (선택적)
        """
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        log_entry = {
            "type": "decision",
            "timestamp": timestamp,
            "decision_type": decision_type,
            "decision_data": decision_data,
            "reasoning": reasoning
        }
        
        self._write_log("decisions", log_entry)
    
    def _write_log(self, log_category: str, log_entry: Dict[str, Any]) -> None:
        """
        로그를 파일에 기록합니다.
        
        Args:
            log_category: 로그 카테고리
            log_entry: 로그 엔트리
        """
        log_file = self.log_dir / f"{log_category}.jsonl"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")


# 전역 로거 인스턴스
_audit_logger = None


def get_audit_logger() -> AuditLogger:
    """
    AuditLogger 인스턴스를 반환합니다.
    
    Returns:
        AuditLogger 인스턴스
    """
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_proposal_decision(
    problem_candidate: Dict[str, Any],
    proposal: Dict[str, Any],
    user_decision: str,
    reason: Optional[str] = None
) -> None:
    """
    제안 결정을 로깅합니다.
    
    Args:
        problem_candidate: 문제 후보
        proposal: 제안
        user_decision: 사용자 결정
        reason: 사유 (선택적)
    """
    logger = get_audit_logger()
    
    logger.log_proposal(
        problem_candidate_id=problem_candidate.get("id", "unknown"),
        evidence=problem_candidate.get("evidence", {}),
        proposal_text=proposal.get("recommended_solution", {}).get("name", ""),
        alternatives_shown=[s.get("name", "") for s in proposal.get("alternative_solutions", [])],
        user_decision=user_decision
    )


def log_agent_execution(
    agent_config: Dict[str, Any],
    execution_result: Dict[str, Any],
    trigger_event_id: Optional[str] = None
) -> None:
    """
    에이전트 실행을 로깅합니다.
    
    Args:
        agent_config: 에이전트 구성
        execution_result: 실행 결과
        trigger_event_id: 트리거 이벤트 ID (선택적)
    """
    logger = get_audit_logger()
    
    workflow_results = execution_result.get("workflow_results", [])
    tool_calls = []
    actions = []
    
    for result in workflow_results:
        tool_calls.append({
            "name": result.get("action", "unknown"),
            "tool": result.get("tool", "unknown"),
            "success": result.get("status") == "success",
            "output": result.get("output", "")
        })
    
    # 도메인별 처리된 데이터 확인
    domain = execution_result.get("domain", "email")
    processed_data = []
    
    if domain == "email":
        processed_data = execution_result.get("processed_emails", [])
    elif domain == "github":
        processed_data = execution_result.get("processed_prs", [])
    elif domain == "health":
        processed_data = execution_result.get("processed_records", [])
    elif domain == "finance":
        processed_data = execution_result.get("processed_transactions", [])
    
    actions = processed_data
    
    outcome_metrics = execution_result.get("summary", {})
    
    logger.log_execution(
        agent_id=agent_config.get("id", "unknown"),
        trigger_event_id=trigger_event_id,
        tool_calls=tool_calls,
        actions=actions,
        outcome_metrics=outcome_metrics
    )


def get_execution_history(
    agent_id: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    실행 이력을 조회합니다.
    
    Args:
        agent_id: 에이전트 ID (선택적, None이면 전체)
        limit: 최대 조회 개수
        
    Returns:
        실행 이력 리스트
    """
    logger = get_audit_logger()
    log_file = logger.log_dir / "executions.jsonl"
    
    if not log_file.exists():
        return []
    
    history = []
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                if agent_id is None or entry.get("agent_id") == agent_id:
                    history.append(entry)
    
    # 최신순 정렬
    history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    
    return history[:limit]

