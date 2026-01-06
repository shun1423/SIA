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
# 원본 데이터 저장용 (도메인별)
if "original_emails" not in st.session_state:
    st.session_state.original_emails = None
if "original_prs" not in st.session_state:
    st.session_state.original_prs = None
if "original_health" not in st.session_state:
    st.session_state.original_health = None
if "original_finance" not in st.session_state:
    st.session_state.original_finance = None
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
        st.success("✅ Anthropic API 연결됨 (실제 동작 모드)")
    else:
        st.warning("⚠️ API 키 없음 (데모 모드)")
        st.info("`.env` 파일에 `ANTHROPIC_API_KEY`를 설정하면 실제 Claude API를 사용합니다.")
        st.caption("현재는 하드코딩된 폴백 로직을 사용합니다.")
    
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
    page_options = [
            "홈",
        "온보딩",
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
    ]
    
    # 세션 상태에서 페이지 가져오기 (온보딩 후 자동 전환용)
    if "page" not in st.session_state:
        st.session_state.page = "홈"
    
    # 페이지 선택 라디오 버튼
    # 세션 상태에서 현재 페이지 가져오기
    if "page" not in st.session_state:
        st.session_state.page = "홈"
    
    # 라디오 버튼의 현재 인덱스 계산
    try:
        current_index = page_options.index(st.session_state.page)
    except ValueError:
        current_index = 0
        st.session_state.page = "홈"
    
    page = st.radio(
        "계층 선택",
        page_options,
        index=current_index,
        label_visibility="collapsed",
        key="page_radio"
    )
    
    # 라디오 버튼 선택값을 세션 상태에 저장
    st.session_state.page = page

