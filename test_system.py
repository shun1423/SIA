"""
시스템 테스트 스크립트
실제로 동작하는지 확인하는 테스트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 경로에 추가
sys.path.append(str(Path(__file__).parent))

from utils.diagnostic import check_system_status, get_operation_mode, print_diagnostic_report


def test_real_operation():
    """
    실제 동작 테스트
    """
    print("\n" + "=" * 60)
    print("실제 동작 테스트")
    print("=" * 60 + "\n")
    
    # 1. 진단 보고서 출력
    print_diagnostic_report()
    
    # 2. 각 레이어별 실제 동작 테스트
    mode = get_operation_mode()
    
    if mode == "demo":
        print("\n⚠️  경고: API 키가 설정되지 않아 데모 모드로 동작합니다.")
        print("   실제 Claude API를 사용하려면 .env 파일에 ANTHROPIC_API_KEY를 설정하세요.\n")
    
    # 3. 간단한 플로우 테스트
    print("\n" + "=" * 60)
    print("플로우 테스트")
    print("=" * 60 + "\n")
    
    try:
        # Sensor Layer 테스트
        print("1. Sensor Layer 테스트...")
        from layers.sensor import get_current_state
        current_state = get_current_state(domain="email")
        print(f"   ✅ 현재 상태 수집: {current_state.get('domain')} 도메인, {len(current_state.get('data', {}).get('emails', []))}개 이메일")
        
        # Expectation Layer 테스트
        print("2. Expectation Layer 테스트...")
        from layers.expectation import generate_expectation
        expectation = generate_expectation(domain="email")
        print(f"   ✅ 기대 상태 생성: {len(expectation.get('expectations', []))}개 기대 상태")
        
        # Comparison Layer 테스트
        print("3. Comparison Layer 테스트...")
        from layers.comparison import compare_states
        gaps = compare_states(current_state, expectation)
        print(f"   ✅ Gap 발견: {len(gaps)}개")
        for gap in gaps:
            print(f"      - {gap.get('description', 'N/A')} (Problem Score: {gap.get('problem_score', 0):.2f})")
        
        # Interpretation Layer 테스트
        if gaps:
            print("4. Interpretation Layer 테스트...")
            from layers.interpretation import interpret_gaps
            problems = interpret_gaps(gaps)
            print(f"   ✅ 문제 해석: {len(problems)}개")
            for problem in problems:
                print(f"      - {problem.get('name', 'N/A')} (상태: {problem.get('status', 'N/A')})")
        
        print("\n✅ 모든 레이어가 정상적으로 동작합니다!")
        
    except Exception as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_real_operation()

