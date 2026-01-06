"""
Sensor Layer: 외부 데이터 소스에서 현재 상태를 수집하는 계층
v3.2 업데이트: 다양한 도메인 지원 (이메일, GitHub, 건강, 재정)
"""

import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime


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


def load_github_prs(data_path: str = "data/sample_github_prs.json") -> List[Dict[str, Any]]:
    """
    샘플 GitHub PR 데이터를 로드합니다.
    
    Args:
        data_path: PR 데이터 파일 경로
        
    Returns:
        PR 리스트
    """
    file_path = Path(data_path)
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_health_data(data_path: str = "data/sample_health_data.json") -> List[Dict[str, Any]]:
    """
    샘플 건강 데이터를 로드합니다.
    
    Args:
        data_path: 건강 데이터 파일 경로
        
    Returns:
        건강 데이터 리스트
    """
    file_path = Path(data_path)
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_finance_data(data_path: str = "data/sample_finance_data.json") -> List[Dict[str, Any]]:
    """
    샘플 재정 데이터를 로드합니다.
    
    Args:
        data_path: 재정 데이터 파일 경로
        
    Returns:
        거래 리스트
    """
    file_path = Path(data_path)
    if not file_path.exists():
        return []
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_current_state(
    domain: Optional[str] = None,
    domains: Optional[List[str]] = None,
    emails: Optional[List[Dict[str, Any]]] = None,
    github_prs: Optional[List[Dict[str, Any]]] = None,
    health_data: Optional[List[Dict[str, Any]]] = None,
    finance_data: Optional[List[Dict[str, Any]]] = None,
    world_model: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    현재 상태를 구조화된 형태로 반환합니다.
    v3.2 업데이트: 다양한 도메인 지원 및 여러 도메인 조합 지원
    
    Args:
        domain: 단일 도메인 ("email", "github", "health", "finance") - 하위 호환성
        domains: 여러 도메인 리스트 - 여러 도메인 조합 시 사용
        emails: 이메일 리스트 (None이면 자동 로드)
        github_prs: GitHub PR 리스트 (None이면 자동 로드)
        health_data: 건강 데이터 리스트 (None이면 자동 로드)
        finance_data: 재정 데이터 리스트 (None이면 자동 로드)
        world_model: World Model (도메인 자동 감지용)
        
    Returns:
        현재 상태 딕셔너리 (여러 도메인일 경우 조합된 데이터)
    """
    # 도메인 결정: domains > domain > world_model에서 자동 감지
    target_domains = []
    if domains:
        target_domains = domains
    elif domain:
        target_domains = [domain]
    elif world_model:
        # World Model에서 활성 소스의 도메인 추출
        source_to_domain = {
            "Gmail": "email",
            "GitHub": "github",
            "Apple Health": "health"
        }
        connected_sources = world_model.get("connected_sources", [])
        active_sources = [s for s in connected_sources if s.get("status") == "active"]
        for source in active_sources:
            source_name = source.get("name", "")
            domain_name = source_to_domain.get(source_name)
            if domain_name and domain_name not in target_domains:
                target_domains.append(domain_name)
    
    # 도메인이 없으면 기본값 (하위 호환성)
    if not target_domains:
        target_domains = ["email"]
    
    # 여러 도메인 조합 처리
    if len(target_domains) > 1:
        combined_data = {}
        combined_metadata = {
            "sources": [],
            "collection_method": "batch",
            "domains": target_domains
        }
        
        for dom in target_domains:
            if dom == "email":
                if emails is None:
                    emails = load_emails()
                combined_data["emails"] = emails
                combined_data["total_emails"] = len(emails)
                combined_data["unread_count"] = len([e for e in emails if not e.get("read", False)])
                combined_metadata["sources"].append("email")
                
            elif dom == "github":
                if github_prs is None:
                    github_prs = load_github_prs()
                pending_reviews = [pr for pr in github_prs if pr.get("review_status") == "pending"]
                old_prs = [pr for pr in pending_reviews if pr.get("age_hours", 0) > 48]
                combined_data["prs"] = github_prs
                combined_data["total_prs"] = len(github_prs)
                combined_data["open_prs"] = len([pr for pr in github_prs if pr.get("status") == "open"])
                combined_data["pending_reviews"] = len(pending_reviews)
                combined_data["old_prs"] = len(old_prs)
                combined_metadata["sources"].append("github")
                
            elif dom == "health":
                if health_data is None:
                    health_data = load_health_data()
                if health_data:
                    avg_sleep = sum(d.get("sleep", {}).get("duration_hours", 0) for d in health_data) / len(health_data)
                    avg_steps = sum(d.get("activity", {}).get("steps", 0) for d in health_data) / len(health_data)
                else:
                    avg_sleep = 0
                    avg_steps = 0
                combined_data["health_records"] = health_data
                combined_data["total_health_records"] = len(health_data)
                combined_data["average_sleep_hours"] = avg_sleep
                combined_data["average_steps"] = avg_steps
                combined_metadata["sources"].append("health")
                
            elif dom == "finance":
                if finance_data is None:
                    finance_data = load_finance_data()
                total_spending = sum(txn.get("amount", 0) for txn in finance_data)
                category_spending = {}
                for txn in finance_data:
                    category = txn.get("category", "기타")
                    category_spending[category] = category_spending.get(category, 0) + txn.get("amount", 0)
                combined_data["transactions"] = finance_data
                combined_data["total_transactions"] = len(finance_data)
                combined_data["total_spending"] = total_spending
                combined_data["category_spending"] = category_spending
                combined_metadata["sources"].append("finance")
        
        return {
            "domain": "multi",  # 여러 도메인 조합
            "domains": target_domains,
            "timestamp": datetime.now().isoformat(),
            "data": combined_data,
            "metadata": combined_metadata
        }
    
    # 단일 도메인 처리 (기존 로직)
    domain = target_domains[0]
    if domain == "email":
        if emails is None:
            emails = load_emails()
        
        return {
            "domain": "email",
            "timestamp": datetime.now().isoformat(),
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
    
    elif domain == "github" or domain == "개발":
        if github_prs is None:
            github_prs = load_github_prs()
        
        # PR 통계 계산
        pending_reviews = [pr for pr in github_prs if pr.get("review_status") == "pending"]
        old_prs = [pr for pr in pending_reviews if pr.get("age_hours", 0) > 48]
        
        return {
            "domain": "github",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "total_prs": len(github_prs),
                "open_prs": len([pr for pr in github_prs if pr.get("status") == "open"]),
                "pending_reviews": len(pending_reviews),
                "old_prs": len(old_prs),
                "prs": github_prs,
            },
            "metadata": {
                "source": "sample_data",
                "collection_method": "batch",
            }
        }
    
    elif domain == "health" or domain == "건강":
        if health_data is None:
            health_data = load_health_data()
        
        # 건강 통계 계산
        if health_data:
            avg_sleep = sum(d.get("sleep", {}).get("duration_hours", 0) for d in health_data) / len(health_data)
            avg_steps = sum(d.get("activity", {}).get("steps", 0) for d in health_data) / len(health_data)
        else:
            avg_sleep = 0
            avg_steps = 0
        
        return {
            "domain": "health",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "total_records": len(health_data),
                "average_sleep_hours": avg_sleep,
                "average_steps": avg_steps,
                "records": health_data,
            },
            "metadata": {
                "source": "sample_data",
                "collection_method": "batch",
            }
        }
    
    elif domain == "finance" or domain == "재정":
        if finance_data is None:
            finance_data = load_finance_data()
        
        # 재정 통계 계산
        total_spending = sum(txn.get("amount", 0) for txn in finance_data)
        category_spending = {}
        for txn in finance_data:
            category = txn.get("category", "기타")
            category_spending[category] = category_spending.get(category, 0) + txn.get("amount", 0)
        
        return {
            "domain": "finance",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "total_transactions": len(finance_data),
                "total_spending": total_spending,
                "category_spending": category_spending,
                "transactions": finance_data,
            },
            "metadata": {
                "source": "sample_data",
                "collection_method": "batch",
            }
        }
    
    else:
        # 알 수 없는 도메인
        return {
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "data": {},
            "metadata": {
                "source": "unknown",
                "collection_method": "unknown",
            }
        }

