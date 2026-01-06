"""
Composition Layer: 솔루션을 구현하기 위한 LLM과 도구를 동적으로 선택하고 조합하는 계층
v3.2 업데이트: 에이전트 구성 요소 확장 (트리거, 입력, 도구, 처리 로직, 실행 액션, 안전 정책)
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

# World Model 로드용
import sys
sys.path.append(str(Path(__file__).parent.parent))


def compose_agent(
    solution: Dict[str, Any],
    problem: Optional[Dict[str, Any]] = None,
    world_model: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    솔루션을 구현하기 위한 에이전트 구성을 생성합니다.
    v3.2 업데이트: 트리거, 입력, 도구, 처리 로직, 실행 액션, 안전 정책 포함
    
    Args:
        solution: 승인된 솔루션
        problem: 확정된 문제 (선택적)
        world_model: World Model 데이터 (선택적)
        
    Returns:
        에이전트 구성 딕셔너리 (v3.2 스펙 준수)
    """
    # World Model 로드 (없으면 기본값)
    if world_model is None:
        from layers.expectation import load_world_model
        world_model = load_world_model()
    
    required_tools = solution.get("required_tools", [])
    solution_name = solution.get("name", "")
    
    # 도메인 결정: 온보딩 데이터에서만 가져오기 (기본값 없음)
    solution_domain = None
    
    # 1순위: problem에서 도메인 가져오기
    if problem and problem.get("domain"):
        solution_domain = problem.get("domain")
    # 2순위: solution에서 도메인 가져오기
    elif solution and solution.get("domain"):
        solution_domain = solution.get("domain")
    # 3순위: World Model의 connected_sources에서 도메인 추출
    elif world_model and world_model.get("connected_sources"):
        source_to_domain = {
            "Gmail": "email",
            "GitHub": "github",
            "Apple Health": "health"
        }
        active_sources = [s for s in world_model["connected_sources"] if s.get("status") == "active"]
        if active_sources:
            # problem의 도메인과 일치하는 소스 찾기
            if problem and problem.get("domain"):
                # problem의 도메인과 일치하는 소스가 있는지 확인
                problem_domain = problem.get("domain")
                for source in active_sources:
                    source_name = source.get("name", "")
                    if source_to_domain.get(source_name) == problem_domain:
                        solution_domain = problem_domain
                        break
                else:
                    # 일치하는 소스가 없으면 첫 번째 소스 사용
                    first_source_name = active_sources[0].get("name", "")
                    solution_domain = source_to_domain.get(first_source_name)
            else:
                # problem이 없으면 첫 번째 소스 사용
                first_source_name = active_sources[0].get("name", "")
                solution_domain = source_to_domain.get(first_source_name)
    
    # 도메인을 찾을 수 없으면 에러
    if not solution_domain:
        raise ValueError(
            "도메인을 결정할 수 없습니다. "
            "온보딩에서 데이터 소스를 연결했는지 확인하거나, "
            "problem이나 solution에 domain 정보가 포함되어 있는지 확인하세요."
        )
    
    risk_level = solution.get("risk_level", "low")
    
    # 1. 트리거(Trigger) 구성
    trigger = _generate_trigger(solution, problem, solution_domain)
    
    # 2. 입력(Inputs) 구성
    inputs = _generate_inputs(solution, solution_domain)
    
    # 3. 도구(Tools/MCP) 구성
    tools = _generate_tools(required_tools, world_model, solution_domain)
    
    # 4. 처리 로직(Logic) 구성
    logic = _generate_logic(solution, solution_domain)
    
    # 5. 실행 액션(Actions) 구성
    actions = _generate_actions(solution, solution_domain, tools)
    
    # 6. 안전 정책(Safety) 구성
    safety = _generate_safety_policy(solution, world_model, risk_level)
    
    # 에이전트 ID 생성
    agent_id = f"agent_{solution.get('id', 'unknown')}_{datetime.now().strftime('%Y%m%d')}"
    
    return {
        "id": agent_id,
        "solution_id": solution.get("id"),
        "solution_name": solution_name,
        "domain": solution_domain,
        "risk_level": risk_level,
        "created_at": datetime.now().isoformat(),
        
        # v3.2 에이전트 구성 요소
        "trigger": trigger,
        "inputs": inputs,
        "tools": tools,
        "logic": logic,
        "actions": actions,
        "safety": safety,
        
        # 하위 호환성을 위한 레거시 필드
        "llm": {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022"
        },
        "workflow": generate_workflow(solution, tools, solution_domain)
    }


