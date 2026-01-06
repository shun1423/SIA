"""
Onboarding Layer: 사용자 온보딩 플로우 구현
v3.2 스펙에 따른 온보딩 프로세스
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json


# 추상적 목표 옵션
ABSTRACT_GOAL_OPTIONS = [
    "업무 효율 높이고 싶어",
    "중요한 거 놓치지 않고 싶어",
    "개발 생산성 높이고 싶어",
    "뭔가 비효율적인데 뭔지 모르겠어"
]

# 데이터 소스 옵션
DATA_SOURCE_OPTIONS = {
    "업무/커뮤니케이션": [
        {"name": "Gmail", "description": "이메일 패턴 분석 및 중요 메일 관리", "category": "communication"}
    ],
    "개발": [
        {"name": "GitHub", "description": "PR/이슈 처리 패턴 분석", "category": "development"}
    ],
    "건강/습관": [
        {"name": "Apple Health", "description": "수면, 운동 패턴 분석", "category": "health"}
    ],
    "재정/지출": [
        {"name": "Finance App", "description": "카드/은행 거래 내역 분석 및 지출 패턴 관리", "category": "finance"}
    ]
}

# 개입 빈도 옵션
INTERVENTION_FREQUENCY_OPTIONS = [
    {"value": "aggressive", "label": "적극적으로 알려줘", "description": "문제 발견할 때마다"},
    {"value": "moderate", "label": "적당히", "description": "중요한 것만"},
    {"value": "minimal", "label": "최소한으로", "description": "주간 요약만"}
]

# 자동화 수준 옵션
AUTOMATION_LEVEL_OPTIONS = [
    {"value": "proposal_only", "label": "제안만 해줘", "description": "실행은 내가 결정"},
    {"value": "simple_auto", "label": "간단한 건 알아서 해도 돼", "description": "낮은 리스크만 자동 실행"}
]


def create_onboarding_data(
    abstract_goals: List[str],
    connected_sources: List[str],
    intervention_frequency: str = "moderate",
    automation_level: str = "proposal_only"
) -> Dict[str, Any]:
    """
    온보딩 데이터를 기반으로 World Model을 생성합니다.
    
    Args:
        abstract_goals: 선택한 추상적 목표 리스트
        connected_sources: 연결한 데이터 소스 리스트
        intervention_frequency: 개입 빈도
        automation_level: 자동화 수준
        
    Returns:
        World Model 딕셔너리
    """
    # 추상적 목표 생성
    abstract_goals_list = []
    for i, goal_text in enumerate(abstract_goals, 1):
        abstract_goals_list.append({
            "id": f"abstract_goal_{i}",
            "text": goal_text,
            "created_at": datetime.now().isoformat(),
            "priority": "high" if i <= 2 else "medium"
        })
    
    # 연결된 소스 생성
    connected_sources_list = []
    for source_name in connected_sources:
        # 소스 정보 찾기
        source_info = None
        for category, sources in DATA_SOURCE_OPTIONS.items():
            for source in sources:
                if source["name"] == source_name:
                    source_info = source
                    break
            if source_info:
                break
        
        if source_info:
            connected_sources_list.append({
                "id": f"source_{source_name.lower().replace(' ', '_')}",
                "name": source_name,
                "type": "mcp",
                "permissions": {
                    "read": ["metadata", "subject"] if "email" in source_name.lower() else ["metadata"],
                    "write": []  # 초기에는 읽기 전용
                },
                "connected_at": datetime.now().isoformat(),
                "status": "active"
            })
    
    # 선호 설정
    preferences = {
        "notifications": {
            "frequency": intervention_frequency,
            "channels": ["email", "in_app"],
            "quiet_hours": {
                "start": "22:00",
                "end": "08:00"
            }
        },
        "automation": {
            "acceptance": automation_level,
            "auto_approve_threshold": 0.8 if automation_level == "simple_auto" else 1.0
        }
    }
    
    # World Model 생성
    world_model = {
        "user": {
            "user_id": "demo_user"
        },
        "abstract_goals": abstract_goals_list,
        "preferences": preferences,
        "patterns": [],
        "ideal_states": [],
        "problem_candidates": [],
        "confirmed_problems": [],
        "active_agents": [],
        "connected_sources": connected_sources_list,
        "safety": {
            "policy": {
                "default_write_block": True,
                "action_allowlist": ["apply_label", "send_notification"],
                "forbidden_actions": ["delete", "send_email", "modify_calendar"],
                "approval_required_for": ["write_operations", "high_risk_actions"]
            },
            "data_governance": {
                "sensitivity_classification": {
                    "low": ["aggregated_metrics", "message_count"],
                    "medium": ["sender_domain", "subject_keywords"],
                    "high": ["body_content", "personal_info"]
                },
                "retention_periods": {
                    "observations": 30,
                    "features": 90,
                    "logs": 180
                }
            }
        },
        "updated_at": datetime.now().isoformat()
    }
    
    return world_model


def save_world_model(world_model: Dict[str, Any], file_path: str = "data/world_model.json") -> None:
    """
    World Model을 파일에 저장합니다.
    
    Args:
        world_model: World Model 딕셔너리
        file_path: 저장할 파일 경로
    """
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, "w", encoding="utf-8") as f:
        json.dump(world_model, f, ensure_ascii=False, indent=2)


def load_onboarding_template() -> Dict[str, Any]:
    """
    온보딩 템플릿을 로드합니다.
    
    Returns:
        온보딩 템플릿 딕셔너리
    """
    return {
        "abstract_goal_options": ABSTRACT_GOAL_OPTIONS,
        "data_source_options": DATA_SOURCE_OPTIONS,
        "intervention_frequency_options": INTERVENTION_FREQUENCY_OPTIONS,
        "automation_level_options": AUTOMATION_LEVEL_OPTIONS
    }


def validate_onboarding_data(
    abstract_goals: List[str],
    connected_sources: List[str]
) -> Dict[str, Any]:
    """
    온보딩 데이터를 검증합니다.
    
    Args:
        abstract_goals: 선택한 추상적 목표 리스트
        connected_sources: 연결한 데이터 소스 리스트
        
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
    
    # 필수 필드 검증
    if not abstract_goals or len(abstract_goals) == 0:
        errors.append("최소 1개 이상의 목표를 선택해주세요.")
    
    if not connected_sources or len(connected_sources) == 0:
        warnings.append("데이터 소스를 연결하지 않으면 관찰이 시작되지 않습니다.")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }

