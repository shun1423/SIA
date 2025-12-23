"""
Learning Layer: 실행 결과를 관찰하고 World Model을 업데이트하는 계층
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime


def analyze_results(execution_result: Dict[str, Any], user_feedback: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    실행 결과를 분석합니다.
    
    Args:
        execution_result: Execution Layer의 실행 결과
        user_feedback: 사용자 피드백 (선택적)
        
    Returns:
        분석 결과 딕셔너리
    """
    workflow_results = execution_result.get("workflow_results", [])
    
    # 성공률 계산
    success_count = sum(1 for r in workflow_results if r.get("status") == "success")
    total_count = len(workflow_results)
    success_rate = success_count / total_count if total_count > 0 else 0
    
    # 처리된 항목 수
    processed_items = 0
    for result in workflow_results:
        if "classified_emails" in result:
            processed_items = len(result["classified_emails"])
    
    return {
        "success_rate": success_rate,
        "processed_items": processed_items,
        "user_satisfaction": user_feedback.get("satisfaction", 0.5) if user_feedback else 0.5,
        "feedback": user_feedback,
        "timestamp": datetime.now().isoformat()
    }


def update_world_model(
    analysis_result: Dict[str, Any],
    world_model_path: str = "data/world_model.json"
) -> Dict[str, Any]:
    """
    분석 결과를 바탕으로 World Model을 업데이트합니다.
    
    Args:
        analysis_result: Learning Layer의 분석 결과
        world_model_path: World Model 파일 경로
        
    Returns:
        업데이트된 World Model
    """
    file_path = Path(world_model_path)
    
    if not file_path.exists():
        return {}
    
    # World Model 로드
    with open(file_path, "r", encoding="utf-8") as f:
        world_model = json.load(f)
    
    # 간단한 업데이트 예시
    # 실제로는 더 정교한 학습 로직이 필요
    
    # 성공률이 높고 사용자 만족도가 높으면 패턴 추가
    if analysis_result.get("success_rate", 0) > 0.8 and analysis_result.get("user_satisfaction", 0) > 0.7:
        # 새로운 패턴 추가 예시
        new_pattern = {
            "id": f"pattern_{len(world_model.get('patterns', [])) + 1}",
            "type": "learned",
            "behavior": "자동 분류 시스템 사용",
            "domain": "email",
            "learned_at": datetime.now().isoformat()
        }
        
        if "patterns" not in world_model:
            world_model["patterns"] = []
        world_model["patterns"].append(new_pattern)
    
    # 업데이트 시간 갱신
    world_model["updated_at"] = datetime.now().isoformat()
    
    # 파일 저장
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(world_model, f, ensure_ascii=False, indent=2)
    
    return world_model

