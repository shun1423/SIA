"""
Sensor Layer: 외부 데이터 소스에서 현재 상태를 수집하는 계층
"""

import json
from typing import Dict, List, Any
from pathlib import Path


def load_emails(data_path: str = "data/sample_emails.json") -> List[Dict[str, Any]]:
    """
    샘플 이메일 데이터를 로드합니다.
    
    Args:
        data_path: 이메일 데이터 파일 경로
        
    Returns:
        이메일 리스트
    """
    file_path = Path(data_path)
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_current_state(emails: List[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    현재 상태를 구조화된 형태로 반환합니다.
    
    Args:
        emails: 이메일 리스트 (None이면 자동 로드)
        
    Returns:
        현재 상태 딕셔너리
    """
    if emails is None:
        emails = load_emails()
    
    return {
        "domain": "email",
        "timestamp": "2025-01-15T09:00:00Z",
        "data": {
            "total_emails": len(emails),
            "unread_count": len([e for e in emails if not e.get("read", False)]),
            "emails": emails,
        },
        "metadata": {
            "source": "sample_data",
            "collection_method": "batch",
        }
    }