def _generate_trigger(
    solution: Dict[str, Any],
    problem: Optional[Dict[str, Any]],
    domain: str
) -> Dict[str, Any]:
    """
    트리거를 생성합니다.
    
    Args:
        solution: 솔루션
        problem: 문제
        domain: 도메인
        
    Returns:
        트리거 딕셔너리
    """
    solution_name = solution.get("name", "")
    
    # 도메인별 기본 트리거
    if domain == "email":
        if "분류" in solution_name or "우선순위" in solution_name:
            return {
                "type": "event",
                "source": "gmail",
                "event": "new_email",
                "description": "새 메일 도착 시 실행"
            }
        elif "요약" in solution_name or "리포트" in solution_name:
            return {
                "type": "schedule",
                "cron": "0 9 * * *",  # 매일 오전 9시
                "description": "매일 오전 9시 실행"
            }
    elif domain == "calendar":
        return {
            "type": "schedule",
            "cron": "0 8 * * *",  # 매일 오전 8시
            "description": "매일 오전 8시 실행"
        }
    elif domain == "github" or domain == "개발":
        if "리뷰" in solution_name:
            return {
                "type": "event",
                "source": "github",
                "event": "new_pr",
                "description": "새 PR이 생성되거나 리뷰가 필요할 때"
            }
        else:
            return {
                "type": "schedule",
                "cron": "0 10 * * 1-5",  # 평일 오전 10시
                "description": "평일 오전 10시 실행"
            }
    elif domain == "health":
        return {
            "type": "schedule",
            "cron": "0 8 * * *",  # 매일 오전 8시
            "description": "매일 오전 8시에 건강 데이터 확인"
        }
    elif domain == "finance":
        return {
            "type": "schedule",
            "cron": "0 22 * * *",  # 매일 오후 10시
            "description": "매일 오후 10시에 지출 내역 확인"
        }
    
    # 기본값: 이벤트 기반
    return {
        "type": "event",
        "source": domain,
        "event": "data_update",
        "description": "데이터 업데이트 시 실행"
    }


def _generate_inputs(
    solution: Dict[str, Any],
    domain: str
) -> Dict[str, Any]:
    """
    입력을 생성합니다.
    
    Args:
        solution: 솔루션
        domain: 도메인
        
    Returns:
        입력 딕셔너리
    """
    # 도메인별 기본 입력 범위
    scope_map = {
        "email": "metadata_and_subject",  # 메타데이터와 제목만 (본문 제외)
        "calendar": "event_metadata",
        "github": "pr_metadata",
        "health": "aggregated_metrics",
        "finance": "transaction_metadata"
    }
    
    scope = scope_map.get(domain, "metadata")
    
    return {
        "scope": scope,
        "description": f"{domain} 도메인의 {scope} 데이터를 읽습니다",
        "sensitivity": "low" if scope == "metadata" else "medium"
    }


