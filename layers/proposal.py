"""
Proposal Layer: 솔루션을 사용자에게 제안하고 승인을 받는 계층
"""

from typing import Dict, Any, List, Optional


def select_best_solution(solutions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    여러 솔루션 중 최적안을 선택합니다.
    
    Args:
        solutions: Exploration Layer에서 탐색한 솔루션 리스트
        
    Returns:
        최적 솔루션
    """
    if not solutions:
        return {}
    
    # 복잡도와 장단점을 고려한 간단한 선택 로직
    # 실제로는 더 정교한 평가가 필요
    complexity_score = {"low": 3, "medium": 2, "high": 1}
    
    best = solutions[0]
    best_score = len(best.get("pros", [])) - len(best.get("cons", [])) + complexity_score.get(best.get("complexity", "medium"), 1)
    
    for sol in solutions[1:]:
        score = len(sol.get("pros", [])) - len(sol.get("cons", [])) + complexity_score.get(sol.get("complexity", "medium"), 1)
        if score > best_score:
            best = sol
            best_score = score
    
    return best


def create_proposal(
    problem: Dict[str, Any],
    solutions: List[Dict[str, Any]],
    selected_solution: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    사용자에게 제안할 Proposal을 생성합니다.
    
    Args:
        problem: 해석된 문제
        solutions: 탐색된 솔루션 리스트
        selected_solution: 선택된 솔루션 (None이면 자동 선택)
        
    Returns:
        Proposal 딕셔너리
    """
    if selected_solution is None:
        selected_solution = select_best_solution(solutions)
    
    return {
        "id": f"proposal_{problem.get('id', 'unknown')}",
        "problem": problem,
        "recommended_solution": selected_solution,
        "alternative_solutions": [s for s in solutions if s["id"] != selected_solution.get("id")],
        "status": "pending"
    }

