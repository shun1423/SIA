"""
Security & Safety Layer: 프롬프트 인젝션, 데이터 유출, 멀티테넌트 격리 대응
"""

from typing import Dict, Any, List, Optional
import re


def sanitize_input(text: str, context: Optional[str] = None) -> str:
    """
    사용자 입력을 정제합니다.
    프롬프트 인젝션 공격을 방지합니다.
    
    Args:
        text: 입력 텍스트
        context: 컨텍스트 (선택적)
        
    Returns:
        정제된 텍스트
    """
    if not text:
        return ""
    
    # 위험한 패턴 제거
    dangerous_patterns = [
        r"ignore\s+(previous|all|above)\s+instructions?",
        r"forget\s+(previous|all|above)\s+instructions?",
        r"system\s*:",
        r"assistant\s*:",
        r"you\s+are\s+now",
        r"act\s+as\s+if",
        r"pretend\s+to\s+be"
    ]
    
    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
    
    return sanitized.strip()


def classify_sensitivity(data: Dict[str, Any]) -> str:
    """
    데이터의 민감도를 분류합니다.
    
    Args:
        data: 데이터 딕셔너리
        
    Returns:
        민감도 등급 ("low", "medium", "high")
    """
    # High 민감도 키워드
    high_sensitivity_keywords = [
        "body", "content", "text", "message", "personal_info",
        "password", "token", "secret", "private"
    ]
    
    # Medium 민감도 키워드
    medium_sensitivity_keywords = [
        "subject", "title", "sender", "domain", "metadata"
    ]
    
    data_str = str(data).lower()
    
    for keyword in high_sensitivity_keywords:
        if keyword in data_str:
            return "high"
    
    for keyword in medium_sensitivity_keywords:
        if keyword in data_str:
            return "medium"
    
    return "low"


def mask_sensitive_data(data: Dict[str, Any], sensitivity_level: str = "high") -> Dict[str, Any]:
    """
    민감한 데이터를 마스킹합니다.
    
    Args:
        data: 데이터 딕셔너리
        sensitivity_level: 마스킹할 민감도 레벨
        
    Returns:
        마스킹된 데이터 딕셔너리
    """
    masked = data.copy()
    
    # High 민감도 필드 마스킹
    high_sensitivity_fields = ["body", "content", "text", "message", "password", "token"]
    
    if sensitivity_level in ["high", "medium"]:
        for field in high_sensitivity_fields:
            if field in masked:
                value = masked[field]
                if isinstance(value, str) and len(value) > 0:
                    # 첫 10자만 보여주고 나머지는 마스킹
                    if len(value) > 10:
                        masked[field] = value[:10] + "..." + "[MASKED]"
                    else:
                        masked[field] = "[MASKED]"
    
    return masked


def validate_prompt_injection(prompt: str) -> Dict[str, Any]:
    """
    프롬프트 인젝션 공격을 검증합니다.
    
    Args:
        prompt: 프롬프트 문자열
        
    Returns:
        검증 결과 딕셔너리
        {
            "safe": bool,
            "threats": List[str],
            "sanitized": str
        }
    """
    threats = []
    
    # 위험한 패턴 검사
    injection_patterns = [
        (r"ignore\s+(previous|all|above)\s+instructions?", "명령 무시 시도"),
        (r"forget\s+(previous|all|above)\s+instructions?", "명령 삭제 시도"),
        (r"system\s*:\s*", "시스템 프롬프트 조작 시도"),
        (r"assistant\s*:\s*", "어시스턴트 역할 조작 시도"),
        (r"you\s+are\s+now\s+", "역할 변경 시도"),
        (r"act\s+as\s+if\s+", "가상 시나리오 주입 시도"),
        (r"pretend\s+to\s+be\s+", "역할 위장 시도"),
        (r"output\s+format\s*:\s*", "출력 형식 조작 시도"),
        (r"json\s+only", "JSON 강제 시도"),
        (r"no\s+explanation", "설명 제거 시도")
    ]
    
    for pattern, threat_name in injection_patterns:
        if re.search(pattern, prompt, re.IGNORECASE):
            threats.append(threat_name)
    
    # 정제된 프롬프트 생성
    sanitized = sanitize_input(prompt)
    
    return {
        "safe": len(threats) == 0,
        "threats": threats,
        "sanitized": sanitized
    }


def check_data_leakage(
    output: str,
    input_data: Dict[str, Any],
    world_model: Dict[str, Any]
) -> Dict[str, Any]:
    """
    데이터 유출을 검사합니다.
    
    Args:
        output: 출력 문자열
        input_data: 입력 데이터
        world_model: World Model 데이터
        
    Returns:
        검사 결과 딕셔너리
        {
            "safe": bool,
            "leaks": List[str],
            "recommendation": str
        }
    """
    leaks = []
    
    # High 민감도 데이터가 출력에 포함되어 있는지 확인
    high_sensitivity_fields = ["body", "content", "text", "message", "password", "token"]
    
    for field in high_sensitivity_fields:
        if field in input_data:
            value = str(input_data[field])
            # 입력 데이터의 일부가 출력에 포함되어 있는지 확인
            if value and value in output:
                leaks.append(f"High 민감도 필드 '{field}'가 출력에 포함되었습니다.")
    
    # 개인 식별 정보 확인
    pii_patterns = [
        (r"\b\d{3}-\d{4}-\d{4}\b", "전화번호"),
        (r"\b\d{6}-\d{7}\b", "주민등록번호"),
        (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "이메일 주소")
    ]
    
    for pattern, pii_type in pii_patterns:
        if re.search(pattern, output):
            leaks.append(f"{pii_type}가 출력에 포함되었습니다.")
    
    recommendation = ""
    if leaks:
        recommendation = "민감한 정보를 마스킹하거나 제거하세요."
    else:
        recommendation = "출력이 안전합니다."
    
    return {
        "safe": len(leaks) == 0,
        "leaks": leaks,
        "recommendation": recommendation
    }


def enforce_tenant_isolation(
    user_id: str,
    data: Dict[str, Any],
    world_model: Dict[str, Any]
) -> bool:
    """
    멀티테넌트 격리를 강제합니다.
    
    Args:
        user_id: 사용자 ID
        data: 데이터
        world_model: World Model 데이터
        
    Returns:
        격리 준수 여부
    """
    # World Model의 사용자 ID 확인
    world_model_user = world_model.get("user", {}).get("user_id")
    
    if world_model_user and world_model_user != user_id:
        return False
    
    return True

