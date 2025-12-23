"""
SIA MVP - Streamlit 멀티페이지 애플리케이션
10개 계층을 네비게이션할 수 있는 구조
"""

import streamlit as st
import os
import json
import random
import time
from pathlib import Path
from dotenv import load_dotenv
from anthropic import Anthropic
import pandas as pd
from datetime import datetime

# 환경 변수 로드
load_dotenv()

# 페이지 설정
st.set_page_config(
    page_title="SIA MVP",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 세션 상태 초기화
if "world_model" not in st.session_state:
    st.session_state.world_model = None
if "current_state" not in st.session_state:
    st.session_state.current_state = None
if "expectation" not in st.session_state:
    st.session_state.expectation = None
if "gaps" not in st.session_state:
    st.session_state.gaps = []
if "problems" not in st.session_state:
    st.session_state.problems = []
if "solutions" not in st.session_state:
    st.session_state.solutions = []
if "proposal" not in st.session_state:
    st.session_state.proposal = None
if "agent_config" not in st.session_state:
    st.session_state.agent_config = None
if "execution_result" not in st.session_state:
    st.session_state.execution_result = None
if "original_emails" not in st.session_state:
    st.session_state.original_emails = None
if "world_model_before" not in st.session_state:
    st.session_state.world_model_before = None
if "demo_running" not in st.session_state:
    st.session_state.demo_running = False

# Anthropic API 클라이언트 초기화
@st.cache_resource
def init_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        return Anthropic(api_key=api_key)
    except Exception as e:
        st.error(f"API 클라이언트 초기화 실패: {str(e)}")
        return None

client = init_anthropic_client()

# 진행 단계 확인 함수
def get_progress_steps():
    """현재 진행 단계를 반환합니다."""
    steps = [
        ("🌍 World Model", st.session_state.world_model is not None),
        ("👁️ Sensor Layer", st.session_state.current_state is not None),
        ("🎯 Expectation Layer", st.session_state.expectation is not None),
        ("⚖️ Comparison Layer", len(st.session_state.gaps) > 0),
        ("🔍 Interpretation Layer", len(st.session_state.problems) > 0),
        ("🔎 Exploration Layer", len(st.session_state.solutions) > 0),
        ("💡 Proposal Layer", st.session_state.proposal is not None and st.session_state.proposal.get("status") == "approved"),
        ("🔧 Composition Layer", st.session_state.agent_config is not None),
        ("⚡ Execution Layer", st.session_state.execution_result is not None),
        ("📚 Learning Layer", st.session_state.execution_result is not None and st.session_state.world_model_before is not None),
    ]
    return steps

# 사이드바 네비게이션
with st.sidebar:
    st.title("SIA MVP")
    st.markdown("---")
    
    # API 상태
    if client:
        st.success("Anthropic API 연결됨")
    else:
        st.error("API 키 필요")
        st.info("`.env` 파일에 `ANTHROPIC_API_KEY`를 설정하세요")
    
    st.markdown("---")
    
    # 진행 상황을 접을 수 있게
    with st.expander("진행 상황", expanded=False):
        steps = get_progress_steps()
        completed_count = sum(1 for _, completed in steps if completed)
        
        st.progress(completed_count / 10)
        st.caption(f"{completed_count}/10 단계 완료")
        
        for i, (step_name, completed) in enumerate(steps, 1):
            status = "완료" if completed else "대기"
            st.markdown(f"{i}. {step_name} - {status}")
    
    st.markdown("---")
    st.markdown("### 계층 네비게이션")
    
    # 페이지 선택
    page = st.radio(
        "계층 선택",
        [
            "홈",
            "World Model",
            "Sensor Layer",
            "Expectation Layer",
            "Comparison Layer",
            "Interpretation Layer",
            "Exploration Layer",
            "Proposal Layer",
            "Composition Layer",
            "Execution Layer",
            "Learning Layer",
            "에이전트 데모"
        ],
        label_visibility="collapsed"
    )

# 데모 자동 실행 함수
def run_demo():
    """전체 플로우를 자동으로 실행합니다."""
    st.session_state.demo_running = True
    
    try:
        # 1. Sensor Layer
        from layers.sensor import load_emails, get_current_state
        with st.spinner("📥 현재 상태 수집 중..."):
            emails = load_emails()
            current_state = get_current_state(emails)
            st.session_state.current_state = current_state
            st.session_state.original_emails = [e.copy() for e in emails]  # 원본 저장
        
        # 2. Expectation Layer
        from layers.expectation import generate_expectation
        with st.spinner("🎯 기대 상태 생성 중..."):
            expectation = generate_expectation(anthropic_client=client)
            st.session_state.expectation = expectation
        
        # 3. Comparison Layer
        from layers.comparison import compare_states
        with st.spinner("⚖️ 상태 비교 중..."):
            gaps = compare_states(current_state, expectation, anthropic_client=client)
            st.session_state.gaps = gaps
        
        # 4. Interpretation Layer
        from layers.interpretation import interpret_gaps
        with st.spinner("🔍 문제 해석 중..."):
            problems = interpret_gaps(gaps, anthropic_client=client)
            st.session_state.problems = problems
        
        # 5. Exploration Layer
        from layers.exploration import explore_solutions
        with st.spinner("🔎 솔루션 탐색 중..."):
            all_solutions = []
            for problem in problems:
                solutions = explore_solutions(problem, anthropic_client=client)
                all_solutions.extend(solutions)
            st.session_state.solutions = all_solutions
        
        # 6. Proposal Layer
        from layers.proposal import create_proposal
        with st.spinner("💡 제안 생성 중..."):
            if problems and all_solutions:
                problem = problems[0]
                solutions = [s for s in all_solutions if s.get("id", "").startswith("sol_")]
                proposal = create_proposal(problem, solutions)
                proposal["status"] = "approved"  # 데모에서는 자동 승인
                st.session_state.proposal = proposal
        
        # 7. Composition Layer
        from layers.composition import compose_agent
        with st.spinner("🔧 에이전트 구성 중..."):
            if st.session_state.proposal:
                solution = st.session_state.proposal["recommended_solution"]
                agent_config = compose_agent(solution)
                st.session_state.agent_config = agent_config
        
        # 8. Execution Layer
        from layers.execution import execute_agent
        with st.spinner("⚡ 에이전트 실행 중..."):
            execution_result = execute_agent(
                st.session_state.agent_config,
                emails=emails
            )
            st.session_state.execution_result = execution_result
        
        # 9. Learning Layer
        from layers.learning import analyze_results, update_world_model
        with st.spinner("📚 학습 및 업데이트 중..."):
            # World Model 백업
            world_model_path = Path("data/world_model.json")
            if world_model_path.exists():
                with open(world_model_path, "r", encoding="utf-8") as f:
                    st.session_state.world_model_before = json.load(f)
            
            analysis = analyze_results(execution_result)
            updated_model = update_world_model(analysis)
            st.session_state.world_model = updated_model
        
        st.session_state.demo_running = False
        st.success("데모가 완료되었습니다!")
        
    except Exception as e:
        st.session_state.demo_running = False
        st.error(f"데모 실행 중 오류 발생: {str(e)}")
        st.exception(e)

# 페이지별 콘텐츠
if page == "홈":
    st.title("Self-Initiating Agent (SIA) MVP")
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("""
        ## 소개
        
        SIA는 **사용자가 먼저 시작하지 않아도** 스스로 문제를 발견하고 해결책을 제안하는 AI 에이전트입니다.
        
        ### 핵심 원리
        
        > "이상적 상태"와 "현재 상태"를 비교하여, 차이가 발생하면 스스로 행동합니다.
        
        ### 현재 AI 에이전트 vs SIA
        
        | 현재 방식 | SIA 방식 |
        | --- | --- |
        | 사람이 문제를 정의합니다 | AI가 문제를 발견합니다 |
        | 사람이 해결책을 설계합니다 | AI가 해결책을 제안합니다 |
        | 사람이 도구를 선택합니다 | AI가 필요한 도구를 조합합니다 |
        | 한 번 실행하고 끝납니다 | 결과를 보고 다음에 더 잘합니다 |
        
        ### 10개 계층 구조
        
        1. **World Model**: 사용자 목표/선호/패턴 저장소
        2. **Sensor Layer**: 외부 데이터 수집
        3. **Expectation Layer**: 이상적 상태 생성
        4. **Comparison Layer**: 현재 vs 이상 비교
        5. **Interpretation Layer**: Gap을 문제로 정의
        6. **Exploration Layer**: 해결책 탐색
        7. **Proposal Layer**: 사용자에게 제안
        8. **Composition Layer**: 도구 동적 선택/조합
        9. **Execution Layer**: 실행
        10. **Learning Layer**: 결과 학습 및 World Model 업데이트
        
        ### 시작하기
        
        아래 버튼을 클릭하여 전체 플로우를 자동으로 실행하거나, 사이드바에서 각 계층을 선택하여 단계별로 확인하세요.
        """)
    
    with col2:
        st.markdown("### 빠른 시작")
        st.markdown("**SIA 전체 플로우 실행**")
        st.caption("10개 계층을 순차적으로 실행하여 에이전트를 생성합니다.")
        if st.button("SIA 전체 플로우 실행", type="primary", use_container_width=True):
            run_demo()
        
        st.markdown("---")
        st.markdown("### 현재 상태")
        steps = get_progress_steps()
        completed = sum(1 for _, c in steps if c)
        st.metric("완료된 단계", f"{completed}/10")
        
        if completed == 10:
            st.success("모든 단계 완료!")
            st.info("에이전트 데모 페이지에서 생성된 에이전트를 테스트할 수 있습니다.")
    
    # 현재 World Model 미리보기
    st.markdown("---")
    st.markdown("### 현재 World Model")
    
    world_model_path = Path("data/world_model.json")
    if world_model_path.exists():
        with open(world_model_path, "r", encoding="utf-8") as f:
            world_model = json.load(f)
        
        user = world_model.get("user", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**사용자**: {user.get('name', 'N/A')}")
        with col2:
            st.info(f"**역할**: {user.get('role', 'N/A')}")
        with col3:
            goals = world_model.get("goals", [])
            st.info(f"**목표**: {len(goals)}개")
    else:
        st.warning("World Model 데이터를 찾을 수 없습니다.")

elif page == "World Model":
    st.title("🌍 World Model")
    st.markdown("---")
    
    world_model_path = Path("data/world_model.json")
    if world_model_path.exists():
        with open(world_model_path, "r", encoding="utf-8") as f:
            world_model = json.load(f)
        
        st.session_state.world_model = world_model
        
        # 사용자 정보
        st.markdown("### 사용자 정보")
        user = world_model.get("user", {})
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("이름", user.get("name", "N/A"))
        with col2:
            st.metric("역할", user.get("role", "N/A"))
        with col3:
            st.metric("이메일", user.get("email", "N/A"))
        
        # Goals
        st.markdown("### 목표 (Goals)")
        goals = world_model.get("goals", [])
        for goal in goals:
            with st.expander(f"🎯 {goal.get('text', '')}"):
                st.json(goal)
        
        # Preferences
        st.markdown("### 선호 (Preferences)")
        st.json(world_model.get("preferences", {}))
        
        # Patterns
        st.markdown("### 패턴 (Patterns)")
        patterns = world_model.get("patterns", [])
        for pattern in patterns:
            with st.expander(f"📊 {pattern.get('behavior', '')}"):
                st.json(pattern)
        
        # Ideal States
        st.markdown("### 이상적 상태 (Ideal States)")
        ideal_states = world_model.get("ideal_states", [])
        for ideal in ideal_states:
            with st.expander(f"✨ {ideal.get('description', '')}"):
                st.json(ideal)
    else:
        st.error("World Model 파일을 찾을 수 없습니다.")

elif page == "Sensor Layer":
    st.title("👁️ Sensor Layer")
    st.markdown("---")
    st.markdown("외부 데이터 소스에서 현재 상태를 수집하는 계층")
    
    from layers.sensor import load_emails, get_current_state
    
    if st.button("현재 상태 수집"):
        try:
            with st.spinner("이메일 데이터를 로드하는 중..."):
                emails = load_emails()
                current_state = get_current_state(emails)
                st.session_state.current_state = current_state
                st.session_state.original_emails = [e.copy() for e in emails]  # 원본 저장
            
            st.success(f"{len(emails)}개의 이메일을 수집했습니다.")
            
            st.markdown("### 수집된 데이터")
            st.json(current_state)
            
            st.markdown("### 이메일 목록")
            for email in emails[:10]:  # 처음 10개만 표시
                with st.expander(f"📧 {email.get('subject', 'N/A')}"):
                    st.markdown(f"**발신자**: {email.get('sender', 'N/A')}")
                    st.markdown(f"**수신 시간**: {email.get('received_at', 'N/A')}")
                    st.markdown(f"**우선순위**: {email.get('hidden_priority', 'N/A')}")
                    st.markdown(f"**본문**: {email.get('body', 'N/A')[:100]}...")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
            st.exception(e)

elif page == "Expectation Layer":
    st.title("🎯 Expectation Layer")
    st.markdown("---")
    st.markdown("World Model을 기반으로 이상적인 상태를 생성하는 계층")
    
    from layers.expectation import generate_expectation
    
    if st.button("기대 상태 생성"):
        if not client:
            st.warning("⚠️ Anthropic API 키가 설정되지 않았습니다. Claude API를 사용하려면 .env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
            st.info("API 키 없이도 기본 로직으로 작동하지만, Claude API를 사용하면 더 정확한 결과를 얻을 수 있습니다.")
        
        try:
            with st.spinner("기대 상태를 생성하는 중..."):
                expectation = generate_expectation(anthropic_client=client)
                st.session_state.expectation = expectation
            
            st.success("기대 상태를 생성했습니다.")
            st.json(expectation)
            
            st.markdown("### 기대 상태 요약")
            expectations = expectation.get("expectations", [])
            for exp in expectations:
                st.info(f"**{exp.get('description', '')}** (우선순위: {exp.get('priority', 'N/A')})")
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
            st.exception(e)

elif page == "Comparison Layer":
    st.title("⚖️ Comparison Layer")
    st.markdown("---")
    st.markdown("현재 상태와 이상적 상태를 비교하여 Gap을 찾는 계층")
    
    from layers.comparison import compare_states
    
    if st.button("상태 비교"):
        if st.session_state.current_state is None:
            from layers.sensor import get_current_state
            st.session_state.current_state = get_current_state()
        
        if st.session_state.expectation is None:
            from layers.expectation import generate_expectation
            st.session_state.expectation = generate_expectation(anthropic_client=client)
        
        if not client:
            st.warning("⚠️ Anthropic API 키가 설정되지 않았습니다. Claude API를 사용하려면 .env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
            st.info("API 키 없이도 기본 로직으로 작동하지만, Claude API를 사용하면 더 정확한 Gap 분석을 얻을 수 있습니다.")
        
        try:
            with st.spinner("상태를 비교하는 중..."):
                gaps = compare_states(
                    st.session_state.current_state, 
                    st.session_state.expectation,
                    anthropic_client=client
                )
                st.session_state.gaps = gaps
            
            st.success(f"{len(gaps)}개의 Gap을 발견했습니다.")
            
            for gap in gaps:
                with st.expander(f"⚠️ {gap.get('description', '')} (심각도: {gap.get('severity', 'N/A')})"):
                    st.json(gap)
        except Exception as e:
            st.error(f"오류 발생: {str(e)}")
            st.exception(e)

elif page == "Interpretation Layer":
    st.title("🔍 Interpretation Layer")
    st.markdown("---")
    st.markdown("Gap을 문제로 정의하고 해석하는 계층")
    
    from layers.interpretation import interpret_gaps
    
    if st.button("문제 해석"):
        if not st.session_state.gaps:
            st.warning("먼저 Comparison Layer에서 Gap을 찾아주세요.")
        else:
            if not client:
                st.warning("⚠️ Anthropic API 키가 설정되지 않았습니다. Claude API를 사용하려면 .env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
            
            try:
                with st.spinner("문제를 해석하는 중..."):
                    problems = interpret_gaps(st.session_state.gaps, anthropic_client=client)
                    st.session_state.problems = problems
                
                st.success(f"{len(problems)}개의 문제를 정의했습니다.")
                
                for problem in problems:
                    with st.expander(f"🚨 {problem.get('name', '')}"):
                        st.markdown(f"**설명**: {problem.get('description', '')}")
                        st.markdown(f"**원인**: {problem.get('cause', '')}")
                        st.markdown(f"**영향**: {problem.get('impact', '')}")
                        st.json(problem)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                st.exception(e)

elif page == "Exploration Layer":
    st.title("🔎 Exploration Layer")
    st.markdown("---")
    st.markdown("문제에 대한 솔루션을 탐색하는 계층")
    
    from layers.exploration import explore_solutions
    
    if st.button("솔루션 탐색"):
        if not st.session_state.problems:
            st.warning("먼저 Interpretation Layer에서 문제를 정의해주세요.")
        else:
            if not client:
                st.warning("⚠️ Anthropic API 키가 설정되지 않았습니다. Claude API를 사용하려면 .env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
            
            try:
                with st.spinner("솔루션을 탐색하는 중..."):
                    all_solutions = []
                    for problem in st.session_state.problems:
                        solutions = explore_solutions(problem, anthropic_client=client)
                        all_solutions.extend(solutions)
                    st.session_state.solutions = all_solutions
                
                st.success(f"{len(all_solutions)}개의 솔루션을 탐색했습니다.")
                
                for solution in all_solutions:
                    with st.expander(f"💡 {solution.get('name', '')}"):
                        st.markdown(f"**설명**: {solution.get('description', '')}")
                        st.markdown("**장점**:")
                        for pro in solution.get('pros', []):
                            st.markdown(f"- ✅ {pro}")
                        st.markdown("**단점**:")
                        for con in solution.get('cons', []):
                            st.markdown(f"- ❌ {con}")
                        st.markdown(f"**복잡도**: {solution.get('complexity', 'N/A')}")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                st.exception(e)

elif page == "Proposal Layer":
    st.title("💡 Proposal Layer")
    st.markdown("---")
    st.markdown("사용자에게 솔루션을 제안하고 승인을 받는 계층")
    
    from layers.proposal import create_proposal, select_best_solution
    
    # 제안이 이미 생성되어 있는지 확인
    if st.session_state.proposal is None:
        if st.button("제안 생성"):
            if not st.session_state.problems or not st.session_state.solutions:
                st.warning("먼저 Exploration Layer에서 솔루션을 탐색해주세요.")
            else:
                try:
                    with st.spinner("제안을 생성하는 중..."):
                        problem = st.session_state.problems[0]  # 첫 번째 문제 사용
                        solutions = [s for s in st.session_state.solutions if s.get("id", "").startswith("sol_")]
                        
                        proposal = create_proposal(problem, solutions)
                        st.session_state.proposal = proposal
                    st.rerun()
                except Exception as e:
                    st.error(f"오류 발생: {str(e)}")
                    st.exception(e)
    else:
        # 제안이 이미 생성되어 있으면 표시
        proposal = st.session_state.proposal
        status = proposal.get("status", "pending")
        
        st.markdown("### 발견한 문제")
        problem = proposal["problem"]
        st.error(f"🚨 **{problem.get('name', '')}**")
        st.info(problem.get("description", ""))
        st.markdown(f"**원인**: {problem.get('cause', '')}")
        st.markdown(f"**영향**: {problem.get('impact', '')}")
        
        st.markdown("---")
        st.markdown("### 제안된 솔루션")
        
        # 솔루션 3개를 카드로 나란히 배치
        recommended = proposal["recommended_solution"]
        alternatives = proposal.get("alternative_solutions", [])[:2]  # 최대 2개
        
        all_solutions = [recommended] + alternatives
        
        cols = st.columns(min(len(all_solutions), 3))
        for i, solution in enumerate(all_solutions[:3]):
            with cols[i]:
                is_recommended = solution.get("id") == recommended.get("id")
                if is_recommended:
                    st.success("⭐ **권장 솔루션**")
                else:
                    st.info("💡 **대안 솔루션**")
                
                st.markdown(f"### {solution.get('name', '')}")
                st.markdown(solution.get("description", ""))
                
                st.markdown("**장점**:")
                for pro in solution.get('pros', [])[:3]:
                    st.markdown(f"- ✅ {pro}")
                
                st.markdown("**단점**:")
                for con in solution.get('cons', [])[:2]:
                    st.markdown(f"- ❌ {con}")
                
                st.markdown(f"**복잡도**: {solution.get('complexity', 'N/A')}")
        
        st.markdown("---")
        
        # 승인 상태에 따라 버튼 표시
        if status != "approved":
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("승인", key="approve_btn", type="primary", use_container_width=True):
                    st.session_state.proposal["status"] = "approved"
                    st.rerun()
            with col2:
                if st.button("다른 방안", key="alternative_btn", use_container_width=True):
                    st.info("다른 솔루션을 탐색합니다...")
                    st.session_state.proposal = None
                    st.rerun()
            with col3:
                reject_reason = st.text_input("거절 사유 (선택사항)", key="reject_reason")
                if st.button("거절", key="reject_btn", use_container_width=True):
                    st.session_state.proposal["status"] = "rejected"
                    if reject_reason:
                        # World Model에 피드백 저장 (간단한 예시)
                        st.info(f"거절 사유가 기록되었습니다: {reject_reason}")
                    st.rerun()
        else:
            st.success("제안이 승인되었습니다!")
            st.info("💡 Composition Layer로 이동하여 에이전트를 구성하세요.")

elif page == "Composition Layer":
    st.title("🔧 Composition Layer")
    st.markdown("---")
    st.markdown("솔루션을 구현하기 위한 LLM과 도구를 동적으로 선택하고 조합하는 계층")
    
    from layers.composition import compose_agent
    
    # 제안 상태 확인 및 표시
    if st.session_state.proposal is None:
        st.warning("⚠️ 제안이 생성되지 않았습니다. 먼저 Proposal Layer에서 제안을 생성해주세요.")
        st.info("💡 Proposal Layer로 이동하여 제안을 생성하고 승인하세요.")
    elif st.session_state.proposal.get("status") != "approved":
        current_status = st.session_state.proposal.get("status", "pending")
        st.warning(f"⚠️ 제안이 승인되지 않았습니다. (현재 상태: {current_status})")
        st.info("💡 Proposal Layer로 이동하여 제안을 승인하세요.")
    else:
        # 제안이 승인된 경우
        st.success("승인된 제안이 있습니다.")
        
        if st.button("에이전트 구성"):
            try:
                with st.spinner("에이전트를 구성하는 중..."):
                    solution = st.session_state.proposal["recommended_solution"]
                    agent_config = compose_agent(solution)
                    st.session_state.agent_config = agent_config
                
                st.success("에이전트 구성을 완료했습니다.")
                
                st.markdown("### 구성된 에이전트")
                st.json(agent_config)
                
                st.markdown("### 워크플로우")
                workflow = agent_config.get("workflow", [])
                for step in workflow:
                    st.markdown(f"**{step['step']}단계**: {step['action']} (도구: {step['tool']})")
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                st.exception(e)
        
        # 이미 구성된 에이전트가 있으면 표시
        if st.session_state.agent_config is not None:
            st.markdown("---")
            st.markdown("### 이미 구성된 에이전트")
            st.json(st.session_state.agent_config)

elif page == "Execution Layer":
    st.title("⚡ Execution Layer")
    st.markdown("---")
    st.markdown("구성된 에이전트를 실행하는 계층")
    
    from layers.execution import execute_agent
    
    if st.button("실행"):
        if st.session_state.agent_config is None:
            st.warning("먼저 Composition Layer에서 에이전트를 구성해주세요.")
        else:
            # 이메일 데이터 가져오기
            emails = None
            if st.session_state.current_state:
                emails = st.session_state.current_state.get("data", {}).get("emails", [])
            
            try:
                with st.spinner("에이전트를 실행하는 중..."):
                    execution_result = execute_agent(
                        st.session_state.agent_config,
                        emails=emails
                    )
                    st.session_state.execution_result = execution_result
                
                st.success("실행이 완료되었습니다.")
                
                st.markdown("### 실행 결과 요약")
                summary = execution_result.get("summary", {})
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("총 단계", summary.get("total_steps", 0))
                with col2:
                    st.metric("완료 단계", summary.get("completed_steps", 0))
                with col3:
                    st.metric("성공률", f"{summary.get('success_rate', 0) * 100:.0f}%")
                with col4:
                    st.metric("처리된 이메일", summary.get("processed_count", 0))
                
                # Before/After 비교
                if st.session_state.original_emails and execution_result.get("processed_emails"):
                    st.markdown("---")
                    st.markdown("### 📊 Before/After 비교")
                    
                    original = st.session_state.original_emails[:10]
                    processed = execution_result["processed_emails"][:10]
                    
                    comparison_data = []
                    for orig, proc in zip(original, processed):
                        comparison_data.append({
                            "이메일 ID": orig.get("id", ""),
                            "제목": orig.get("subject", "")[:50],
                            "Before: 우선순위": orig.get("hidden_priority", "N/A"),
                            "After: 라벨": proc.get("applied_label", "N/A"),
                            "After: 우선순위": proc.get("applied_priority", "N/A"),
                            "After: 점수": proc.get("priority_score", "N/A")
                        })
                    
                    df = pd.DataFrame(comparison_data)
                    st.dataframe(df, use_container_width=True)
                
                st.markdown("### 단계별 결과")
                for result in execution_result.get("workflow_results", []):
                    with st.expander(f"✅ {result.get('action', 'N/A')}"):
                        st.json(result)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                st.exception(e)

elif page == "Learning Layer":
    st.title("📚 Learning Layer")
    st.markdown("---")
    st.markdown("실행 결과를 관찰하고 World Model을 업데이트하는 계층")
    
    from layers.learning import analyze_results, update_world_model
    
    if st.button("📚 학습 및 업데이트"):
        if st.session_state.execution_result is None:
            st.warning("먼저 Execution Layer에서 실행을 완료해주세요.")
        else:
            try:
                with st.spinner("결과를 분석하는 중..."):
                    # World Model 백업
                    world_model_path = Path("data/world_model.json")
                    if world_model_path.exists() and st.session_state.world_model_before is None:
                        with open(world_model_path, "r", encoding="utf-8") as f:
                            st.session_state.world_model_before = json.load(f)
                    
                    # 결과 분석
                    analysis = analyze_results(st.session_state.execution_result)
                
                st.success("✅ 결과를 분석했습니다.")
                
                st.markdown("### 분석 결과")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("성공률", f"{analysis.get('success_rate', 0) * 100:.0f}%")
                with col2:
                    st.metric("처리된 항목", analysis.get("processed_items", 0))
                
                # World Model 업데이트
                if st.button("🔄 World Model 업데이트"):
                    try:
                        with st.spinner("World Model을 업데이트하는 중..."):
                            updated_model = update_world_model(analysis)
                            st.session_state.world_model = updated_model
                        
                        st.success("✅ World Model이 업데이트되었습니다.")
                        
                        # 변경사항 diff 표시
                        if st.session_state.world_model_before:
                            st.markdown("---")
                            st.markdown("### 📝 World Model 변경사항")
                            
                            before_patterns = len(st.session_state.world_model_before.get("patterns", []))
                            after_patterns = len(updated_model.get("patterns", []))
                            
                            if after_patterns > before_patterns:
                                st.success(f"✅ 새로운 패턴 {after_patterns - before_patterns}개가 추가되었습니다.")
                                
                                # 새로 추가된 패턴 표시
                                new_patterns = updated_model.get("patterns", [])[before_patterns:]
                                for pattern in new_patterns:
                                    with st.expander(f"🆕 {pattern.get('behavior', '')}"):
                                        st.json(pattern)
                            
                            st.markdown("**업데이트 시간**: " + updated_model.get("updated_at", "N/A"))
                    except Exception as e:
                        st.error(f"오류 발생: {str(e)}")
                        st.exception(e)
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                st.exception(e)

elif page == "에이전트 데모":
    st.title("에이전트 데모")
    st.markdown("---")
    st.markdown("SIA로 생성된 에이전트가 실시간으로 이메일을 분류하는 과정을 확인하세요.")
    
    # 에이전트가 구성되어 있는지 확인
    if not st.session_state.agent_config:
        st.error("에이전트가 구성되지 않았습니다.")
        st.info("먼저 홈 화면에서 'SIA 전체 플로우 실행'을 실행하거나, 각 계층을 순차적으로 진행하여 에이전트를 생성하세요.")
        st.markdown("**필요한 단계:**")
        st.markdown("1. Sensor Layer → 현재 상태 수집")
        st.markdown("2. Expectation Layer → 기대 상태 생성")
        st.markdown("3. Comparison Layer → 상태 비교")
        st.markdown("4. Interpretation Layer → 문제 해석")
        st.markdown("5. Exploration Layer → 솔루션 탐색")
        st.markdown("6. Proposal Layer → 제안 승인")
        st.markdown("7. Composition Layer → 에이전트 구성")
        st.stop()
    
    # 랜덤 이메일 생성 함수
    def generate_random_emails(count=10):
        """랜덤 이메일을 생성합니다."""
        senders = [
            ("박상사", "park.sangsa@company.com", "high"),
            ("마케팅팀", "marketing@company.com", "high"),
            ("이동료", "lee.dongryo@company.com", "medium"),
            ("HR팀", "hr@company.com", "medium"),
            ("외부 협력사", "partner@external.com", "medium"),
            ("스팸", "spam@fake.com", "low"),
            ("뉴스레터", "newsletter@service.com", "low"),
        ]
        
        subjects_high = [
            "[긴급] 회의 일정 변경",
            "[중요] 프로젝트 승인 요청",
            "[긴급] 예산 승인 필요",
            "[중요] 마감일 임박 안내",
            "[긴급] 시스템 점검 공지"
        ]
        
        subjects_medium = [
            "주간보고 요청",
            "회의록 공유",
            "프로젝트 업데이트",
            "건강검진 안내",
            "팀 빌딩 이벤트"
        ]
        
        subjects_low = [
            "할인 쿠폰 발급",
            "월간 뉴스레터",
            "서비스 안내",
            "마케팅 이벤트",
            "구독 갱신 안내"
        ]
        
        emails = []
        for i in range(count):
            sender_info = random.choice(senders)
            sender, sender_email, priority = sender_info
            
            if priority == "high":
                subject = random.choice(subjects_high)
            elif priority == "medium":
                subject = random.choice(subjects_medium)
            else:
                subject = random.choice(subjects_low)
            
            email = {
                "id": f"demo_email_{i+1}",
                "sender": sender,
                "sender_email": sender_email,
                "subject": subject,
                "body": f"이메일 본문 내용입니다. {subject} 관련 내용입니다.",
                "received_at": datetime.now().isoformat(),
                "hidden_priority": priority
            }
            emails.append(email)
        
        return emails
    
    # 에이전트 정보 표시
    st.markdown("### 현재 활성화된 에이전트")
    
    agent_config = st.session_state.agent_config
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**에이전트 이름**: {agent_config.get('solution_name', 'N/A')}")
    with col2:
        st.info(f"**에이전트 ID**: {agent_config.get('id', 'N/A')}")
    
    st.markdown("**적용된 규칙**:")
    workflow = agent_config.get("workflow", [])
    for step in workflow:
        st.markdown(f"- {step.get('action', 'N/A')} → {step.get('tool', 'N/A')}")
    
    st.markdown("---")
    
    # 데모 시작 버튼
    if st.button("데모 시작", type="primary", use_container_width=True):
        # 랜덤 이메일 생성
        demo_emails = generate_random_emails(10)
        
        st.markdown("### 실시간 분류 데모")
        st.markdown("에이전트가 이메일을 하나씩 분석하고 분류하는 과정을 확인하세요.")
        
        # 결과 저장용
        results = []
        status_container = st.container()
        
        # 각 이메일 처리
        for i, email in enumerate(demo_emails):
            with status_container:
                # 새 이메일 도착 표시
                st.markdown(f"---")
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**새 이메일 도착**: {email.get('subject', 'N/A')}")
                    st.caption(f"발신자: {email.get('sender', 'N/A')} | 수신 시간: {email.get('received_at', 'N/A')[:19]}")
                
                # 분석 중 표시
                with st.status(f"분석 중... ({i+1}/10)", state="running") as status:
                    time.sleep(0.5)  # 분석 시뮬레이션
                    
                    # 분류 로직 (간단한 시뮬레이션)
                    priority = email.get("hidden_priority", "medium")
                    
                    if priority == "high":
                        label = "긴급"
                        priority_display = "High"
                    elif priority == "medium":
                        label = "일반"
                        priority_display = "Medium"
                    else:
                        label = "낮음"
                        priority_display = "Low"
                    
                    # 결과 저장
                    result = {
                        "id": email.get("id"),
                        "subject": email.get("subject"),
                        "sender": email.get("sender"),
                        "priority": priority_display,
                        "label": label,
                        "original_priority": priority
                    }
                    results.append(result)
                    
                    status.update(
                        label=f"분석 완료: 우선순위 {priority_display}, 라벨: {label}",
                        state="complete"
                    )
                    
                    time.sleep(0.3)
        
        st.markdown("---")
        st.success("데모가 완료되었습니다!")
        
        # 결과 요약
        st.markdown("### 결과 요약")
        
        # 우선순위별 분포
        priority_counts = {"High": 0, "Medium": 0, "Low": 0}
        for result in results:
            priority_counts[result["priority"]] += 1
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("High 우선순위", priority_counts["High"])
        with col2:
            st.metric("Medium 우선순위", priority_counts["Medium"])
        with col3:
            st.metric("Low 우선순위", priority_counts["Low"])
        
        # 차트로 시각화
        st.markdown("#### 우선순위별 분포")
        chart_data = pd.DataFrame({
            "우선순위": ["High", "Medium", "Low"],
            "개수": [priority_counts["High"], priority_counts["Medium"], priority_counts["Low"]]
        })
        st.bar_chart(chart_data.set_index("우선순위"))
        
        # 처리된 이메일 상세
        st.markdown("#### 처리된 이메일 상세")
        results_df = pd.DataFrame(results)
        st.dataframe(
            results_df[["subject", "sender", "priority", "label"]],
            use_container_width=True,
            hide_index=True
        )
        
        # 세션 상태에 저장
        st.session_state.demo_results = results
