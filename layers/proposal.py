"""
Proposal Layer: 솔루션을 사용자에게 제안하고 승인을 받는 계층
v3.2 업데이트: 문제 상태 머신 통합
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

# 문제 상태 머신 임포트
import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.problem_state_machine import ProblemStateMachine


def select_best_solution(solutions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    여러 솔루션 중 최적안을 선택합니다.
    
    Args:
        solutions: Exploration Layer에서 탐색한 솔루션 리스트
        
    Returns:
        최적 솔루션 (없으면 None)
    """
    if not solutions:
        return None
    
    # 빈 솔루션 필터링
    valid_solutions = [s for s in solutions if s and isinstance(s, dict)]
    if not valid_solutions:
        return None
    
    # 복잡도와 장단점을 고려한 간단한 선택 로직
    # 실제로는 더 정교한 평가가 필요
    complexity_score = {"low": 3, "medium": 2, "high": 1}
    
    best = valid_solutions[0]
    best_score = len(best.get("pros", [])) - len(best.get("cons", [])) + complexity_score.get(best.get("complexity", "medium"), 1)
    
    for sol in valid_solutions[1:]:
        score = len(sol.get("pros", [])) - len(sol.get("cons", [])) + complexity_score.get(sol.get("complexity", "medium"), 1)
        if score > best_score:
            best = sol
            best_score = score
    
    return best


def create_proposal(
    problem: Dict[str, Any],
    solutions: List[Dict[str, Any]],
    selected_solution: Optional[Dict[str, Any]] = None,
    auto_promote: bool = True
) -> Dict[str, Any]:
    """
    사용자에게 제안할 Proposal을 생성합니다.
    v3.2 업데이트: 문제 상태 머신 통합
    
    Args:
        problem: 해석된 문제
        solutions: 탐색된 솔루션 리스트
        selected_solution: 선택된 솔루션 (None이면 자동 선택)
        auto_promote: 자동으로 Proposed 상태로 승격할지 여부
        
    Returns:
        Proposal 딕셔너리
    """
    if selected_solution is None:
        selected_solution = select_best_solution(solutions)
    
    # selected_solution이 None이면 에러
    if not selected_solution:
        raise ValueError("추천 솔루션을 선택할 수 없습니다. 솔루션 리스트를 확인해주세요.")
    
    # 문제를 Proposed 상태로 승격 (v3.2)
    if auto_promote and problem.get("status") == "candidate":
        try:
            problem = ProblemStateMachine.promote_candidate_to_proposed(problem)
        except Exception as e:
            # 상태 전이 실패 시 그대로 진행
            print(f"상태 전이 실패: {e}")
    
    return {
        "id": f"proposal_{problem.get('id', 'unknown')}",
        "problem": problem,
        "recommended_solution": selected_solution,
        "alternative_solutions": [s for s in solutions if s.get("id") != selected_solution.get("id")],
        "status": "pending",
        "created_at": problem.get("proposed_at", problem.get("detected_at", ""))
    }