# 데모 자동 실행 함수
def run_demo():
    """전체 플로우를 자동으로 실행합니다."""
    st.session_state.demo_running = True
    
    try:
        # World Model 로드 (먼저)
        from layers.expectation import load_world_model
        world_model = load_world_model()
        st.session_state.world_model = world_model
        
        # 연결된 소스 확인
        connected_sources = world_model.get("connected_sources", [])
        active_sources = [s for s in connected_sources if s.get("status") == "active"]
        
        # active_sources가 없어도 샘플 데이터로 데모 가능 (경고만 표시)
        if not active_sources:
            st.warning("⚠️ 연결된 데이터 소스가 없습니다. 샘플 데이터로 데모를 진행합니다.")
        
        # 소스별 도메인 매핑
        source_to_domain = {
            "Gmail": "email",
            "GitHub": "github",
            "Apple Health": "health",
            "Finance App": "finance",
            "카드사": "finance",
            "은행": "finance"
        }
        
        # 온보딩에서 선택한 소스에 따라 도메인 추출
        onboarding_domains = []
        if active_sources:
            for source in active_sources:
                source_name = source.get("name", "")
                domain = source_to_domain.get(source_name)
                if domain and domain not in onboarding_domains:
                    onboarding_domains.append(domain)
        
        # 데모용 도메인 선택
        st.markdown("---")
        st.markdown("### 🎯 데모 도메인 선택")
        
        all_demo_domains = {
            "email": "📧 이메일 (Gmail) - 중요 메일 가시성, 응답 시간",
            "github": "🔀 GitHub (PR 리뷰) - 리뷰 지연, PR 우선순위",
            "health": "💚 건강 (Apple Health) - 수면 시간, 활동량",
            "finance": "💰 재정 (카드/은행) - 지출 패턴, 예산 초과"
        }
        
        # 온보딩에서 선택한 도메인이 있으면 기본값으로 설정
        if onboarding_domains:
            default_domain = onboarding_domains[0]
            st.info(f"💡 온보딩에서 연결한 소스: {', '.join([s.get('name', '') for s in active_sources])}")
            st.caption(f"💡 기본 도메인: {all_demo_domains.get(default_domain, default_domain)} (온보딩 선택)")
            
            # 온보딩 도메인을 기본값으로, 다른 도메인도 선택 가능
            selected_demo_domain = st.selectbox(
                "데모할 도메인을 선택하세요:",
                options=list(all_demo_domains.keys()),
                index=list(all_demo_domains.keys()).index(default_domain) if default_domain in all_demo_domains else 0,
                format_func=lambda x: all_demo_domains.get(x, x),
                key="demo_domain_selector_main",
                help="온보딩에서 선택한 도메인이 기본값으로 설정됩니다. 다른 도메인도 선택할 수 있습니다."
            )
        else:
            st.warning("⚠️ 온보딩에서 소스를 연결하지 않았습니다. 샘플 데이터로 데모를 진행합니다.")
            st.caption("💡 원하는 도메인을 선택하여 데모할 수 있습니다.")
            
            selected_demo_domain = st.selectbox(
                "데모할 도메인을 선택하세요:",
                options=list(all_demo_domains.keys()),
                format_func=lambda x: all_demo_domains.get(x, x),
                key="demo_domain_selector_main",
                help="각 도메인별로 다른 문제와 솔루션을 데모할 수 있습니다."
            )
        
        # 선택된 도메인으로 available_domains 설정
        available_domains = [selected_demo_domain]
        
        # 세션 상태에 선택된 도메인 저장 (모든 레이어에서 일관되게 사용)
        st.session_state.selected_domain = selected_demo_domain
        
        # 1. Sensor Layer - 선택된 도메인에서 데이터 수집
        from layers.sensor import get_current_state
        
        domain_labels = {
            "email": "📧 이메일",
            "github": "🔀 GitHub",
            "health": "💚 건강",
            "finance": "💰 재정"
        }
        
        selected_domain = available_domains[0]
        domain_display = domain_labels.get(selected_domain, selected_domain)
        
        with st.spinner(f"📥 {domain_display} 도메인 데이터 수집 중..."):
            current_state = get_current_state(domain=selected_domain, world_model=world_model)
        
        st.session_state.current_state = current_state
        
        # 관찰 기간 설명 (데모 모드)
        st.markdown("---")
        st.markdown("### 📊 관찰 기간 시뮬레이션")
        st.info("""
        **데모 모드**: 실제 2-4주 관찰 대신 샘플 데이터를 사용합니다.
        
        실제 운영 시에는:
        - **1주차**: 도메인 기본값으로 탐지 시작
        - **2주차**: 개인 베이스라인 계산 완료  
        - **3주차~**: 개인화된 Problem Score 적용
        
        지금은 샘플 데이터가 **이미 2-4주 관찰이 완료된 상태**로 가정됩니다.
        """)
        
        # 베이스라인 계산 안내
        with st.expander("📈 개인 베이스라인 계산 중...", expanded=False):
            from utils.baseline_calculator import calculate_baseline
            baseline_info = calculate_baseline(
                domain=available_domains[0] if available_domains else "email",
                current_state=current_state,
                world_model=world_model,
                weeks=3
            )
            if baseline_info:
                st.json(baseline_info)
                st.caption(f"💡 {baseline_info.get('baseline_period', '3주')}간의 데이터를 기반으로 개인 베이스라인을 계산했습니다.")
            else:
                st.info("💡 히스토리 데이터가 없어 기본값을 사용합니다. (실제 운영 시에는 과거 2-4주 데이터로 계산)")
        
        # 원본 데이터 저장 (도메인별)
        data = current_state.get("data", {})
        if "emails" in data:
            st.session_state.original_emails = data.get("emails", [])
        if "prs" in data:
            st.session_state.original_prs = data.get("prs", [])
        if "health_records" in data:
            st.session_state.original_health = data.get("health_records", [])
        if "transactions" in data:
            st.session_state.original_finance = data.get("transactions", [])
        
        # 선택된 도메인 사용
        selected_domain = available_domains[0]
        
        # 도메인별 데이터 수집 결과 표시
        st.success(f"✅ {domain_display} 도메인 데이터 수집 완료!")
        
        # 도메인별 데이터 요약 표시
        if selected_domain == "email":
            email_count = data.get("total_emails", len(data.get("emails", [])))
            st.caption(f"📊 수집된 이메일: {email_count}개")
        elif selected_domain == "github":
            pr_count = data.get("total_prs", len(data.get("prs", [])))
            st.caption(f"📊 수집된 PR: {pr_count}개")
        elif selected_domain == "health":
            record_count = data.get("total_records", len(data.get("records", [])))
            st.caption(f"📊 수집된 건강 기록: {record_count}개")
        elif selected_domain == "finance":
            txn_count = data.get("total_transactions", len(data.get("transactions", [])))
            st.caption(f"📊 수집된 거래 내역: {txn_count}개")
        
        # 2. Expectation Layer
        from layers.expectation import generate_expectation
        with st.spinner("🎯 기대 상태 생성 중 (World Model + 현재 맥락 기반)..."):
            # current_state의 domain이 없거나 다르면 selected_domain 사용
            current_state_domain = current_state.get("domain")
            if current_state_domain and current_state_domain != selected_domain:
                st.warning(f"⚠️ 현재 상태의 도메인({current_state_domain})과 선택된 도메인({selected_domain})이 다릅니다. 선택된 도메인을 사용합니다.")
                domain = selected_domain
            else:
                domain = current_state_domain if current_state_domain else selected_domain
            
            # current_state에 domain 명시적으로 설정 (일관성 유지)
            if not current_state.get("domain"):
                current_state["domain"] = domain
                st.session_state.current_state = current_state
            
            expectation = generate_expectation(
                world_model=world_model,
                domain=domain,
                anthropic_client=client
            )
            st.session_state.expectation = expectation
            
            # 기대 상태 설명
            st.caption(f"💡 추상적 목표 '{', '.join([g.get('text', '') for g in world_model.get('abstract_goals', [])[:2]])}'를 {domain} 도메인의 구체적 기대 상태로 변환했습니다.")
        
        # 3. Comparison Layer
        from layers.comparison import compare_states
        with st.spinner("⚖️ 상태 비교 중 (Tiered Inference: Cheap Detection → LLM 해석)..."):
            gaps = compare_states(
                current_state, 
                expectation, 
                anthropic_client=client,
                world_model=world_model
            )
            st.session_state.gaps = gaps
            
            # Tiered Inference 설명
            if gaps:
                st.caption(f"💡 규칙/통계 기반 탐지로 {len(gaps)}개 Gap 후보를 발견했습니다. (Cheap Detection)")
                st.caption("💡 각 Gap에 Problem Score를 계산하여 개인 베이스라인과 비교했습니다.")
        
        # 4. Interpretation Layer
        from layers.interpretation import interpret_gaps
        from utils.problem_state_machine import ProblemStateMachine
        with st.spinner("🔍 문제 해석 중 (Gap → Problem Candidate로 변환)..."):
            problems = interpret_gaps(gaps, anthropic_client=client)
            # 문제를 Problem Candidates로 변환
            problem_candidates = []
            for problem in problems:
                problem_candidates.append(problem)
            st.session_state.problems = problems
            st.session_state.problem_candidates = problem_candidates
            
            # 문제 상태 머신 설명
            if problems:
                st.caption(f"💡 {len(problems)}개 Gap을 문제 후보(Candidate)로 변환했습니다. 사용자 승인 후 확정 문제(Confirmed)로 전이됩니다.")
        
        # 5. Exploration Layer
        from layers.exploration import explore_solutions
        with st.spinner("🔎 솔루션 탐색 중 (각 문제에 대한 해결책 3개 제안)..."):
            all_solutions = []
            for problem in problems:
                solutions = explore_solutions(problem, anthropic_client=client)
                all_solutions.extend(solutions)
            st.session_state.solutions = all_solutions
            
            if all_solutions:
                st.caption(f"💡 {len(all_solutions)}개의 솔루션을 탐색했습니다. 각 솔루션의 장단점과 구현 복잡도를 평가했습니다.")
        
        # 6. Proposal Layer
        from layers.proposal import create_proposal
        from utils.problem_state_machine import ProblemStateMachine
        with st.spinner("💡 제안 생성 중 (문제 후보 → Proposed 상태 전이)..."):
            if not problems:
                st.warning("⚠️ 해석된 문제가 없습니다. Interpretation Layer를 확인해주세요.")
                st.session_state.demo_running = False
                return
            
            if not all_solutions:
                st.warning("⚠️ 탐색된 솔루션이 없습니다. Exploration Layer를 확인해주세요.")
                st.session_state.demo_running = False
                return
            
            problem = problems[0]
            solutions = [s for s in all_solutions if s.get("id", "").startswith("sol_")]
            
            if not solutions:
                st.warning("⚠️ 유효한 솔루션이 없습니다. 솔루션 ID 형식을 확인해주세요.")
                st.session_state.demo_running = False
                return
            
            try:
                proposal = create_proposal(problem, solutions)
            except Exception as e:
                st.error(f"❌ 제안 생성 중 오류 발생: {str(e)}")
                st.exception(e)
                st.session_state.demo_running = False
                return
            
            if not proposal:
                st.error("❌ 제안 생성에 실패했습니다.")
                st.session_state.demo_running = False
                return
            
            # recommended_solution 확인
            if not proposal.get("recommended_solution"):
                st.error("❌ 제안에 추천 솔루션이 없습니다.")
                st.info("💡 솔루션 선택에 실패했습니다.")
                st.session_state.demo_running = False
                return
            
            # 문제를 Proposed 상태로 전이
            if problem.get("status") == "candidate":
                problem = ProblemStateMachine.promote_candidate_to_proposed(problem)
            
            proposal["status"] = "approved"  # 데모에서는 자동 승인
            
            # 문제를 Confirmed 상태로 전이
            if proposal["status"] == "approved":
                problem = ProblemStateMachine.confirm_problem(problem)
                # World Model에 추가
                if "confirmed_problems" not in world_model:
                    world_model["confirmed_problems"] = []
                world_model["confirmed_problems"].append(problem)
            
            st.session_state.proposal = proposal
            st.session_state.problems = [problem]  # 업데이트된 문제로 교체
            
            st.caption(f"💡 문제를 Proposed → Confirmed 상태로 전이했습니다. (데모 모드: 자동 승인)")
        
        # 7. Composition Layer
        from layers.composition import compose_agent
        with st.spinner("🔧 에이전트 구성 중 (v3.2: 트리거, 입력, 도구, 로직, 액션, 안전 정책)..."):
            if not st.session_state.proposal:
                st.error("❌ 제안이 생성되지 않았습니다. Proposal Layer를 확인해주세요.")
                st.info("💡 문제나 솔루션이 없어서 제안을 생성할 수 없습니다.")
                st.session_state.demo_running = False
                return
            
            solution = st.session_state.proposal.get("recommended_solution")
            if not solution:
                st.error("❌ 제안에 추천 솔루션이 없습니다.")
                st.info("💡 Proposal Layer에서 솔루션을 선택하지 못했습니다.")
                st.session_state.demo_running = False
                return
            
            problem = st.session_state.problems[0] if st.session_state.problems else None
            
            try:
                agent_config = compose_agent(
                    solution,
                    problem=problem,
                    world_model=world_model
                )
            except ValueError as e:
                st.error(f"❌ 에이전트 구성 중 오류 발생: {str(e)}")
                st.info("💡 온보딩에서 데이터 소스를 연결했는지 확인하거나, 문제/솔루션에 도메인 정보가 포함되어 있는지 확인하세요.")
                st.session_state.demo_running = False
                return
            except Exception as e:
                st.error(f"❌ 에이전트 구성 중 예상치 못한 오류 발생: {str(e)}")
                st.exception(e)
                st.session_state.demo_running = False
                return
            
            if not agent_config:
                st.error("❌ 에이전트 구성에 실패했습니다.")
                st.info("💡 솔루션 정보를 확인해주세요.")
                st.session_state.demo_running = False
                return
            
            st.session_state.agent_config = agent_config
            
            # Active Agents에 추가
            if "active_agents" not in world_model:
                world_model["active_agents"] = []
            world_model["active_agents"].append({
                "id": agent_config.get("id"),
                "solution_name": agent_config.get("solution_name"),
                "created_at": agent_config.get("created_at"),
                "status": "active"
            })
            
            st.caption(f"💡 에이전트 '{agent_config.get('solution_name')}'를 구성했습니다. 트리거, 도구, 로직, 액션이 동적으로 선택되었습니다.")
        
        # 8. Execution Layer
        from layers.execution import execute_agent
        with st.spinner("⚡ 에이전트 실행 중 (멱등성, 레이트리밋, 충돌 관리 적용)..."):
            # agent_config 존재 확인
            if not st.session_state.agent_config:
                st.error("❌ 에이전트 구성이 없습니다. Composition Layer를 확인해주세요.")
                st.session_state.demo_running = False
                return
            
            # 도메인별 입력 데이터 준비
            input_data = {}
            agent_domain = st.session_state.agent_config.get("domain")
            
            if not agent_domain:
                st.error("❌ 에이전트에 도메인 정보가 없습니다.")
                st.info("에이전트를 다시 구성해주세요.")
                st.session_state.demo_running = False
                return
            
            # 에이전트 도메인과 선택된 도메인이 일치하는지 확인
            if agent_domain != selected_domain:
                st.warning(f"⚠️ 에이전트 도메인({agent_domain})과 선택된 도메인({selected_domain})이 다릅니다. 에이전트 도메인을 사용합니다.")
                selected_domain = agent_domain
            
            if agent_domain == "email":
                input_data["emails"] = current_state.get("data", {}).get("emails", [])
            elif agent_domain == "github":
                input_data["prs"] = current_state.get("data", {}).get("prs", [])
            elif agent_domain == "health":
                input_data["records"] = current_state.get("data", {}).get("records", [])
            elif agent_domain == "finance":
                input_data["transactions"] = current_state.get("data", {}).get("transactions", [])
            
            execution_result = execute_agent(
                st.session_state.agent_config,
                input_data=input_data if input_data else None,
                world_model=world_model
            )
            st.session_state.execution_result = execution_result
        
        # 9. Learning Layer
        from layers.learning import analyze_results, update_world_model
        with st.spinner("📚 학습 및 업데이트 중 (실행 결과 → World Model 업데이트)..."):
            # World Model 백업
            world_model_path = Path("data/world_model.json")
            if world_model_path.exists():
                with open(world_model_path, "r", encoding="utf-8") as f:
                    st.session_state.world_model_before = json.load(f)
            
            analysis = analyze_results(execution_result)
            updated_model = update_world_model(
                analysis, 
                world_model_path="data/world_model.json",
                execution_result=execution_result
            )
            
            # World Model 파일에 저장
            with open(world_model_path, "w", encoding="utf-8") as f:
                json.dump(updated_model, f, ensure_ascii=False, indent=2)
            
            st.session_state.world_model = updated_model
        
        st.session_state.demo_running = False
        
        # 완료 메시지와 결과 요약
        st.success("✅ 전체 플로우 실행이 완료되었습니다!")
        
        st.markdown("---")
        st.markdown("### 📊 실행 결과 요약")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("발견된 Gap", len(st.session_state.gaps) if st.session_state.gaps else 0)
        with col2:
            st.metric("해석된 문제", len(st.session_state.problems) if st.session_state.problems else 0)
        with col3:
            st.metric("탐색된 솔루션", len(st.session_state.solutions) if st.session_state.solutions else 0)
        with col4:
            st.metric("생성된 에이전트", 1 if st.session_state.agent_config else 0)
        
        st.markdown("---")
        st.markdown("### 🎯 다음 단계")
        st.info("""
        **각 레이어 페이지에서 상세 결과를 확인할 수 있습니다:**
        
        1. **Sensor Layer**: 수집된 데이터 확인
        2. **Expectation Layer**: 생성된 기대 상태 확인
        3. **Comparison Layer**: 발견된 Gap 확인
        4. **Interpretation Layer**: 해석된 문제 확인
        5. **Exploration Layer**: 탐색된 솔루션 확인
        6. **Proposal Layer**: 제안된 솔루션 확인 및 승인
        7. **Composition Layer**: 구성된 에이전트 확인
        8. **Execution Layer**: 에이전트 실행 및 결과 확인
        9. **Learning Layer**: 학습 결과 및 World Model 업데이트 확인
        """)
        
        if st.session_state.agent_config:
            st.success("💡 에이전트가 구성되었습니다! Execution Layer에서 실행해보세요.")
        
    except Exception as e:
        st.session_state.demo_running = False
        st.error(f"데모 실행 중 오류 발생: {str(e)}")
        st.exception(e)
        st.info("💡 오류가 발생했습니다. 각 레이어를 개별적으로 실행해보세요.")

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
        
        # 온보딩 완료 후 자동 실행 플래그 확인
        if st.session_state.get("run_full_flow_after_onboarding", False):
            st.session_state.run_full_flow_after_onboarding = False
            # 온보딩 완료 후 자동 실행 안내
            st.info("🎉 온보딩이 완료되었습니다! 전체 플로우를 자동으로 실행합니다...")
            run_demo()
        elif st.button("SIA 전체 플로우 실행", type="primary", use_container_width=True):
            # 온보딩 데이터 확인
            world_model_path = Path("data/world_model.json")
            if not world_model_path.exists():
                st.error("❌ 온보딩이 완료되지 않았습니다.")
                st.info("온보딩 페이지에서 초기 설정을 먼저 완료해주세요.")
            else:
                from layers.expectation import load_world_model
                world_model = load_world_model()
                connected_sources = world_model.get("connected_sources", [])
                active_sources = [s for s in connected_sources if s.get("status") == "active"]
                if not active_sources:
                    st.error("❌ 연결된 데이터 소스가 없습니다.")
                    st.info("온보딩 페이지에서 데이터 소스를 연결해주세요.")
                else:
                    run_demo()
        
        # 온보딩 안내
        world_model_path = Path("data/world_model.json")
        if not world_model_path.exists():
            st.warning("⚠️ 온보딩이 필요합니다")
            st.caption("온보딩 페이지에서 초기 설정을 완료하세요.")
        
        st.markdown("---")
        st.markdown("### 현재 상태")
        steps = get_progress_steps()
        completed = sum(1 for _, c in steps if c)
        st.metric("완료된 단계", f"{completed}/10")
        
        if completed == 10:
            st.success("모든 단계 완료!")
            st.info("에이전트 데모 페이지에서 생성된 에이전트를 테스트할 수 있습니다.")
    
    # 시스템 상태 표시
    st.markdown("---")
    st.markdown("### 시스템 상태")
    from utils.diagnostic import get_operation_mode
    mode = get_operation_mode()
    if mode == "real":
        st.success("🟢 실제 동작 모드: Claude API를 사용합니다")
    else:
        st.warning("🟡 데모 모드: 하드코딩된 폴백 로직을 사용합니다")
        st.caption("실제 동작을 원하면 .env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
    
    # 현재 World Model 미리보기
    st.markdown("---")
    st.markdown("### 현재 World Model")
    
    world_model_path = Path("data/world_model.json")
    if world_model_path.exists():
        with open(world_model_path, "r", encoding="utf-8") as f:
            world_model = json.load(f)
        
        abstract_goals = world_model.get("abstract_goals", [])
        connected_sources = world_model.get("connected_sources", [])
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**추상적 목표**: {len(abstract_goals)}개")
        with col2:
            st.info(f"**연결된 소스**: {len(connected_sources)}개")
        with col3:
            active_agents = world_model.get("active_agents", [])
            st.info(f"**활성 에이전트**: {len(active_agents)}개")
    else:
        st.warning("World Model 데이터를 찾을 수 없습니다.")
        st.info("💡 온보딩 페이지에서 초기 설정을 완료하세요.")

elif page == "온보딩":
    st.title("🚀 SIA 온보딩")
    st.markdown("---")
    st.markdown("SIA를 시작하기 위해 몇 가지 정보를 입력해주세요. (약 5분 소요)")
    
    from layers.onboarding import (
        create_onboarding_data,
        save_world_model,
        load_onboarding_template,
        validate_onboarding_data
    )
    
    template = load_onboarding_template()
    
    # 온보딩 단계 관리
    if "onboarding_step" not in st.session_state:
        st.session_state.onboarding_step = 1
    
    # Step 1: 목표 입력
    if st.session_state.onboarding_step == 1:
        st.markdown("### Step 1: 목표 입력 (2분)")
        st.info("구체적인 문제를 말씀하실 필요 없어요. 대략적인 방향만 알려주세요.")
        
        st.markdown("**추상적 목표 선택** (복수 선택 가능):")
        selected_goals = []
        for goal in template["abstract_goal_options"]:
            if st.checkbox(goal, key=f"goal_{goal}"):
                selected_goals.append(goal)
        
        st.markdown("---")
        st.markdown("**또는 직접 입력하기**")
        custom_goal = st.text_input(
            "직접 목표를 입력하세요 (선택사항)",
            value="",
            key="custom_goal",
            placeholder="예: 회의 준비 시간을 줄이고 싶어"
        )
        
        if custom_goal and custom_goal.strip():
            if st.button("직접 입력한 목표 추가", use_container_width=True):
                if custom_goal.strip() not in selected_goals:
                    selected_goals.append(custom_goal.strip())
                    st.success(f"목표가 추가되었습니다: {custom_goal.strip()}")
                    st.rerun()
        
        if st.button("다음 단계", type="primary", use_container_width=True):
            # 검증
            validation = validate_onboarding_data(
                selected_goals, []
            )
            
            if validation["valid"]:
                st.session_state.onboarding_goals = selected_goals
                st.session_state.onboarding_step = 2
                st.rerun()
            else:
                for error in validation["errors"]:
                    st.error(error)
                for warning in validation["warnings"]:
                    st.warning(warning)
    
    # Step 2: 데이터 소스 연결
    elif st.session_state.onboarding_step == 2:
        st.markdown("### Step 2: 데이터 소스 연결 (3분)")
        st.info("좋아요! 이제 상황을 파악하기 위해 서비스를 연결해주세요.")
        st.caption("💡 모든 연결은 읽기 전용으로 시작합니다.")
        
        selected_sources = []
        
        for category, sources in template["data_source_options"].items():
            st.markdown(f"**[{category}]**")
            for source in sources:
                if st.checkbox(
                    f"☐ {source['name']} - {source['description']}",
                    key=f"source_{source['name']}"
                ):
                    selected_sources.append(source['name'])
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("이전 단계", use_container_width=True):
                st.session_state.onboarding_step = 1
                st.rerun()
        with col2:
            if st.button("다음 단계", type="primary", use_container_width=True):
                # 검증
                validation = validate_onboarding_data(
                    st.session_state.onboarding_goals, selected_sources
                )
                
                if validation["valid"] or len(validation["warnings"]) > 0:
                    st.session_state.onboarding_sources = selected_sources
                    st.session_state.onboarding_step = 3
                    st.rerun()
                else:
                    for error in validation["errors"]:
                        st.error(error)
                    for warning in validation["warnings"]:
                        st.warning(warning)
    
    # Step 3: 선호 설정
    elif st.session_state.onboarding_step == 3:
        st.markdown("### Step 3: 선호 설정 (1분)")
        
        # 세션 상태 초기화 (이전 값이 있으면 사용)
        if "onboarding_intervention" not in st.session_state:
            st.session_state.onboarding_intervention = "moderate"
        if "onboarding_automation" not in st.session_state:
            st.session_state.onboarding_automation = "proposal_only"
        
        st.markdown("**개입 빈도:**")
        intervention_frequency = st.radio(
            "개입 빈도 선택",
            options=[opt["value"] for opt in template["intervention_frequency_options"]],
            format_func=lambda x: next(
                opt["label"] for opt in template["intervention_frequency_options"]
                if opt["value"] == x
            ),
            index=[opt["value"] for opt in template["intervention_frequency_options"]].index(
                st.session_state.onboarding_intervention
            ) if st.session_state.onboarding_intervention in [opt["value"] for opt in template["intervention_frequency_options"]] else 1,
            key="onboarding_intervention_radio"
        )
        
        st.markdown("**자동화 수준:**")
        automation_level = st.radio(
            "자동화 수준 선택",
            options=[opt["value"] for opt in template["automation_level_options"]],
            format_func=lambda x: next(
                opt["label"] for opt in template["automation_level_options"]
                if opt["value"] == x
            ),
            index=[opt["value"] for opt in template["automation_level_options"]].index(
                st.session_state.onboarding_automation
            ) if st.session_state.onboarding_automation in [opt["value"] for opt in template["automation_level_options"]] else 0,
            key="onboarding_automation_radio"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("이전 단계", use_container_width=True):
                st.session_state.onboarding_step = 2
                st.rerun()
        with col2:
            if st.button("완료", type="primary", use_container_width=True):
                # 위젯의 반환값을 세션 상태에 저장
                st.session_state.onboarding_intervention = intervention_frequency
                st.session_state.onboarding_automation = automation_level
                st.session_state.onboarding_step = 4
                st.rerun()
    
    # Step 4: 관찰 시작
    elif st.session_state.onboarding_step == 4:
        st.markdown("### Step 4: 관찰 시작")
        
        # World Model 생성
        with st.spinner("World Model 생성 중..."):
            world_model = create_onboarding_data(
                abstract_goals=st.session_state.onboarding_goals,
                connected_sources=st.session_state.onboarding_sources,
                intervention_frequency=st.session_state.onboarding_intervention,
                automation_level=st.session_state.onboarding_automation
            )
            
            # 저장
            save_world_model(world_model)
            st.session_state.world_model = world_model
        
        st.success("✅ 온보딩이 완료되었습니다!")
        
        # 2-4주 관찰 기간 설명 (시각적으로)
        st.markdown("---")
        st.markdown("### 📊 SIA 관찰 프로세스")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("""
            **실제 운영 시 SIA는 다음과 같이 동작합니다:**
            
            #### 🔍 관찰 단계 (1-2주)
            - 연결된 데이터 소스에서 **읽기 전용**으로 데이터를 수집합니다
            - 메타데이터 중심으로 패턴을 분석합니다 (본문은 저장하지 않음)
            - **개인 베이스라인**을 계산합니다 (과거 2-4주 평균)
            
            #### 📈 베이스라인 계산
            - **1주차**: 도메인 기본값으로 탐지 시작
            - **2주차**: 개인 베이스라인 계산 완료
            - **3주차~**: 개인화된 Problem Score 적용
            
            #### 💡 문제 발견 및 제안
            - 베이스라인과 현재 상태를 비교하여 Gap 발견
            - Problem Score가 임계값을 넘으면 문제 후보로 등록
            - 사용자에게 제안 및 승인 요청
            """)
        
        with col2:
            st.markdown("""
            #### 타임라인
            ```
            Day 1-7:   🔍 관찰 시작
                       └─ 기본 규칙으로 탐지
            
            Day 8-14:  📊 베이스라인 계산
                       └─ 개인 패턴 학습
            
            Day 15+:   💡 문제 발견
                       └─ 제안 및 승인
            ```
            """)
        
        # 시각적 타임라인
        st.markdown("---")
        st.markdown("#### 관찰 기간 시뮬레이션")
        
        timeline_cols = st.columns(4)
        with timeline_cols[0]:
            st.markdown("**1주차**")
            st.caption("🔍 관찰 시작")
            st.caption("기본 규칙 탐지")
        with timeline_cols[1]:
            st.markdown("**2주차**")
            st.caption("📊 데이터 축적")
            st.caption("패턴 분석")
        with timeline_cols[2]:
            st.markdown("**3주차**")
            st.caption("📈 베이스라인 계산")
            st.caption("개인화 시작")
        with timeline_cols[3]:
            st.markdown("**4주차+**")
            st.caption("💡 문제 발견")
            st.caption("제안 생성")
        
        # 베이스라인 계산 설명
        st.markdown("---")
        with st.expander("📚 개인 베이스라인 우선 원칙 (자세히)", expanded=False):
            st.markdown("""
            **SIA의 핵심 원칙: 외부 평균이 아닌 개인 베이스라인을 우선합니다**
            
            #### 왜 개인 베이스라인인가?
            - 사람마다 업무 패턴이 다릅니다
            - 예: A는 평소 메일 응답 시간이 1시간, B는 4시간
            - 외부 평균(예: 2시간)을 기준으로 하면 둘 다 문제로 보일 수 있음
            
            #### 베이스라인 계산 방법
            1. **과거 2-4주 데이터 수집**
               - 이메일: 평균 응답 시간, 중요 메일 비율
               - GitHub: 평균 PR 리뷰 시간, 리뷰 패턴
               - 건강: 평균 수면 시간, 활동량
               
            2. **개인 패턴 학습**
               - 요일별 패턴 (월요일 vs 금요일)
               - 시간대별 패턴 (오전 vs 오후)
               - 맥락별 패턴 (마감일, 휴가 등)
            
            3. **Problem Score 계산에 반영**
               - 현재 값 vs 개인 베이스라인 비교
               - 베이스라인 대비 50% 이상 차이면 높은 점수
               - 베이스라인 대비 20% 이하 차이면 낮은 점수
            """)
        
        st.markdown("---")
        st.markdown("### 🎯 데모 모드")
        
        st.info("""
        **지금은 데모 모드입니다:**
        
        - 실제 2-4주 관찰은 시간이 오래 걸리므로, **샘플 데이터를 사용**하여 즉시 데모를 실행합니다
        - 샘플 데이터는 **이미 2-4주 관찰이 완료된 상태**로 가정합니다
        - 베이스라인 계산 로직은 구현되어 있으며, 실제 데이터가 있으면 자동으로 계산됩니다
        
        **아래 버튼을 클릭하면:**
        1. 샘플 데이터로 현재 상태 수집 (Sensor Layer)
        2. 개인 베이스라인 계산 (과거 데이터 기반)
        3. 기대 상태 생성 (Expectation Layer)
        4. Gap 발견 및 문제 해석 (Comparison → Interpretation)
        5. 솔루션 탐색 및 제안 (Exploration → Proposal)
        6. 에이전트 구성 및 실행 (Composition → Execution)
        7. 학습 및 World Model 업데이트 (Learning Layer)
        """)
        
        # 전체 플로우 실행 버튼
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 전체 플로우 실행하기", type="primary", use_container_width=True):
                # 홈 페이지로 이동하고 전체 플로우 실행
                st.session_state.run_full_flow_after_onboarding = True
                # 페이지를 "홈"으로 변경
                st.session_state.page = "홈"
                st.rerun()
        
        with col2:
            if st.button("나중에 실행", use_container_width=True):
                st.info("💡 [SIA 상태: 관찰 중 🔍]")
                st.caption("홈 화면에서 'SIA 전체 플로우 실행' 버튼을 눌러 언제든지 실행할 수 있습니다.")
        
        # 요약 표시
        st.markdown("---")
        st.markdown("### 설정 요약")
        
        st.markdown("### 설정 요약")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**목표**: {len(st.session_state.onboarding_goals)}개")
            for goal in st.session_state.onboarding_goals:
                st.caption(f"  • {goal}")
        with col2:
            st.markdown(f"**연결된 소스**: {len(st.session_state.onboarding_sources)}개")
            for source in st.session_state.onboarding_sources:
                st.caption(f"  • {source}")
        
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**개입 빈도**: {st.session_state.onboarding_intervention}")
        with col2:
            st.markdown(f"**자동화 수준**: {st.session_state.onboarding_automation}")
        
        if st.button("홈으로 돌아가기", type="primary", use_container_width=True):
            st.session_state.onboarding_step = 1
            st.rerun()

elif page == "World Model":
    st.title("🌍 World Model")
    st.markdown("---")
    
    world_model_path = Path("data/world_model.json")
    if world_model_path.exists():
        with open(world_model_path, "r", encoding="utf-8") as f:
            world_model = json.load(f)
        
        st.session_state.world_model = world_model
        
        # Abstract Goals (v3.2)
        st.markdown("### 추상적 목표 (Abstract Goals)")
        abstract_goals = world_model.get("abstract_goals", [])
        if abstract_goals:
            for goal in abstract_goals:
                with st.expander(f"🎯 {goal.get('text', '')}"):
                    st.json(goal)
        else:
            st.info("추상적 목표가 설정되지 않았습니다. 온보딩 페이지에서 설정하세요.")
        
        # Preferences
        st.markdown("### 선호 (Preferences)")
        st.json(world_model.get("preferences", {}))
        
        # Problem Candidates (v3.2)
        st.markdown("### 문제 후보 (Problem Candidates)")
        problem_candidates = world_model.get("problem_candidates", [])
        if problem_candidates:
            for candidate in problem_candidates:
                status_icon = {
                    "candidate": "🔍",
                    "proposed": "💡",
                    "confirmed": "✅",
                    "rejected": "❌",
                    "snoozed": "⏸️"
                }.get(candidate.get("status", "candidate"), "❓")
                with st.expander(f"{status_icon} {candidate.get('description', '')} (점수: {candidate.get('problem_score', 0):.2f})"):
                    st.json(candidate)
        else:
            st.info("문제 후보가 없습니다.")
        
        # Confirmed Problems (v3.2)
        st.markdown("### 확정 문제 (Confirmed Problems)")
        confirmed_problems = world_model.get("confirmed_problems", [])
        if confirmed_problems:
            for problem in confirmed_problems:
                with st.expander(f"🚨 {problem.get('name', '')}"):
                    st.json(problem)
        else:
            st.info("확정된 문제가 없습니다.")
        
        # Active Agents (v3.2)
        st.markdown("### 활성 에이전트 (Active Agents)")
        active_agents = world_model.get("active_agents", [])
        if active_agents:
            for agent in active_agents:
                with st.expander(f"🤖 {agent.get('solution_name', 'N/A')}"):
                    st.json(agent)
        else:
            st.info("활성 에이전트가 없습니다.")
        
        # Connected Sources (v3.2)
        st.markdown("### 연결된 소스 (Connected Sources)")
        connected_sources = world_model.get("connected_sources", [])
        if connected_sources:
            for source in connected_sources:
                status_icon = "✅" if source.get("status") == "active" else "❌"
                with st.expander(f"{status_icon} {source.get('name', 'N/A')}"):
                    st.json(source)
        else:
            st.info("연결된 소스가 없습니다.")
        
        # Patterns (레거시 호환)
        st.markdown("### 패턴 (Patterns)")
        patterns = world_model.get("patterns", [])
        if patterns:
            for pattern in patterns:
                with st.expander(f"📊 {pattern.get('behavior', '')}"):
                    st.json(pattern)
        else:
            st.info("패턴이 없습니다.")
        
        # Ideal States (레거시 호환)
        st.markdown("### 이상적 상태 (Ideal States)")
        ideal_states = world_model.get("ideal_states", [])
        if ideal_states:
            for ideal in ideal_states:
                with st.expander(f"✨ {ideal.get('description', '')}"):
                    st.json(ideal)
        else:
            st.info("이상적 상태가 설정되지 않았습니다.")
    else:
        st.error("World Model 파일을 찾을 수 없습니다.")

elif page == "Sensor Layer":
    st.title("👁️ Sensor Layer")
    st.markdown("---")
    st.markdown("외부 데이터 소스에서 현재 상태를 수집하는 계층")
    
    from layers.sensor import get_current_state
    from layers.expectation import load_world_model
    
    # World Model에서 연결된 소스 확인
    world_model = load_world_model()
    connected_sources = world_model.get("connected_sources", [])
    
    if not connected_sources:
        st.warning("⚠️ 연결된 데이터 소스가 없습니다.")
        st.info("💡 온보딩 페이지에서 데이터 소스를 연결하세요.")
    else:
        st.markdown("### 연결된 데이터 소스")
        source_names = [s.get("name", "") for s in connected_sources if s.get("status") == "active"]
        
        # 소스별 도메인 매핑 (이메일만 지원)
        source_to_domain = {
            "Gmail": "email",
            "GitHub": "github",
            "Apple Health": "health"
        }
        
        # 연결된 소스 표시
        for source in connected_sources:
            if source.get("status") == "active":
                st.success(f"✅ {source.get('name', 'N/A')} - {source.get('type', 'N/A')}")
        
        st.markdown("---")
        
        # 수집할 도메인 결정 (모든 활성 도메인에서 수집)
        available_domains = []
        for source_name in source_names:
            domain = source_to_domain.get(source_name)
            if domain and domain not in available_domains:
                available_domains.append(domain)
        
        if not available_domains:
            st.error("❌ 지원하는 도메인을 찾을 수 없습니다.")
            st.info("온보딩에서 데이터 소스를 연결해주세요.")
            st.stop()
        
        # 여러 도메인이 있으면 모두 수집 (Sensor Layer는 조합)
        if len(available_domains) > 1:
            st.info(f"💡 {len(available_domains)}개의 도메인에서 데이터를 수집합니다: {', '.join(available_domains)}")
            st.info("Sensor Layer는 모든 활성 도메인의 데이터를 조합해서 수집합니다.")
        
        # 데이터 수집 버튼
        if st.button("📥 모든 활성 도메인 데이터 수집", type="primary"):
            with st.spinner(f"데이터 수집 중... ({', '.join(available_domains)})"):
                from layers.sensor import get_current_state
                current_state = get_current_state(domains=available_domains, world_model=world_model)
                st.session_state.current_state = current_state
                st.success(f"✅ {len(available_domains)}개 도메인 데이터 수집 완료!")
        
        # 수집된 데이터 표시
        if st.session_state.get("current_state"):
            current_state = st.session_state.current_state
            st.markdown("### 수집된 데이터")
            
            data = current_state.get("data", {})
            domains_in_data = current_state.get("domains", [current_state.get("domain", "unknown")])
            
            if len(domains_in_data) > 1:
                st.info(f"🔀 조합된 데이터: {', '.join(domains_in_data)}")
            
            # 도메인별 데이터 표시
            if "emails" in data:
                st.markdown("#### 📧 이메일 데이터")
                st.metric("총 이메일", data.get("total_emails", 0))
                st.metric("읽지 않음", data.get("unread_count", 0))
                with st.expander("이메일 목록 보기"):
                    st.json(data.get("emails", [])[:5])  # 처음 5개만
            
            if "prs" in data:
                st.markdown("#### 🔀 GitHub PR 데이터")
                st.metric("총 PR", data.get("total_prs", 0))
                st.metric("리뷰 대기", data.get("pending_reviews", 0))
                with st.expander("PR 목록 보기"):
                    st.json(data.get("prs", [])[:5])  # 처음 5개만
            
            if "health_records" in data:
                st.markdown("#### 💚 건강 데이터")
                st.metric("총 기록", data.get("total_health_records", 0))
                st.metric("평균 수면 시간", f"{data.get('average_sleep_hours', 0):.1f}시간")
                with st.expander("건강 기록 보기"):
                    st.json(data.get("health_records", [])[:5])  # 처음 5개만
            
            if "transactions" in data:
                st.markdown("#### 💰 재정 데이터")
                st.metric("총 거래", data.get("total_transactions", 0))
                st.metric("총 지출", f"{data.get('total_spending', 0):,}원")
                with st.expander("거래 내역 보기"):
                    st.json(data.get("transactions", [])[:5])  # 처음 5개만
        
        # 개별 도메인 선택 (하위 호환성)
        st.markdown("---")
        st.markdown("### 개별 도메인 선택 (선택사항)")
        selected_domain = st.selectbox(
            "수집할 도메인 선택",
            options=available_domains,
            index=0,
            help="온보딩에서 연결한 소스에 따라 사용 가능한 도메인이 표시됩니다."
        )
        
        if st.button("현재 상태 수집", type="primary", use_container_width=True):
            try:
                domain_display_names = {
                    "email": "이메일",
                    "github": "GitHub",
                    "health": "건강",
                    "finance": "재정",
                    "calendar": "캘린더"
                }
                display_name = domain_display_names.get(selected_domain, selected_domain)
                
                with st.spinner(f"{display_name} 데이터를 수집하는 중..."):
                    current_state = get_current_state(domain=selected_domain)
                    st.session_state.current_state = current_state
                    
                    # 원본 데이터 저장 (이메일인 경우만)
                    if selected_domain == "email":
                        st.session_state.original_emails = current_state.get("data", {}).get("emails", [])
                
                # 도메인별 성공 메시지
                if selected_domain == "email":
                    email_count = current_state.get("data", {}).get("total_emails", 0)
                    st.success(f"✅ {email_count}개의 이메일을 수집했습니다.")
                elif selected_domain == "github":
                    pr_count = current_state.get("data", {}).get("total_prs", 0)
                    st.success(f"✅ {pr_count}개의 PR을 수집했습니다.")
                elif selected_domain == "health":
                    record_count = current_state.get("data", {}).get("total_records", 0)
                    st.success(f"✅ {record_count}개의 건강 데이터를 수집했습니다.")
                elif selected_domain == "finance":
                    txn_count = current_state.get("data", {}).get("total_transactions", 0)
                    st.success(f"✅ {txn_count}개의 거래 내역을 수집했습니다.")
                else:
                    st.success(f"✅ {selected_domain} 도메인 데이터를 수집했습니다.")
                
                st.markdown("### 수집된 데이터 요약")
                data = current_state.get("data", {})
                
                # 도메인별 요약 표시
                if selected_domain == "email":
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 이메일", data.get("total_emails", 0))
                    with col2:
                        st.metric("미확인", data.get("unread_count", 0))
                    with col3:
                        st.metric("도메인", selected_domain)
                    
                    st.markdown("### 이메일 목록 (최대 10개)")
                    emails = data.get("emails", [])[:10]
                    for email in emails:
                        with st.expander(f"📧 {email.get('subject', 'N/A')}"):
                            st.markdown(f"**발신자**: {email.get('sender', 'N/A')}")
                            st.markdown(f"**수신 시간**: {email.get('received_at', 'N/A')}")
                            st.markdown(f"**우선순위**: {email.get('hidden_priority', 'N/A')}")
                            st.markdown(f"**본문**: {email.get('body', 'N/A')[:100]}...")
                
                elif selected_domain == "github":
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("총 PR", data.get("total_prs", 0))
                    with col2:
                        st.metric("리뷰 대기", data.get("pending_reviews", 0))
                    with col3:
                        st.metric("오래된 PR", data.get("old_prs", 0))
                    
                    st.markdown("### PR 목록")
                    prs = data.get("prs", [])
                    for pr in prs:
                        with st.expander(f"🔀 {pr.get('title', 'N/A')} (나이: {pr.get('age_hours', 0)}시간)"):
                            st.markdown(f"**작성자**: {pr.get('author', 'N/A')}")
                            st.markdown(f"**상태**: {pr.get('status', 'N/A')}")
                            st.markdown(f"**리뷰 상태**: {pr.get('review_status', 'N/A')}")
                            st.json(pr)
                
                elif selected_domain == "health":
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("기록 수", data.get("total_records", 0))
                    with col2:
                        st.metric("평균 수면", f"{data.get('average_sleep_hours', 0):.1f}시간")
                    with col3:
                        st.metric("평균 걸음", f"{data.get('average_steps', 0):.0f}걸음")
                    
                    st.markdown("### 건강 데이터")
                    records = data.get("records", [])
                    for record in records:
                        with st.expander(f"📊 {record.get('date', 'N/A')}"):
                            st.json(record)
                
                elif selected_domain == "finance":
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("총 거래", data.get("total_transactions", 0))
                    with col2:
                        st.metric("총 지출", f"{data.get('total_spending', 0):,}원")
                    
                    st.markdown("### 카테고리별 지출")
                    category_spending = data.get("category_spending", {})
                    for category, amount in category_spending.items():
                        st.info(f"**{category}**: {amount:,}원")
                    
                    st.markdown("### 거래 내역")
                    transactions = data.get("transactions", [])
                    for txn in transactions:
                        with st.expander(f"💰 {txn.get('category', 'N/A')} - {txn.get('amount', 0):,}원"):
                            st.json(txn)
                
                # 전체 데이터 JSON 표시 (접을 수 있게)
                with st.expander("📋 전체 데이터 (JSON)"):
                    st.json(current_state)
                    
            except Exception as e:
                st.error(f"오류 발생: {str(e)}")
                st.exception(e)

elif page == "Expectation Layer":
    st.title("🎯 Expectation Layer")
    st.markdown("---")
    st.markdown("World Model을 기반으로 이상적인 상태를 생성하는 계층")
    
    from layers.expectation import generate_expectation
    from utils.domain_helper import get_active_domain
    
    if st.button("기대 상태 생성"):
        if not client:
            st.warning("⚠️ Anthropic API 키가 설정되지 않았습니다. Claude API를 사용하려면 .env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
            st.info("API 키 없이도 기본 로직으로 작동하지만, Claude API를 사용하면 더 정확한 결과를 얻을 수 있습니다.")
        
        try:
            with st.spinner("기대 상태를 생성하는 중..."):
                from layers.expectation import load_world_model
                world_model = load_world_model()
                
                # 도메인 결정: 일관된 도메인 사용
                domain = get_active_domain(
                    world_model=world_model,
                    current_state=st.session_state.get("current_state"),
                    session_state=st.session_state
                )
                
                st.caption(f"💡 사용 중인 도메인: {domain}")
                
                # current_state가 있으면 그것의 도메인과 일치하는지 확인
                if st.session_state.current_state:
                    current_domain = st.session_state.current_state.get("domain")
                    if current_domain and current_domain != domain:
                        st.warning(f"⚠️ 현재 상태의 도메인({current_domain})과 온보딩 도메인({domain})이 다릅니다. 온보딩 도메인을 사용합니다.")
                
                expectation = generate_expectation(
                    world_model=world_model,
                    domain=domain,
                    anthropic_client=client
                )
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
    from utils.domain_helper import get_active_domain
    
    if st.button("상태 비교"):
        from layers.expectation import load_world_model
        world_model = load_world_model()
        
        # 도메인 결정: 일관된 도메인 사용
        domain = get_active_domain(
            world_model=world_model,
            current_state=st.session_state.get("current_state"),
            session_state=st.session_state
        )
        
        if st.session_state.current_state is None:
            from layers.sensor import get_current_state
            st.session_state.current_state = get_current_state(domain=domain, world_model=world_model)
        
        if st.session_state.expectation is None:
            from layers.expectation import generate_expectation
            st.session_state.expectation = generate_expectation(
                world_model=world_model,
                domain=domain,
                anthropic_client=client
            )
        
        st.caption(f"💡 사용 중인 도메인: {domain}")
        
        if not client:
            st.warning("⚠️ Anthropic API 키가 설정되지 않았습니다. Claude API를 사용하려면 .env 파일에 ANTHROPIC_API_KEY를 설정하세요.")
            st.info("API 키 없이도 기본 로직으로 작동하지만, Claude API를 사용하면 더 정확한 Gap 분석을 얻을 수 있습니다.")
        
        try:
            with st.spinner("상태를 비교하는 중..."):
                # World Model 로드
                from layers.expectation import load_world_model
                world_model = load_world_model()
                
                gaps = compare_states(
                    st.session_state.current_state, 
                    st.session_state.expectation,
                    anthropic_client=client,
                    world_model=world_model
                )
                st.session_state.gaps = gaps
            
            st.success(f"{len(gaps)}개의 Gap을 발견했습니다.")
            
            for gap in gaps:
                problem_score = gap.get("problem_score", 0)
                with st.expander(f"⚠️ {gap.get('description', '')} (심각도: {gap.get('severity', 'N/A')}, Problem Score: {problem_score:.2f})"):
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
                    # 문제 상태 표시
                    status = problem.get("status", "unknown")
                    status_icons = {
                        "candidate": "🔍",
                        "proposed": "💡",
                        "confirmed": "✅",
                        "rejected": "❌",
                        "snoozed": "⏸️"
                    }
                    status_icon = status_icons.get(status, "❓")
                    
                    with st.expander(f"{status_icon} {problem.get('name', '')} (상태: {status}, 점수: {problem.get('problem_score', 0):.2f})"):
                        st.markdown(f"**설명**: {problem.get('description', '')}")
                        st.markdown(f"**원인**: {problem.get('cause', '')}")
                        st.markdown(f"**영향**: {problem.get('impact', '')}")
                        st.markdown(f"**도메인**: {problem.get('domain', 'N/A')}")
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
            from utils.problem_state_machine import ProblemStateMachine
            from layers.expectation import load_world_model
            from layers.crosscutting.observability import log_proposal_decision
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("승인", key="approve_btn", type="primary", use_container_width=True):
                    # 문제를 Confirmed 상태로 전이
                    problem = proposal["problem"]
                    try:
                        problem = ProblemStateMachine.confirm_problem(problem)
                        
                        # World Model에 추가
                        world_model = load_world_model()
                        if "confirmed_problems" not in world_model:
                            world_model["confirmed_problems"] = []
                        world_model["confirmed_problems"].append(problem)
                        
                        # World Model 저장
                        world_model_path = Path("data/world_model.json")
                        with open(world_model_path, "w", encoding="utf-8") as f:
                            json.dump(world_model, f, ensure_ascii=False, indent=2)
                        
                        # Observability 로깅
                        log_proposal_decision(problem, proposal, "approve")
                        
                        st.session_state.proposal["status"] = "approved"
                        st.session_state.proposal["problem"] = problem
                        st.session_state.problems = [problem]
                        st.rerun()
                    except Exception as e:
                        st.error(f"승인 처리 중 오류: {str(e)}")
            with col2:
                if st.button("다른 방안", key="alternative_btn", use_container_width=True):
                    st.info("다른 솔루션을 탐색합니다...")
                    st.session_state.proposal = None
                    st.rerun()
            with col3:
                reject_reason = st.text_input("거절 사유 (선택사항)", key="reject_reason")
                if st.button("거절", key="reject_btn", use_container_width=True):
                    # 문제를 Rejected 상태로 전이
                    problem = proposal["problem"]
                    try:
                        problem = ProblemStateMachine.reject_problem(problem, reason=reject_reason)
                        
                        # Observability 로깅
                        log_proposal_decision(problem, proposal, "reject", reason=reject_reason)
                        
                        st.session_state.proposal["status"] = "rejected"
                        st.session_state.proposal["problem"] = problem
                        if reject_reason:
                            st.info(f"거절 사유가 기록되었습니다: {reject_reason}")
                        st.rerun()
                    except Exception as e:
                        st.error(f"거절 처리 중 오류: {str(e)}")
            with col4:
                if st.button("보류", key="snooze_btn", use_container_width=True):
                    # 문제를 Snoozed 상태로 전이
                    problem = proposal["problem"]
                    try:
                        problem = ProblemStateMachine.snooze_problem(problem, days=7)
                        
                        # Observability 로깅
                        log_proposal_decision(problem, proposal, "snooze")
                        
                        st.session_state.proposal["status"] = "snoozed"
                        st.session_state.proposal["problem"] = problem
                        st.info("7일 후 다시 제안됩니다.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"보류 처리 중 오류: {str(e)}")
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
                    from layers.expectation import load_world_model
                    world_model = load_world_model()
                    
                    solution = st.session_state.proposal["recommended_solution"]
                    problem = st.session_state.problems[0] if st.session_state.problems else None
                    agent_config = compose_agent(
                        solution,
                        problem=problem,
                        world_model=world_model
                    )
                    st.session_state.agent_config = agent_config
                
                st.success("에이전트 구성을 완료했습니다.")
                
                st.markdown("### 구성된 에이전트 (v3.2 구조)")
                
                # v3.2 구조 표시
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**기본 정보**")
                    st.json({
                        "id": agent_config.get("id"),
                        "solution_name": agent_config.get("solution_name"),
                        "domain": agent_config.get("domain"),
                        "risk_level": agent_config.get("risk_level")
                    })
                
                with col2:
                    st.markdown("**트리거**")
                    st.json(agent_config.get("trigger", {}))
                
                st.markdown("**입력 (Inputs)**")
                st.json(agent_config.get("inputs", {}))
                
                st.markdown("**도구 (Tools)**")
                tools = agent_config.get("tools", [])
                for tool in tools:
                    with st.expander(f"🔧 {tool.get('name', 'N/A')}"):
                        st.json(tool)
                
                st.markdown("**처리 로직 (Logic)**")
                st.json(agent_config.get("logic", {}))
                
                st.markdown("**실행 액션 (Actions)**")
                actions = agent_config.get("actions", [])
                for action in actions:
                    with st.expander(f"⚡ {action.get('do', 'N/A')}"):
                        st.json(action)
                
                st.markdown("**안전 정책 (Safety)**")
                st.json(agent_config.get("safety", {}))
                
                # 하위 호환성: 워크플로우도 표시
                st.markdown("---")
                st.markdown("### 워크플로우 (레거시)")
                workflow = agent_config.get("workflow", [])
                if workflow:
                    for step in workflow:
                        st.markdown(f"**{step['step']}단계**: {step['action']} (도구: {step['tool']})")
                else:
                    st.info("워크플로우가 없습니다. v3.2 구조의 actions를 사용합니다.")
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
                    from layers.expectation import load_world_model
                    world_model = load_world_model()
                    
                    # 도메인별 입력 데이터 준비
                    input_data = {}
                    domain = st.session_state.agent_config.get("domain")
                    
                    if not domain:
                        st.error("❌ 에이전트에 도메인 정보가 없습니다.")
                        st.info("에이전트를 다시 구성해주세요.")
                        st.stop()
                    
                    if domain == "email" and emails:
                        input_data["emails"] = emails
                    elif domain == "github" and st.session_state.current_state:
                        input_data["prs"] = st.session_state.current_state.get("data", {}).get("prs", [])
                    elif domain == "health" and st.session_state.current_state:
                        input_data["health"] = st.session_state.current_state.get("data", {}).get("records", [])
                    elif domain == "finance" and st.session_state.current_state:
                        input_data["transactions"] = st.session_state.current_state.get("data", {}).get("transactions", [])
                    
                    execution_result = execute_agent(
                        st.session_state.agent_config,
                        input_data=input_data if input_data else None,
                        world_model=world_model
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
                    domain = execution_result.get("domain")
                    if not domain:
                        domain = st.session_state.agent_config.get("domain")
                    if not domain:
                        st.warning("도메인 정보를 확인할 수 없습니다.")
                        domain = "unknown"
                    
                    domain_names = {
                        "email": "처리된 이메일",
                        "github": "처리된 PR",
                        "health": "처리된 기록",
                        "finance": "처리된 거래"
                    }
                    st.metric(domain_names.get(domain, "처리된 항목"), summary.get("processed_count", 0))
                
                # Before/After 비교 (도메인별)
                domain = execution_result.get("domain")
                if not domain:
                    domain = st.session_state.agent_config.get("domain")
                
                if domain == "email" and st.session_state.original_emails and execution_result.get("processed_emails"):
                    st.markdown("---")
                    st.markdown("### 📊 Before/After 비교 (이메일)")
                    
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
                elif domain == "github" and execution_result.get("processed_prs"):
                    st.markdown("---")
                    st.markdown("### 📊 처리된 PR")
                    prs = execution_result["processed_prs"][:10]
                    for pr in prs:
                        with st.expander(f"🔀 {pr.get('title', 'N/A')}"):
                            st.json(pr)
                elif domain == "health" and execution_result.get("processed_records"):
                    st.markdown("---")
                    st.markdown("### 📊 처리된 건강 데이터")
                    records = execution_result["processed_records"][:10]
                    for record in records:
                        with st.expander(f"📊 {record.get('date', 'N/A')}"):
                            st.json(record)
                elif domain == "finance" and execution_result.get("processed_transactions"):
                    st.markdown("---")
                    st.markdown("### 📊 처리된 거래 내역")
                    transactions = execution_result["processed_transactions"][:10]
                    for txn in transactions:
                        with st.expander(f"💰 {txn.get('category', 'N/A')} - {txn.get('amount', 0):,}원"):
                            st.json(txn)
                
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
                            updated_model = update_world_model(
                                analysis,
                                execution_result=st.session_state.execution_result
                            )
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
    
    # 에이전트 도메인 확인
    agent_domain = st.session_state.agent_config.get("domain")
    
    if not agent_domain:
        st.error("❌ 에이전트에 도메인 정보가 없습니다.")
        st.info("에이전트를 다시 구성해주세요.")
        st.stop()
    
    # 도메인별 설명
    domain_descriptions = {
        "email": "SIA로 생성된 에이전트가 실시간으로 이메일을 분류하는 과정을 확인하세요.",
        "github": "SIA로 생성된 에이전트가 실시간으로 PR을 리뷰하는 과정을 확인하세요.",
        "health": "SIA로 생성된 에이전트가 실시간으로 건강 데이터를 분석하는 과정을 확인하세요.",
        "finance": "SIA로 생성된 에이전트가 실시간으로 거래를 분석하는 과정을 확인하세요."
    }
    st.markdown(domain_descriptions.get(agent_domain, "에이전트가 실시간으로 데이터를 처리하는 과정을 확인하세요."))
    
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
    
    # 에이전트 정보 표시 (v3.2 구조)
    st.markdown("### 현재 활성화된 에이전트")
    
    agent_config = st.session_state.agent_config
    
    # v3.2 구조 정보 표시
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**에이전트 이름**: {agent_config.get('solution_name', 'N/A')}")
    with col2:
        st.info(f"**도메인**: {agent_config.get('domain', 'N/A')}")
    with col3:
        st.info(f"**리스크 레벨**: {agent_config.get('risk_level', 'N/A')}")
    
    # 트리거 정보
    trigger = agent_config.get("trigger", {})
    if trigger:
        st.markdown(f"**트리거**: {trigger.get('type', 'N/A')} - {trigger.get('description', 'N/A')}")
    
    # 도구 정보
    tools = agent_config.get("tools", [])
    if tools:
        st.markdown("**도구**: " + ", ".join([t.get("name", "N/A") for t in tools]))
    
    # 처리 로직 정보
    logic = agent_config.get("logic", {})
    if logic:
        rules = logic.get("rules", [])
        if rules:
            st.markdown("**규칙**: " + str(len(rules)) + "개")
        if logic.get("llm", {}).get("enabled"):
            st.markdown("**LLM 사용**: ✅")
    
    # 실행 액션 정보
    actions = agent_config.get("actions", [])
    if actions:
        st.markdown(f"**액션**: {len(actions)}개")
        for action in actions:
            approval_icon = "🔒" if action.get("requires_approval") else "✅"
            st.caption(f"{approval_icon} {action.get('do', 'N/A')}")
    
    # 레거시 워크플로우 (하위 호환성)
    workflow = agent_config.get("workflow", [])
    if workflow:
        st.markdown("---")
        st.markdown("**레거시 워크플로우**:")
    for step in workflow:
        st.markdown(f"- {step.get('action', 'N/A')} → {step.get('tool', 'N/A')}")
    
    st.markdown("---")
    
    # 데모 시작 버튼
    if st.button("데모 시작", type="primary", use_container_width=True):
        # 도메인별 데모 데이터 생성
        if agent_domain == "email":
            demo_data = generate_random_emails(10)
            demo_title = "실시간 이메일 분류 데모"
            demo_description = "에이전트가 이메일을 하나씩 분석하고 분류하는 과정을 확인하세요."
        elif agent_domain == "github":
            # GitHub PR 데모 데이터 생성
            from layers.sensor import load_github_prs
            demo_data = load_github_prs()[:10] if load_github_prs() else []
            demo_title = "실시간 PR 리뷰 데모"
            demo_description = "에이전트가 PR을 하나씩 분석하고 리뷰하는 과정을 확인하세요."
        elif agent_domain == "health":
            # 건강 데이터 데모
            from layers.sensor import load_health_data
            demo_data = load_health_data()[:10] if load_health_data() else []
            demo_title = "실시간 건강 데이터 분석 데모"
            demo_description = "에이전트가 건강 데이터를 하나씩 분석하는 과정을 확인하세요."
        elif agent_domain == "finance":
            # 재정 데이터 데모
            from layers.sensor import load_finance_data
            demo_data = load_finance_data()[:10] if load_finance_data() else []
            demo_title = "실시간 거래 분석 데모"
            demo_description = "에이전트가 거래를 하나씩 분석하는 과정을 확인하세요."
        else:
            demo_data = generate_random_emails(10)
            demo_title = "실시간 데이터 처리 데모"
            demo_description = "에이전트가 데이터를 하나씩 처리하는 과정을 확인하세요."
        
        if not demo_data:
            st.warning(f"{agent_domain} 도메인에 대한 샘플 데이터가 없습니다.")
            st.info("Sensor Layer에서 데이터를 먼저 수집하세요.")
            st.stop()
        
        st.markdown(f"### {demo_title}")
        st.markdown(demo_description)
        
        # 결과 저장용
        results = []
        status_container = st.container()
        
        # 각 항목 처리
        for i, item in enumerate(demo_data):
            with status_container:
                st.markdown(f"---")
                
                # 도메인별 표시
                if agent_domain == "email":
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**새 이메일 도착**: {item.get('subject', 'N/A')}")
                        st.caption(f"발신자: {item.get('sender', 'N/A')} | 수신 시간: {item.get('received_at', 'N/A')[:19]}")
                    
                    with st.status(f"분석 중... ({i+1}/{len(demo_data)})", state="running") as status:
                        time.sleep(0.5)
                        priority = item.get("hidden_priority", "medium")
                        if priority == "high":
                            label = "긴급"
                            priority_display = "High"
                        elif priority == "medium":
                            label = "일반"
                            priority_display = "Medium"
                        else:
                            label = "낮음"
                            priority_display = "Low"
                        
                        result = {
                            "id": item.get("id"),
                            "subject": item.get("subject"),
                            "sender": item.get("sender"),
                            "priority": priority_display,
                            "label": label
                        }
                        results.append(result)
                        status.update(label=f"분석 완료: 우선순위 {priority_display}, 라벨: {label}", state="complete")
                        time.sleep(0.3)
                
                elif agent_domain == "github":
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**새 PR 도착**: {item.get('title', 'N/A')}")
                        st.caption(f"작성자: {item.get('author', 'N/A')} | 나이: {item.get('age_hours', 0)}시간")
                    
                    with st.status(f"리뷰 중... ({i+1}/{len(demo_data)})", state="running") as status:
                        time.sleep(0.5)
                        review_status = "리뷰 필요" if item.get("review_status") == "pending" else "리뷰 완료"
                        result = {
                            "id": item.get("id"),
                            "title": item.get("title"),
                            "author": item.get("author"),
                            "review_status": review_status,
                            "age_hours": item.get("age_hours", 0)
                        }
                        results.append(result)
                        status.update(label=f"리뷰 완료: {review_status}", state="complete")
                        time.sleep(0.3)
                
                elif agent_domain == "health":
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**건강 데이터**: {item.get('date', 'N/A')}")
                        sleep_hours = item.get("sleep", {}).get("duration_hours", 0)
                        steps = item.get("activity", {}).get("steps", 0)
                        st.caption(f"수면: {sleep_hours}시간 | 걸음: {steps}걸음")
                    
                    with st.status(f"분석 중... ({i+1}/{len(demo_data)})", state="running") as status:
                        time.sleep(0.5)
                        status_text = "정상" if sleep_hours >= 7 else "부족"
                        result = {
                            "id": item.get("date", "unknown"),
                            "date": item.get("date"),
                            "sleep_hours": sleep_hours,
                            "steps": steps,
                            "status": status_text
                        }
                        results.append(result)
                        status.update(label=f"분석 완료: 수면 {status_text}", state="complete")
                        time.sleep(0.3)
                
                elif agent_domain == "finance":
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**거래 발생**: {item.get('description', 'N/A')}")
                        st.caption(f"카테고리: {item.get('category', 'N/A')} | 금액: {item.get('amount', 0):,}원")
                    
                    with st.status(f"분석 중... ({i+1}/{len(demo_data)})", state="running") as status:
                        time.sleep(0.5)
                        category = item.get("category", "기타")
                        amount = item.get("amount", 0)
                        result = {
                            "id": item.get("id"),
                            "description": item.get("description"),
                            "category": category,
                            "amount": amount,
                            "date": item.get("date", "N/A")
                        }
                        results.append(result)
                        status.update(label=f"분석 완료: {category} {amount:,}원", state="complete")
                    time.sleep(0.3)
        
        st.markdown("---")
        st.success("데모가 완료되었습니다!")
        
        # 결과 요약
        st.markdown("### 결과 요약")
        
        if agent_domain == "email":
            priority_counts = {"High": 0, "Medium": 0, "Low": 0}
            for result in results:
                priority_counts[result.get("priority", "Medium")] += 1
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("High 우선순위", priority_counts["High"])
            with col2:
                st.metric("Medium 우선순위", priority_counts["Medium"])
            with col3:
                st.metric("Low 우선순위", priority_counts["Low"])
            
            chart_data = pd.DataFrame({
                "우선순위": ["High", "Medium", "Low"],
                "개수": [priority_counts["High"], priority_counts["Medium"], priority_counts["Low"]]
            })
            st.bar_chart(chart_data.set_index("우선순위"))
            
            results_df = pd.DataFrame(results)
            st.dataframe(results_df[["subject", "sender", "priority", "label"]], use_container_width=True, hide_index=True)
        else:
            results_df = pd.DataFrame(results)
            st.dataframe(results_df, use_container_width=True, hide_index=True)
        
        # 세션 상태에 저장
        st.session_state.demo_results = results