def _generate_tools(
    required_tools: List[str],
    world_model: Dict[str, Any],
    domain: str
) -> List[Dict[str, Any]]:
    """
    도구를 생성합니다.
    
    Args:
        required_tools: 필요한 도구 리스트
        world_model: World Model 데이터
        domain: 도메인
        
    Returns:
        도구 리스트
    """
    # 연결된 소스 확인
    connected_sources = world_model.get("connected_sources", [])
    source_map = {s.get("name", "").lower(): s for s in connected_sources}
    
    # 도메인별 도구 매핑
    domain_tool_mappings = {
        "email": {
            "email_reader": {
                "type": "mcp",
                "name": "gmail",
                "description": "이메일 데이터 읽기",
                "permissions": {"read": ["metadata", "subject"], "write": []}
            },
            "classifier": {
                "type": "llm",
                "name": "email_classifier",
                "description": "이메일 분류",
                "model": "claude-3-5-sonnet-20241022"
            },
            "label_applier": {
                "type": "mcp",
                "name": "gmail",
                "description": "라벨 적용",
                "permissions": {"read": [], "write": ["apply_label"]}
            },
            "priority_scorer": {
                "type": "llm",
                "name": "priority_scorer",
                "description": "우선순위 점수 계산",
                "model": "claude-3-5-sonnet-20241022"
            },
            "sorter": {
                "type": "function",
                "name": "email_sorter",
                "description": "이메일 정렬",
                "implementation": "sort_emails_by_priority"
            },
            "summarizer": {
                "type": "llm",
                "name": "email_summarizer",
                "description": "이메일 요약",
                "model": "claude-3-5-sonnet-20241022"
            }
        },
        "github": {
            "pr_reader": {
                "type": "mcp",
                "name": "github",
                "description": "PR 데이터 읽기",
                "permissions": {"read": ["metadata", "title", "status"], "write": []}
            },
            "reviewer": {
                "type": "llm",
                "name": "pr_reviewer",
                "description": "PR 리뷰",
                "model": "claude-3-5-sonnet-20241022"
            },
            "notifier": {
                "type": "mcp",
                "name": "slack",
                "description": "리뷰 알림",
                "permissions": {"read": [], "write": ["send_dm"]}
            },
            "priority_scorer": {
                "type": "llm",
                "name": "pr_priority_scorer",
                "description": "PR 우선순위 계산",
                "model": "claude-3-5-sonnet-20241022"
            }
        },
        "health": {
            "health_reader": {
                "type": "mcp",
                "name": "apple_health",
                "description": "건강 데이터 읽기",
                "permissions": {"read": ["sleep", "activity"], "write": []}
            },
            "analyzer": {
                "type": "llm",
                "name": "health_analyzer",
                "description": "건강 패턴 분석",
                "model": "claude-3-5-sonnet-20241022"
            },
            "notifier": {
                "type": "mcp",
                "name": "notification",
                "description": "건강 알림",
                "permissions": {"read": [], "write": ["push_notification"]}
            }
        },
        "finance": {
            "transaction_reader": {
                "type": "mcp",
                "name": "finance_app",
                "description": "거래 내역 읽기",
                "permissions": {"read": ["amount", "category"], "write": []}
            },
            "categorizer": {
                "type": "llm",
                "name": "transaction_categorizer",
                "description": "거래 카테고리화",
                "model": "claude-3-5-sonnet-20241022"
            },
            "analyzer": {
                "type": "llm",
                "name": "spending_analyzer",
                "description": "지출 패턴 분석",
                "model": "claude-3-5-sonnet-20241022"
            }
        }
    }
    
    # 공통 도구 (모든 도메인에서 사용 가능)
    common_tools = {
        "notification": {
            "type": "mcp",
            "name": "notification",
            "description": "알림 전송",
            "permissions": {"read": [], "write": ["send_dm", "push_notification"]}
        },
        "report_generator": {
            "type": "llm",
            "name": "report_generator",
            "description": "리포트 생성",
            "model": "claude-3-5-sonnet-20241022"
        }
    }
    
    # 도메인별 도구 매핑 선택
    tool_mapping = domain_tool_mappings.get(domain, domain_tool_mappings["email"])
    
    # 필요한 도구들 구성
    tools = []
    for tool_name in required_tools:
        tool = None
        
        # 1. 도메인별 도구 매핑에서 찾기
        if tool_name in tool_mapping:
            tool = tool_mapping[tool_name].copy()
        # 2. 공통 도구에서 찾기
        elif tool_name in common_tools:
            tool = common_tools[tool_name].copy()
        # 3. 다른 도메인의 도구에서 찾기 (호환성)
        else:
            for other_domain, other_mapping in domain_tool_mappings.items():
                if tool_name in other_mapping:
                    tool = other_mapping[tool_name].copy()
                    break
        
        if tool:
            # MCP 도구인 경우 연결된 소스 확인
            if tool["type"] == "mcp":
                source_name = tool["name"]
                if source_name.lower() in source_map:
                    source = source_map[source_name.lower()]
                    tool["source_id"] = source.get("id")
                    tool["permissions"] = source.get("permissions", tool.get("permissions", {}))
                    # MCP 시뮬레이터 연결 정보 추가
                    tool["mcp_simulator"] = {
                        "source_name": source_name,
                        "permissions": source.get("permissions", {})
                    }
            tools.append(tool)
        else:
            # 알 수 없는 도구는 기본 구조로 생성
            tools.append({
                "type": "unknown",
                "name": tool_name,
                "description": f"{domain} 도메인용 {tool_name} 도구"
            })
    
    return tools


