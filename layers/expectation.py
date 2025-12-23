"""
Expectation Layer: World Model을 기반으로 이상적인 상태를 생성하는 계층
"""

import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic

# 환경 변수 로드
load_dotenv()


def load_world_model(data_path: str = "data/world_model.json") -> Dict[str, Any]:
    """
    World Model 데이터를 로드합니다.
    
    Args:
        data_path: World Model 파일 경로
        
    Returns:
        World Model 딕셔너리
    """
    file_path = Path(data_path)
    if not file_path.exists():
        return {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _init_anthropic_client() -> Optional[Anthropic]:
    """Anthropic 클라이언트를 초기화합니다."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def generate_expectation(
    world_model: Dict[str, Any] = None,
    current_context: Dict[str, Any] = None,
    anthropic_client: Optional[Anthropic] = None
) -> Dict[str, Any]:
    """
    현재 맥락에서 이상적인 상태를 생성합니다.
    Claude API를 사용하여 World Model과 현재 상황을 분석하여 이상적 상태를 생성합니다.
    
    Args:
        world_model: World Model 데이터
        current_context: 현재 맥락 (시간, 요일 등)
        anthropic_client: Anthropic 클라이언트 (None이면 자동 초기화)
        
    Returns:
        기대 상태 딕셔너리
    """
    if world_model is None:
        world_model = load_world_model()
    
    if current_context is None:
        from datetime import datetime
        now = datetime.now()
        current_context = {
            "day": now.strftime("%A").lower(),
            "time": now.strftime("%H:%M"),
            "timestamp": now.isoformat()
        }
    
    # Anthropic 클라이언트 초기화
    if anthropic_client is None:
        anthropic_client = _init_anthropic_client()
    
    # Claude API를 사용하여 이상적 상태 생성
    if anthropic_client:
        try:
            # 프롬프트 구성
            world_model_str = json.dumps(world_model, ensure_ascii=False, indent=2)
            context_str = json.dumps(current_context, ensure_ascii=False, indent=2)
            
            prompt = f"""이 사용자의 World Model과 현재 상황을 분석하여 이메일 관리의 이상적 상태를 생성해주세요.

## World Model:
{world_model_str}

## 현재 상황:
{context_str}

## 요청사항:
1. World Model의 Goals, Preferences, Patterns, Ideal States를 고려하세요
2. 현재 시간과 요일을 반영하세요
3. 이메일 도메인에 대한 이상적 상태를 JSON 형식으로 반환하세요

다음 JSON 형식으로 응답해주세요:
{{
    "domain": "email",
    "context": {context_str},
    "ideal_states": [
        {{
            "id": "ideal_1",
            "description": "이상적 상태 설명",
            "criterion": "기준",
            "target_value": "목표값",
            "priority": "high|medium|low"
        }}
    ],
    "expectations": [
        {{
            "id": "exp_1",
            "description": "기대 상태 설명",
            "criterion": "기준",
            "target_value": "목표값",
            "priority": "high|medium|low"
        }}
    ]
}}

JSON만 반환하고 다른 설명은 포함하지 마세요."""

            response = anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=2000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            # 응답 파싱
            response_text = response.content[0].text.strip()
            
            # JSON 추출 (마크다운 코드 블록 제거)
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            expectation = json.loads(response_text)
            return expectation
            
        except Exception as e:
            # API 호출 실패 시 폴백: 기존 로직 사용
            print(f"Claude API 호출 실패, 폴백 로직 사용: {e}")
    
    # 폴백: World Model의 Ideal States를 기반으로 생성
    ideal_states = world_model.get("ideal_states", [])
    relevant_ideals = [
        ideal for ideal in ideal_states
        if ideal.get("domain") == "email"
    ]
    
    return {
        "domain": "email",
        "context": current_context,
        "ideal_states": relevant_ideals,
        "expectations": [
            {
                "id": f"exp_{i}",
                "description": ideal.get("description", ""),
                "criterion": ideal.get("criterion", ""),
                "target_value": ideal.get("target_value"),
                "priority": ideal.get("priority", "medium")
            }
            for i, ideal in enumerate(relevant_ideals)
        ]
    }

