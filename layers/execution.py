"""
Execution Layer: 구성된 에이전트를 실행하는 계층
v3.2 업데이트: 횡단 레이어 통합 (Policy, Security, Observability)
"""

from typing import Dict, Any, List, Optional
import json
from pathlib import Path

# 횡단 레이어 임포트
import sys
sys.path.append(str(Path(__file__).parent.parent))
from layers.crosscutting.policy import check_permission, validate_agent_config
from layers.crosscutting.security import sanitize_input, validate_prompt_injection
from layers.crosscutting.observability import log_agent_execution, get_audit_logger
from utils.execution_utils import (
    generate_event_id, check_idempotency, check_rate_limit,
    exponential_backoff, handle_partial_failure
)
from utils.agent_conflict_manager import get_conflict_manager


def execute_agent(
    agent_config: Dict[str, Any], 
    input_data: Dict[str, Any] = None,
    emails: List[Dict[str, Any]] = None,  # 하위 호환성 유지 (deprecated)
    world_model: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    구성된 에이전트를 실행합니다.
    v3.2 업데이트: Policy 체크, Security 검증, Observability 로깅 통합
    
    Args:
        agent_config: Composition Layer에서 생성한 에이전트 구성
        input_data: 입력 데이터 (이메일 등)
        emails: 이메일 리스트 (직접 전달 가능)
        world_model: World Model 데이터 (Policy 체크용)
        
    Returns:
        실행 결과 딕셔너리
    """
    # World Model 로드
    if world_model is None:
        from layers.expectation import load_world_model
        world_model = load_world_model()
    
    # 에이전트 구성 검증
    validation_result = validate_agent_config(agent_config, world_model)
    if not validation_result["valid"]:
        return {
            "status": "failed",
            "error": "에이전트 구성 검증 실패",
            "errors": validation_result["errors"],
            "warnings": validation_result["warnings"]
        }
    
    # v3.2: 다중 에이전트 충돌 관리
    conflict_manager = get_conflict_manager()
    agent_id = agent_config.get("id")
    
    # 도메인 확인
    domain = agent_config.get("domain", "email")
    
    # 도메인별 데이터 로드
    input_data_dict = {}
    if input_data is None:
        # World Model에서 연결된 소스 확인하여 적절한 데이터 로드
        if domain == "email":
            email_path = Path("data/sample_emails.json")
            if email_path.exists():
                with open(email_path, "r", encoding="utf-8") as f:
                    input_data_dict["emails"] = json.load(f)
        elif domain == "github":
            pr_path = Path("data/sample_github_prs.json")
            if pr_path.exists():
                with open(pr_path, "r", encoding="utf-8") as f:
                    input_data_dict["prs"] = json.load(f)
        elif domain == "health":
            health_path = Path("data/sample_health_data.json")
            if health_path.exists():
                with open(health_path, "r", encoding="utf-8") as f:
                    input_data_dict["health"] = json.load(f)
        elif domain == "finance":
            finance_path = Path("data/sample_finance_data.json")
            if finance_path.exists():
                with open(finance_path, "r", encoding="utf-8") as f:
                    input_data_dict["transactions"] = json.load(f)
    else:
        input_data_dict = input_data
    
    # 하위 호환성: emails 파라미터 직접 전달된 경우
    if emails is not None:
        input_data_dict["emails"] = emails
    
    # v3.2: actions 사용 (없으면 workflow 사용 - 하위 호환성)
    actions = agent_config.get("actions", [])
    workflow = agent_config.get("workflow", [])
    
    results = []
    processed_data = {}
    
    # 도메인별 데이터 복사
    if domain == "email":
        processed_data["emails"] = input_data_dict.get("emails", []).copy()
    elif domain == "github":
        processed_data["prs"] = input_data_dict.get("prs", []).copy()
    elif domain == "health":
        processed_data["records"] = input_data_dict.get("health", []).copy()
    elif domain == "finance":
        processed_data["transactions"] = input_data_dict.get("transactions", []).copy()
    
    tool_calls = []
    
    # v3.2: actions 기반 실행 (우선)
    if actions:
        for action_config in actions:
            action_type = action_config.get("type", "")
            action_do = action_config.get("do", "")
            requires_approval = action_config.get("requires_approval", False)
            
            # v3.2 운영 체크리스트: 레이트리밋 체크
            resource = action_config.get("resource", "default")
            rate_limit_check = check_rate_limit(resource, max_requests=100, window_seconds=60)
            if not rate_limit_check["allowed"]:
                results.append({
                    "action": action_do,
                    "status": "rate_limited",
                    "reason": f"레이트리밋 초과. {rate_limit_check['retry_after']:.1f}초 후 재시도 가능",
                    "retry_after": rate_limit_check["retry_after"]
                })
                continue
            
            # Policy 체크
            permission = check_permission(
                action=action_do,
                tool={"name": "unknown"},  # TODO: 실제 도구 매핑
                world_model=world_model,
                agent_config=agent_config
            )
            
            if not permission["allowed"]:
                results.append({
                    "action": action_do,
                    "status": "blocked",
                    "reason": permission["reason"]
                })
                continue
            
            if requires_approval and permission["requires_approval"]:
                # 승인 필요 액션은 실행하지 않고 기록만
                results.append({
                    "action": action_do,
                    "status": "pending_approval",
                    "reason": "사용자 승인이 필요합니다."
                })
                continue
            
            # v3.2 운영 체크리스트: 멱등성 체크
            # 리소스 ID 추출 (도메인별)
            resource_id = None
            if domain == "email" and processed_data.get("emails"):
                resource_id = processed_data["emails"][0].get("id") if processed_data["emails"] else None
            elif domain == "github" and processed_data.get("prs"):
                resource_id = processed_data["prs"][0].get("id") if processed_data["prs"] else None
            
            if resource_id:
                event_id = generate_event_id(action_do, resource_id, {"domain": domain})
                if check_idempotency(event_id):
                    results.append({
                        "action": action_do,
                        "status": "skipped",
                        "reason": "이미 처리된 이벤트입니다 (멱등성)"
                    })
                    continue
                
                # v3.2: 다중 에이전트 충돌 체크
                conflict_check = conflict_manager.check_conflict(
                    agent_id, action_config, resource_id, world_model
                )
                
                if conflict_check["has_conflict"]:
                    # 우선순위에 따라 처리
                    if conflict_check["resolution"] == "agent1_wins":
                        # 락 획득 시도
                        priority = agent_config.get("risk_level", "medium")
                        priority_map = {"low": 5, "medium": 7, "high": 9}
                        priority_score = priority_map.get(priority, 5)
                        
                        if conflict_manager.acquire_lock(agent_id, resource_id, action_config, priority_score):
                            # 락 획득 성공, 계속 진행
                            pass
                        else:
                            results.append({
                                "action": action_do,
                                "status": "conflict",
                                "reason": f"리소스 충돌: {conflict_check['conflicting_agent']}가 사용 중",
                                "conflict_type": conflict_check["conflict_type"]
                            })
                            continue
                    else:
                        results.append({
                            "action": action_do,
                            "status": "conflict",
                            "reason": f"리소스 충돌: 우선순위가 낮음",
                            "conflict_type": conflict_check["conflict_type"]
                        })
                        continue
                else:
                    # 충돌 없으면 락 획득
                    priority = agent_config.get("risk_level", "medium")
                    priority_map = {"low": 5, "medium": 7, "high": 9}
                    priority_score = priority_map.get(priority, 5)
                    conflict_manager.acquire_lock(agent_id, resource_id, action_config, priority_score)
            
            # 액션 실행 (도메인별 시뮬레이션)
            if domain == "email" and "apply_label" in action_do:
                # 이메일 라벨 적용 시뮬레이션
                emails = processed_data.get("emails", [])
                for email in emails:
                    if email.get("hidden_priority") == "high":
                        email["applied_label"] = "Important"
                results.append({
                    "action": action_do,
                    "status": "success",
                    "output": f"라벨 적용 완료: {len([e for e in emails if e.get('hidden_priority') == 'high'])}개"
                })
                # 락 해제
                if resource_id:
                    conflict_manager.release_lock(resource_id)
            elif domain == "github" and "review_pr" in action_do:
                # PR 리뷰 시뮬레이션
                prs = processed_data.get("prs", [])
                reviewed_count = 0
                for pr in prs:
                    if pr.get("review_status") == "pending":
                        pr["review_status"] = "reviewed"
                        reviewed_count += 1
                results.append({
                    "action": action_do,
                    "status": "success",
                    "output": f"PR 리뷰 완료: {reviewed_count}개"
                })
            elif domain == "health" and "track_goal" in action_do:
                # 건강 목표 추적 시뮬레이션
                records = processed_data.get("records", [])
                results.append({
                    "action": action_do,
                    "status": "success",
                    "output": f"건강 데이터 추적: {len(records)}개 기록"
                })
            elif domain == "finance" and "categorize" in action_do:
                # 재정 카테고리화 시뮬레이션
                transactions = processed_data.get("transactions", [])
                results.append({
                    "action": action_do,
                    "status": "success",
                    "output": f"거래 카테고리화 완료: {len(transactions)}개"
                })
            else:
                # 알 수 없는 액션
                results.append({
                    "action": action_do,
                    "status": "skipped",
                    "output": f"도메인 {domain}에 대한 액션 {action_do}는 아직 구현되지 않았습니다."
                })
    
    # 하위 호환성: workflow 기반 실행
    if not actions and workflow:
        for step in workflow:
            action = step.get("action", "")
            tool = step.get("tool", "")
            
            # Policy 체크
            permission = check_permission(
                action=action,
                tool={"name": tool},
                world_model=world_model,
                agent_config=agent_config
            )
            
            if not permission["allowed"]:
                results.append({
                    "step": step.get("step", 0),
                    "action": action,
                    "status": "blocked",
                    "reason": permission["reason"]
                })
                continue
            
            tool_calls.append({
                "name": action,
                "tool": tool,
                "success": True
            })
            
            # 도메인별 액션 처리
            if domain == "email":
                if action == "read_emails":
                    emails = processed_data.get("emails", [])
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"읽은 이메일: {len(emails)}개",
                        "emails_count": len(emails)
                    })
                elif action == "classify_emails":
                    # 이메일 분류 및 라벨 적용
                    emails = processed_data.get("emails", [])
                    classified = []
                    for email in emails:
                        priority = email.get("hidden_priority", "medium")
                        label = "important" if priority == "high" else "normal"
                        
                        # 이메일에 라벨 추가
                        email["applied_label"] = label
                        email["applied_priority"] = priority
                        
                        classified.append({
                            "id": email["id"],
                            "subject": email.get("subject", ""),
                            "priority": priority,
                            "label": label
                        })
                    
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"분류 완료: {len(classified)}개",
                        "classified_emails": classified
                    })
                elif action == "apply_labels":
                    # 라벨 적용 (이미 classify에서 적용됨)
                    emails = processed_data.get("emails", [])
                    labeled_count = sum(1 for e in emails if "applied_label" in e)
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"라벨 적용 완료: {labeled_count}개",
                        "labeled_count": labeled_count
                    })
                elif action == "score_priority":
                    # 우선순위 점수 계산 및 적용
                    emails = processed_data.get("emails", [])
                    for email in emails:
                        priority = email.get("hidden_priority", "medium")
                        priority_score = {"high": 3, "medium": 2, "low": 1}.get(priority, 2)
                        email["priority_score"] = priority_score
                        email["applied_priority"] = priority
                    
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": "우선순위 점수 계산 완료",
                        "scored_count": len(emails)
                    })
                elif action == "sort_emails":
                    # 우선순위 순으로 정렬
                    emails = processed_data.get("emails", [])
                    def get_sort_key(email):
                        priority_score = email.get("priority_score", 2)
                        # 우선순위가 높을수록 앞에 오도록 (내림차순)
                        return -priority_score
                    
                    emails.sort(key=get_sort_key)
                    
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": "정렬 완료 (우선순위 순)",
                        "sorted_emails": [
                            {
                                "id": e["id"],
                                "subject": e.get("subject", ""),
                                "priority": e.get("applied_priority", "medium"),
                                "priority_score": e.get("priority_score", 2)
                            }
                            for e in emails[:10]  # 상위 10개만
                        ]
                    })
                else:
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "skipped",
                        "output": f"이메일 도메인에서 '{action}' 액션은 지원하지 않습니다."
                    })
            
            elif domain == "github":
                if action == "read_prs":
                    prs = processed_data.get("prs", [])
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"읽은 PR: {len(prs)}개",
                        "prs_count": len(prs)
                    })
                elif action == "check_review_status":
                    prs = processed_data.get("prs", [])
                    pending_prs = [pr for pr in prs if pr.get("review_status") == "pending"]
                    old_prs = [pr for pr in pending_prs if pr.get("age_hours", 0) > 48]
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"리뷰 대기 PR: {len(pending_prs)}개, 지연된 PR: {len(old_prs)}개",
                        "pending_count": len(pending_prs),
                        "old_prs_count": len(old_prs)
                    })
                elif action == "notify_review_needed":
                    prs = processed_data.get("prs", [])
                    old_prs = [pr for pr in prs if pr.get("review_status") == "pending" and pr.get("age_hours", 0) > 48]
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"리뷰 알림 전송: {len(old_prs)}개 PR",
                        "notified_count": len(old_prs)
                    })
                elif action == "score_priority":
                    prs = processed_data.get("prs", [])
                    for pr in prs:
                        # PR 우선순위 점수 계산
                        priority_score = 0
                        if pr.get("is_release_branch"):
                            priority_score = 3
                        elif "critical" in pr.get("labels", []):
                            priority_score = 3
                        elif "hotfix" in pr.get("labels", []):
                            priority_score = 3
                        elif pr.get("age_hours", 0) > 48:
                            priority_score = 2
                        else:
                            priority_score = 1
                        pr["priority_score"] = priority_score
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"PR 우선순위 점수 계산 완료: {len(prs)}개",
                        "scored_count": len(prs)
                    })
                elif action == "sort_prs":
                    prs = processed_data.get("prs", [])
                    prs.sort(key=lambda p: -p.get("priority_score", 1))
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": "PR 정렬 완료 (우선순위 순)",
                        "sorted_prs": [{"id": p["id"], "title": p.get("title", ""), "priority_score": p.get("priority_score", 1)} for p in prs[:10]]
                    })
                else:
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "skipped",
                        "output": f"GitHub 도메인에서 '{action}' 액션은 지원하지 않습니다."
                    })
            
            elif domain == "health":
                if action == "read_health":
                    records = processed_data.get("records", [])
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"읽은 건강 데이터: {len(records)}개",
                        "records_count": len(records)
                    })
                elif action == "analyze_sleep":
                    records = processed_data.get("records", [])
                    avg_sleep = sum(r.get("sleep", {}).get("duration_hours", 0) for r in records) / len(records) if records else 0
                    sleep_deficit = avg_sleep < 7
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"수면 분석 완료: 평균 {avg_sleep:.1f}시간",
                        "average_sleep": avg_sleep,
                        "sleep_deficit": sleep_deficit
                    })
                elif action == "analyze_patterns":
                    records = processed_data.get("records", [])
                    avg_sleep = sum(r.get("sleep", {}).get("duration_hours", 0) for r in records) / len(records) if records else 0
                    avg_steps = sum(r.get("activity", {}).get("steps", 0) for r in records) / len(records) if records else 0
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"건강 패턴 분석 완료: 평균 수면 {avg_sleep:.1f}시간, 평균 걸음 {avg_steps:.0f}걸음",
                        "average_sleep": avg_sleep,
                        "average_steps": avg_steps
                    })
                elif action == "send_alert":
                    records = processed_data.get("records", [])
                    avg_sleep = sum(r.get("sleep", {}).get("duration_hours", 0) for r in records) / len(records) if records else 0
                    alert_sent = avg_sleep < 7
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"건강 알림 전송: {'수면 부족 경고' if alert_sent else '정상 상태'}",
                        "alert_sent": alert_sent
                    })
                else:
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "skipped",
                        "output": f"건강 도메인에서 '{action}' 액션은 지원하지 않습니다."
                    })
            
            elif domain == "finance":
                if action == "read_transactions":
                    transactions = processed_data.get("transactions", [])
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "success",
                        "output": f"읽은 거래: {len(transactions)}개",
                        "transactions_count": len(transactions)
                    })
                else:
                    results.append({
                        "step": step["step"],
                        "action": action,
                        "status": "skipped",
                        "output": f"재정 도메인에서 '{action}' 액션은 지원하지 않습니다."
                    })
            
            else:
                # 알 수 없는 도메인
                results.append({
                    "step": step["step"],
                    "action": action,
                    "status": "skipped",
                    "output": f"도메인 '{domain}'는 지원하지 않습니다."
                })
    
    # 도메인별 처리된 데이터 반환
    processed_output = {}
    if domain == "email":
        processed_output["processed_emails"] = processed_data.get("emails", [])
        processed_count = len([e for e in processed_data.get("emails", []) if "applied_label" in e])
        total_items = len(processed_data.get("emails", []))
    elif domain == "github":
        processed_output["processed_prs"] = processed_data.get("prs", [])
        processed_count = len([p for p in processed_data.get("prs", []) if p.get("review_status") == "reviewed"])
        total_items = len(processed_data.get("prs", []))
    elif domain == "health":
        processed_output["processed_records"] = processed_data.get("records", [])
        processed_count = len(processed_data.get("records", []))
        total_items = len(processed_data.get("records", []))
    elif domain == "finance":
        processed_output["processed_transactions"] = processed_data.get("transactions", [])
        processed_count = len(processed_data.get("transactions", []))
        total_items = len(processed_data.get("transactions", []))
    else:
        processed_count = 0
        total_items = 0
    
    # v3.2 운영 체크리스트: 부분 실패 처리
    failure_analysis = handle_partial_failure(results, max_retries=3)
    
    execution_result = {
        "agent_id": agent_config.get("id"),
        "solution_name": agent_config.get("solution_name"),
        "domain": domain,
        "status": "completed",
        "workflow_results": results,
        **processed_output,  # 도메인별 처리된 데이터
        "summary": {
            "total_steps": len(workflow) if workflow else len(actions),
            "completed_steps": len([r for r in results if r.get("status") == "success"]),
            "blocked_steps": len([r for r in results if r.get("status") == "blocked"]),
            "pending_approval": len([r for r in results if r.get("status") == "pending_approval"]),
            "rate_limited": len([r for r in results if r.get("status") == "rate_limited"]),
            "skipped_idempotent": len([r for r in results if r.get("status") == "skipped"]),
            "success_rate": len([r for r in results if r.get("status") == "success"]) / max(len(results), 1),
            "total_items": total_items,
            "processed_count": processed_count,
            "failure_analysis": failure_analysis  # 부분 실패 분석 결과
        }
    }
    
    # Observability: 실행 로깅
    try:
        log_agent_execution(
            agent_config=agent_config,
            execution_result=execution_result,
            trigger_event_id=None  # TODO: 실제 트리거 이벤트 ID
        )
    except Exception as e:
        # 로깅 실패는 실행을 중단하지 않음
        print(f"로깅 실패: {e}")
    
    return execution_result