def _generate_logic(
    solution: Dict[str, Any],
    domain: str
) -> Dict[str, Any]:
    """
    처리 로직을 생성합니다.
    
    Args:
        solution: 솔루션
        domain: 도메인
        
    Returns:
        로직 딕셔너리
    """
    solution_name = solution.get("name", "")
    
    # 규칙 기반 로직
    rules = []
    
    # 도메인별 규칙 생성
    if domain == "email":
        if "분류" in solution_name:
            rules.append({
                "if": "sender in VIP_LIST",
                "then": "importance = high"
            })
            rules.append({
                "if": "subject contains ['마감', '긴급', '요청']",
                "then": "importance = high"
            })
        elif "우선순위" in solution_name:
            rules.append({
                "if": "hidden_priority == 'high'",
                "then": "priority_score = 3"
            })
    elif domain == "github":
        if "리뷰" in solution_name:
            rules.append({
                "if": "pr.age_hours > 48",
                "then": "review_priority = high"
            })
            rules.append({
                "if": "pr.is_release_branch == true",
                "then": "review_priority = high"
            })
    elif domain == "health":
        if "수면" in solution_name:
            rules.append({
                "if": "sleep.duration_hours < 7",
                "then": "alert = true"
            })
    elif domain == "finance":
        if "지출" in solution_name:
            rules.append({
                "if": "category == '배달앱' and weekly_total > 50000",
                "then": "alert = true"
            })
    
    # LLM 기반 로직 (도메인별)
    llm_task_map = {
        "email": "classify_importance" if "분류" in solution_name else "score_priority",
        "github": "review_priority" if "리뷰" in solution_name else "score_priority",
        "health": "analyze_sleep" if "수면" in solution_name else "analyze_patterns",
        "finance": "categorize_transactions" if "카테고리" in solution_name else "analyze_spending"
    }
    
    llm_logic = {
        "enabled": True,
        "task": llm_task_map.get(domain, "process"),
        "model": "claude-3-5-sonnet-20241022"
    }
    
    return {
        "rules": rules,
        "llm": llm_logic
    }


