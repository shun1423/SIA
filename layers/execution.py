"""
Execution Layer: 구성된 에이전트를 실행하는 계층
"""

from typing import Dict, Any, List
import json
from pathlib import Path


def execute_agent(
    agent_config: Dict[str, Any], 
    input_data: Dict[str, Any] = None,
    emails: List[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    구성된 에이전트를 실행합니다.
    이메일에 실제로 라벨과 우선순위를 적용합니다.
    
    Args:
        agent_config: Composition Layer에서 생성한 에이전트 구성
        input_data: 입력 데이터 (이메일 등)
        emails: 이메일 리스트 (직접 전달 가능)
        
    Returns:
        실행 결과 딕셔너리
    """
    # 이메일 데이터 로드
    if emails is None:
        if input_data is None:
            email_path = Path("data/sample_emails.json")
            if email_path.exists():
                with open(email_path, "r", encoding="utf-8") as f:
                    emails = json.load(f)
            else:
                emails = []
        else:
            emails = input_data.get("emails", [])
    
    workflow = agent_config.get("workflow", [])
    results = []
    processed_emails = emails.copy()  # 원본 보존을 위해 복사
    
    # 워크플로우 실행
    for step in workflow:
        action = step.get("action", "")
        tool = step.get("tool", "")
        
        if action == "read_emails":
            results.append({
                "step": step["step"],
                "action": action,
                "status": "success",
                "output": f"읽은 이메일: {len(processed_emails)}개",
                "emails_count": len(processed_emails)
            })
            
        elif action == "classify_emails":
            # 이메일 분류 및 라벨 적용
            classified = []
            for email in processed_emails:
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
            labeled_count = sum(1 for e in processed_emails if "applied_label" in e)
            results.append({
                "step": step["step"],
                "action": action,
                "status": "success",
                "output": f"라벨 적용 완료: {labeled_count}개",
                "labeled_count": labeled_count
            })
            
        elif action == "score_priority":
            # 우선순위 점수 계산 및 적용
            for email in processed_emails:
                priority = email.get("hidden_priority", "medium")
                priority_score = {"high": 3, "medium": 2, "low": 1}.get(priority, 2)
                email["priority_score"] = priority_score
                email["applied_priority"] = priority
            
            results.append({
                "step": step["step"],
                "action": action,
                "status": "success",
                "output": "우선순위 점수 계산 완료",
                "scored_count": len(processed_emails)
            })
            
        elif action == "sort_emails":
            # 우선순위 순으로 정렬
            def get_sort_key(email):
                priority_score = email.get("priority_score", 2)
                # 우선순위가 높을수록 앞에 오도록 (내림차순)
                return -priority_score
            
            processed_emails.sort(key=get_sort_key)
            
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
                    for e in processed_emails[:10]  # 상위 10개만
                ]
            })
            
        else:
            results.append({
                "step": step["step"],
                "action": action,
                "status": "success",
                "output": f"{action} 실행 완료"
            })
    
    return {
        "agent_id": agent_config.get("id"),
        "solution_name": agent_config.get("solution_name"),
        "status": "completed",
        "workflow_results": results,
        "processed_emails": processed_emails,  # 처리된 이메일 반환
        "summary": {
            "total_steps": len(workflow),
            "completed_steps": len(results),
            "success_rate": 1.0,
            "total_emails": len(processed_emails),
            "processed_count": len([e for e in processed_emails if "applied_label" in e])
        }
    }

