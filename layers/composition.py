"""
Composition Layer: 솔루션을 구현하기 위한 LLM과 도구를 동적으로 선택하고 조합하는 계층
"""

from typing import Dict, Any, List


def compose_agent(solution: Dict[str, Any]) -> Dict[str, Any]:
    """
    솔루션을 구현하기 위한 에이전트 구성을 생성합니다.
    
    Args:
        solution: 승인된 솔루션
        
    Returns:
        에이전트 구성 딕셔너리
    """
    required_tools = solution.get("required_tools", [])
    
    # 도구별 매핑
    tool_mapping = {
        "email_reader": {
            "type": "mcp",
            "name": "email_reader",
            "description": "이메일 데이터 읽기",
            "implementation": "load_sample_emails"
        },
        "classifier": {
            "type": "llm",
            "name": "email_classifier",
            "description": "이메일 분류",
            "model": "claude-3-5-sonnet-20241022"
        },
        "label_applier": {
            "type": "mcp",
            "name": "label_applier",
            "description": "라벨 적용",
            "implementation": "apply_labels"
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
        "notification": {
            "type": "mcp",
            "name": "notification",
            "description": "알림 전송",
            "implementation": "send_notification"
        },
        "summarizer": {
            "type": "llm",
            "name": "email_summarizer",
            "description": "이메일 요약",
            "model": "claude-3-5-sonnet-20241022"
        },
        "report_generator": {
            "type": "llm",
            "name": "report_generator",
            "description": "리포트 생성",
            "model": "claude-3-5-sonnet-20241022"
        }
    }
    
    # 필요한 도구들 구성
    tools = [tool_mapping.get(tool, {
        "type": "unknown",
        "name": tool,
        "description": "도구 설명 필요"
    }) for tool in required_tools]
    
    return {
        "id": f"agent_{solution.get('id', 'unknown')}",
        "solution_id": solution.get("id"),
        "solution_name": solution.get("name"),
        "llm": {
            "provider": "anthropic",
            "model": "claude-3-5-sonnet-20241022"
        },
        "tools": tools,
        "workflow": generate_workflow(solution, tools)
    }


def generate_workflow(solution: Dict[str, Any], tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    솔루션에 맞는 워크플로우를 생성합니다.
    
    Args:
        solution: 솔루션
        tools: 구성된 도구 리스트
        
    Returns:
        워크플로우 단계 리스트
    """
    solution_name = solution.get("name", "")
    
    if "자동 분류" in solution_name:
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