def _generate_actions(
    solution: Dict[str, Any],
    domain: str,
    tools: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    실행 액션을 생성합니다.
    
    Args:
        solution: 솔루션
        domain: 도메인
        tools: 도구 리스트
        
    Returns:
        액션 리스트
    """
    solution_name = solution.get("name", "")
    actions = []
    
    # 도메인별 액션 생성
    if domain == "email":
        if "분류" in solution_name:
            actions.append({
                "if": "importance == high",
                "do": "gmail.apply_label('⭐_Important')",
                "type": "write",
                "requires_approval": True
            })
            actions.append({
                "schedule": "daily_09:00",
                "do": "notification.send_dm(daily_summary)",
                "type": "notification",
                "requires_approval": False
            })
        elif "우선순위" in solution_name:
            actions.append({
                "do": "sort_emails_by_priority()",
                "type": "read",
                "requires_approval": False
            })
    
    elif domain == "github":
        if "리뷰" in solution_name:
            actions.append({
                "if": "pr.review_status == 'pending' and pr.age_hours > 48",
                "do": "slack.send_dm(f'PR 리뷰 필요: {pr.title}')",
                "type": "notification",
                "requires_approval": False
            })
            actions.append({
                "if": "pr.is_release_branch == true",
                "do": "slack.send_dm(f'릴리스 PR 리뷰 필요: {pr.title}')",
                "type": "notification",
                "requires_approval": False
            })
        elif "우선순위" in solution_name:
            actions.append({
                "do": "sort_prs_by_priority()",
                "type": "read",
                "requires_approval": False
            })
    
    elif domain == "health":
        if "수면" in solution_name:
            actions.append({
                "if": "sleep.duration_hours < 7",
                "do": "notification.send_push('수면 시간이 부족합니다. 평균 {sleep.duration_hours}시간')",
                "type": "notification",
                "requires_approval": False
            })
        elif "패턴" in solution_name:
            actions.append({
                "schedule": "daily_08:00",
                "do": "notification.send_push(health_summary)",
                "type": "notification",
                "requires_approval": False
            })
    
    elif domain == "finance":
        if "지출" in solution_name:
            actions.append({
                "if": "weekly_spending > limit",
                "do": "notification.send_dm(f'주간 지출 한도 초과: {weekly_spending}원')",
                "type": "notification",
                "requires_approval": False
            })
        elif "카테고리" in solution_name:
            actions.append({
                "do": "categorize_transactions()",
                "type": "read",
                "requires_approval": False
            })
    
    # 기본 액션 (도메인별)
    if not actions:
        if domain == "email":
            actions.append({
                "do": "process_emails()",
                "type": "read",
                "requires_approval": False
            })
        elif domain == "github":
            actions.append({
                "do": "process_prs()",
                "type": "read",
                "requires_approval": False
            })
        elif domain == "health":
            actions.append({
                "do": "process_health_data()",
                "type": "read",
                "requires_approval": False
            })
        elif domain == "finance":
            actions.append({
                "do": "process_transactions()",
                "type": "read",
                "requires_approval": False
            })
    
    return actions


def _generate_safety_policy(
    solution: Dict[str, Any],
    world_model: Dict[str, Any],
    risk_level: str
) -> Dict[str, Any]:
    """
    안전 정책을 생성합니다.
    
    Args:
        solution: 솔루션
        world_model: World Model 데이터
        risk_level: 리스크 레벨
        
    Returns:
        안전 정책 딕셔너리
    """
    safety = world_model.get("safety", {})
    policy = safety.get("policy", {})
    
    # 리스크 레벨별 승인 정책
    approval_policy = {
        "low": {
            "write_operations": "auto_approve",
            "high_risk_actions": "require_approval"
        },
        "medium": {
            "write_operations": "require_approval",
            "high_risk_actions": "require_approval"
        },
        "high": {
            "write_operations": "require_approval",
            "high_risk_actions": "block"
        }
    }
    
    return {
        "risk_level": risk_level,
        "default_write_block": policy.get("default_write_block", True),
        "action_allowlist": policy.get("action_allowlist", []),
        "forbidden_actions": policy.get("forbidden_actions", []),
        "approval_policy": approval_policy.get(risk_level, approval_policy["medium"]),
        "requires_approval": risk_level != "low"
    }


def generate_workflow(solution: Dict[str, Any], tools: List[Dict[str, Any]], domain: str = "email") -> List[Dict[str, Any]]:
    """
    솔루션에 맞는 워크플로우를 생성합니다. (하위 호환성 유지)
    v3.2 업데이트: 도메인별 워크플로우 지원
    
    Args:
        solution: 솔루션
        tools: 구성된 도구 리스트
        domain: 도메인 (기본값: email)
        
    Returns:
        워크플로우 단계 리스트
    """
    solution_name = solution.get("name", "")
    
    # 도메인별 워크플로우 생성
    if domain == "email":
        if "자동 분류" in solution_name or "분류" in solution_name:
            return [
                {"step": 1, "action": "read_emails", "tool": "email_reader"},
                {"step": 2, "action": "classify_emails", "tool": "classifier"},
                {"step": 3, "action": "apply_labels", "tool": "label_applier"},
                {"step": 4, "action": "sort_emails", "tool": "sorter"}
            ]
        elif "우선순위" in solution_name:
            return [
                {"step": 1, "action": "read_emails", "tool": "email_reader"},
                {"step": 2, "action": "score_priority", "tool": "priority_scorer"},
                {"step": 3, "action": "sort_emails", "tool": "sorter"}
            ]
        else:
            return [
                {"step": 1, "action": "read_emails", "tool": "email_reader"},
                {"step": 2, "action": "process", "tool": tools[0]["name"] if tools else "unknown"}
            ]
    
    elif domain == "github":
        if "리뷰" in solution_name:
            return [
                {"step": 1, "action": "read_prs", "tool": "pr_reader"},
                {"step": 2, "action": "check_review_status", "tool": "reviewer"},
                {"step": 3, "action": "notify_review_needed", "tool": "notifier"}
            ]
        elif "우선순위" in solution_name:
            return [
                {"step": 1, "action": "read_prs", "tool": "pr_reader"},
                {"step": 2, "action": "score_priority", "tool": "priority_scorer"},
                {"step": 3, "action": "sort_prs", "tool": "sorter"}
            ]
        else:
            return [
                {"step": 1, "action": "read_prs", "tool": "pr_reader"},
                {"step": 2, "action": "process", "tool": tools[0]["name"] if tools else "unknown"}
            ]
    
    elif domain == "health":
        if "수면" in solution_name:
            return [
                {"step": 1, "action": "read_health", "tool": "health_reader"},
                {"step": 2, "action": "analyze_sleep", "tool": "analyzer"},
                {"step": 3, "action": "send_alert", "tool": "notifier"}
            ]
        elif "패턴" in solution_name:
            return [
                {"step": 1, "action": "read_health", "tool": "health_reader"},
                {"step": 2, "action": "analyze_patterns", "tool": "analyzer"}
            ]
        else:
            return [
                {"step": 1, "action": "read_health", "tool": "health_reader"},
                {"step": 2, "action": "process", "tool": tools[0]["name"] if tools else "unknown"}
            ]
    
    elif domain == "finance":
        if "지출" in solution_name:
            return [
                {"step": 1, "action": "read_transactions", "tool": "transaction_reader"},
                {"step": 2, "action": "analyze_spending", "tool": "analyzer"},
                {"step": 3, "action": "send_alert", "tool": "notifier"}
            ]
        elif "카테고리" in solution_name:
            return [
                {"step": 1, "action": "read_transactions", "tool": "transaction_reader"},
                {"step": 2, "action": "categorize", "tool": "categorizer"}
            ]
        else:
            return [
                {"step": 1, "action": "read_transactions", "tool": "transaction_reader"},
                {"step": 2, "action": "process", "tool": tools[0]["name"] if tools else "unknown"}
            ]
    
    # 기본 워크플로우 (알 수 없는 도메인)
    return [
        {"step": 1, "action": "read_data", "tool": tools[0]["name"] if tools else "unknown"},
        {"step": 2, "action": "process", "tool": tools[1]["name"] if len(tools) > 1 else "unknown"}
    ]

