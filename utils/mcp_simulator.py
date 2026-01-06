"""
MCP (Model Context Protocol) 시뮬레이터
v3.2: 실제 MCP 서버 없이도 MCP 프로토콜을 시뮬레이션
데모 목적으로 실제 MCP처럼 동작하도록 구현
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import json


class MCPSimulator:
    """MCP 서버 시뮬레이터"""
    
    def __init__(self, source_name: str, permissions: Dict[str, List[str]]):
        """
        MCP 시뮬레이터 초기화
        
        Args:
            source_name: 소스 이름 (예: "gmail", "github")
            permissions: 권한 딕셔너리 {"read": [...], "write": [...]}
        """
        self.source_name = source_name
        self.permissions = permissions
        self.data_cache: Dict[str, Any] = {}
    
    def read(self, scope: str, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        데이터를 읽습니다 (MCP read 작업 시뮬레이션).
        
        Args:
            scope: 읽기 범위 (예: "metadata", "subject", "body")
            filters: 필터 조건
            
        Returns:
            읽은 데이터
        """
        if "read" not in self.permissions:
            raise PermissionError(f"{self.source_name}에 읽기 권한이 없습니다.")
        
        # 실제 MCP에서는 서버에 요청하지만, 여기서는 샘플 데이터 로드
        if self.source_name.lower() == "gmail":
            return self._read_gmail(scope, filters)
        elif self.source_name.lower() == "github":
            return self._read_github(scope, filters)
        elif self.source_name.lower() == "apple health":
            return self._read_health(scope, filters)
        elif "finance" in self.source_name.lower():
            return self._read_finance(scope, filters)
        
        return {"data": [], "count": 0}
    
    def write(self, action: str, resource_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        데이터를 씁니다 (MCP write 작업 시뮬레이션).
        
        Args:
            action: 액션 (예: "apply_label", "send_dm")
            resource_id: 리소스 ID
            data: 쓰기 데이터
            
        Returns:
            실행 결과
        """
        if "write" not in self.permissions:
            raise PermissionError(f"{self.source_name}에 쓰기 권한이 없습니다.")
        
        # 쓰기 권한 확인
        write_perms = self.permissions.get("write", [])
        if action not in write_perms:
            raise PermissionError(f"{action} 액션에 대한 권한이 없습니다.")
        
        # 실제 MCP에서는 서버에 요청하지만, 여기서는 시뮬레이션
        if self.source_name.lower() == "gmail" and action == "apply_label":
            return {
                "status": "success",
                "action": action,
                "resource_id": resource_id,
                "applied_label": data.get("label"),
                "timestamp": datetime.now().isoformat()
            }
        elif self.source_name.lower() == "slack" and action == "send_dm":
            return {
                "status": "success",
                "action": action,
                "recipient": data.get("recipient"),
                "message": data.get("message"),
                "timestamp": datetime.now().isoformat()
            }
        
        return {
            "status": "success",
            "action": action,
            "resource_id": resource_id,
            "timestamp": datetime.now().isoformat()
        }
    
    def _read_gmail(self, scope: str, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Gmail 데이터 읽기 시뮬레이션"""
        email_path = Path("data/sample_emails.json")
        if not email_path.exists():
            return {"data": [], "count": 0}
        
        with open(email_path, "r", encoding="utf-8") as f:
            emails = json.load(f)
        
        # scope에 따라 필터링
        if scope == "metadata_and_subject":
            filtered = [
                {
                    "id": e.get("id"),
                    "sender": e.get("sender"),
                    "subject": e.get("subject"),
                    "received_at": e.get("received_at"),
                    "hidden_priority": e.get("hidden_priority")
                }
                for e in emails
            ]
        elif scope == "metadata":
            filtered = [
                {
                    "id": e.get("id"),
                    "sender": e.get("sender"),
                    "received_at": e.get("received_at")
                }
                for e in emails
            ]
        else:
            filtered = emails
        
        return {
            "data": filtered,
            "count": len(filtered),
            "scope": scope,
            "source": "gmail"
        }
    
    def _read_github(self, scope: str, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """GitHub 데이터 읽기 시뮬레이션"""
        pr_path = Path("data/sample_github_prs.json")
        if not pr_path.exists():
            return {"data": [], "count": 0}
        
        with open(pr_path, "r", encoding="utf-8") as f:
            prs = json.load(f)
        
        return {
            "data": prs,
            "count": len(prs),
            "scope": scope,
            "source": "github"
        }
    
    def _read_health(self, scope: str, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """건강 데이터 읽기 시뮬레이션"""
        health_path = Path("data/sample_health_data.json")
        if not health_path.exists():
            return {"data": [], "count": 0}
        
        with open(health_path, "r", encoding="utf-8") as f:
            records = json.load(f)
        
        return {
            "data": records,
            "count": len(records),
            "scope": scope,
            "source": "apple_health"
        }
    
    def _read_finance(self, scope: str, filters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """재정 데이터 읽기 시뮬레이션"""
        finance_path = Path("data/sample_finance_data.json")
        if not finance_path.exists():
            return {"data": [], "count": 0}
        
        with open(finance_path, "r", encoding="utf-8") as f:
            transactions = json.load(f)
        
        return {
            "data": transactions,
            "count": len(transactions),
            "scope": scope,
            "source": "finance_app"
        }


def get_mcp_simulator(source_name: str, permissions: Dict[str, List[str]]) -> MCPSimulator:
    """
    MCP 시뮬레이터 인스턴스를 생성합니다.
    
    Args:
        source_name: 소스 이름
        permissions: 권한 딕셔너리
        
    Returns:
        MCPSimulator 인스턴스
    """
    return MCPSimulator(source_name, permissions)

