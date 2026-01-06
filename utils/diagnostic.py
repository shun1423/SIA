"""
진단 도구: 시스템이 실제로 동작하는지 확인하는 유틸리티
"""

import os
from typing import Dict, Any, List
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def check_system_status() -> Dict[str, Any]:
    """
    시스템 상태를 진단합니다.
    
    Returns:
        진단 결과 딕셔너리
    """
    results = {
        "api_configured": False,
        "api_test": None,
        "data_files": {},
        "layers_status": {},
        "overall_status": "unknown"
    }
    
    # 1. API 키 확인
    api_key = os.getenv("ANTHROPIC_API_KEY")
    results["api_configured"] = api_key is not None and len(api_key) > 0
    
    # 2. API 테스트 (실제 호출 시도)
    if results["api_configured"]:
        try:
            from anthropic import Anthropic
            client = Anthropic(api_key=api_key)
            
            # 간단한 테스트 호출
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=10,
                messages=[{
                    "role": "user",
                    "content": "Say 'OK'"
                }]
            )
            
            results["api_test"] = {
                "success": True,
                "response": response.content[0].text.strip()
            }
        except Exception as e:
            results["api_test"] = {
                "success": False,
                "error": str(e)
            }
    else:
        results["api_test"] = {
            "success": False,
            "error": "API 키가 설정되지 않았습니다"
        }
    
    # 3. 데이터 파일 확인
    data_files = {
        "world_model": "data/world_model.json",
        "sample_emails": "data/sample_emails.json",
        "sample_github_prs": "data/sample_github_prs.json",
        "sample_health_data": "data/sample_health_data.json",
        "sample_finance_data": "data/sample_finance_data.json"
    }
    
    for name, path in data_files.items():
        file_path = Path(path)
        results["data_files"][name] = {
            "exists": file_path.exists(),
            "size": file_path.stat().st_size if file_path.exists() else 0
        }
    
    # 4. 레이어별 상태 확인
    layers = {
        "sensor": "layers/sensor.py",
        "expectation": "layers/expectation.py",
        "comparison": "layers/comparison.py",
        "interpretation": "layers/interpretation.py",
        "exploration": "layers/exploration.py",
        "proposal": "layers/proposal.py",
        "composition": "layers/composition.py",
        "execution": "layers/execution.py",
        "learning": "layers/learning.py"
    }
    
    for layer_name, layer_path in layers.items():
        file_path = Path(layer_path)
        results["layers_status"][layer_name] = {
            "exists": file_path.exists(),
            "has_fallback": _check_has_fallback(layer_path) if file_path.exists() else False
        }
    
    # 5. 전체 상태 판단
    if results["api_test"] and results["api_test"]["success"]:
        results["overall_status"] = "fully_operational"  # 완전 동작
    elif results["api_configured"]:
        results["overall_status"] = "api_configured_but_failed"  # API 설정됐지만 실패
    else:
        results["overall_status"] = "demo_mode"  # 데모 모드 (폴백 사용)
    
    return results


def _check_has_fallback(file_path: Path) -> bool:
    """
    파일에 폴백 로직이 있는지 확인합니다.
    
    Args:
        file_path: 파일 경로
        
    Returns:
        폴백 로직 존재 여부
    """
    try:
        content = file_path.read_text(encoding="utf-8")
        fallback_keywords = [
            "폴백",
            "fallback",
            "하드코딩",
            "hardcoded",
            "시뮬레이션",
            "simulation"
        ]
        return any(keyword in content.lower() for keyword in fallback_keywords)
    except:
        return False


def get_operation_mode() -> str:
    """
    현재 운영 모드를 반환합니다.
    
    Returns:
        "real" (실제 동작) 또는 "demo" (데모 모드)
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if api_key and len(api_key) > 0:
        # API 키가 있으면 실제 동작 모드
        return "real"
    else:
        # API 키가 없으면 데모 모드 (폴백 사용)
        return "demo"


def print_diagnostic_report() -> None:
    """
    진단 보고서를 출력합니다.
    """
    status = check_system_status()
    mode = get_operation_mode()
    
    print("=" * 60)
    print("SIA 시스템 진단 보고서")
    print("=" * 60)
    print()
    
    print(f"📊 운영 모드: {mode.upper()}")
    if mode == "real":
        print("   ✅ 실제 Claude API를 사용하여 동작합니다")
    else:
        print("   ⚠️  데모 모드: 하드코딩된 폴백 로직을 사용합니다")
    print()
    
    print("🔑 API 상태:")
    print(f"   API 키 설정: {'✅ 있음' if status['api_configured'] else '❌ 없음'}")
    if status["api_test"]:
        if status["api_test"]["success"]:
            print(f"   API 테스트: ✅ 성공 ({status['api_test']['response']})")
        else:
            print(f"   API 테스트: ❌ 실패 ({status['api_test']['error']})")
    print()
    
    print("📁 데이터 파일:")
    for name, info in status["data_files"].items():
        status_icon = "✅" if info["exists"] else "❌"
        size_kb = info["size"] / 1024
        print(f"   {status_icon} {name}: {info['size']} bytes ({size_kb:.1f} KB)")
    print()
    
    print("🔧 레이어 상태:")
    for layer_name, info in status["layers_status"].items():
        exists_icon = "✅" if info["exists"] else "❌"
        fallback_icon = "⚠️" if info["has_fallback"] else "✅"
        print(f"   {exists_icon} {layer_name}: 파일 존재, {fallback_icon} 폴백 로직")
    print()
    
    print("=" * 60)
    print(f"전체 상태: {status['overall_status']}")
    print("=" * 60)

