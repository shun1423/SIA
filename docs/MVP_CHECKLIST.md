
SIA MVP 구현 리스트

---

## 1. World Model

### 1.1 데이터 구조 설계

- [ ]  사용자 프로필 스키마 (이름, 역할 등)
- [ ]  Goals 스키마 (목표 텍스트, 우선순위, 생성일)
- [ ]  Preferences 스키마 (알림 빈도, 자동화 수용도 등)
- [ ]  Patterns 스키마 (요일별/시간별 행동 패턴)
- [ ]  Ideal States 스키마 (도메인, 조건, 기준값)

### 1.2 저장소

- [ ]  JSON 파일 기반 저장 (MVP 단계)
- [ ]  읽기/쓰기/업데이트 함수

### 1.3 초기화

- [ ]  온보딩 질문 3~5개 정의
- [ ]  이메일 도메인 기본값 세팅
- [ ]  예시 World Model 데이터 (데모용)

---

## 2. Sensor Layer

### 2.1 가짜 데이터 생성

- [ ]  이메일 샘플 데이터 20~30개
    - 발신자 (상사, 동료, 마케팅, 스팸 등 다양하게)
    - 제목
    - 본문 요약
    - 수신 시간
    - 중요도 (숨겨진 정답)
- [ ]  현재 시간/상황 시뮬레이션 데이터

### 2.2 데이터 로더

- [ ]  JSON에서 이메일 목록 로드
- [ ]  "현재 상태" 구조체로 변환

---

## 3. Expectation Layer

### 3.1 기대 상태 생성 로직

- [ ]  World Model 읽기
- [ ]  현재 맥락 (시간, 요일) 파악
- [ ]  LLM 프롬프트: "이 World Model과 현재 상황에서 이상적 상태는?"
- [ ]  출력 파싱 (구조화된 Expectation 객체)

### 3.2 프롬프트 설계

- [ ]  시스템 프롬프트 작성
- [ ]  출력 포맷 정의 (JSON)

---

## 4. Comparison Layer

### 4.1 비교 로직

- [ ]  현재 상태 입력
- [ ]  기대 상태 입력
- [ ]  LLM 프롬프트: "이 둘을 비교해서 Gap을 찾아줘"
- [ ]  Gap 리스트 출력 (각각 중요도 포함)

### 4.2 Gap 스키마

- [ ]  Gap ID
- [ ]  설명 (텍스트)
- [ ]  중요도 (high/medium/low)
- [ ]  관련 데이터 참조

---

## 5. Interpretation Layer

### 5.1 문제 정의 로직

- [ ]  Gap 입력
- [ ]  LLM 프롬프트: "이 Gap을 문제로 정의하고, 원인과 영향을 분석해줘"
- [ ]  Problem 객체 출력

### 5.2 Problem 스키마

- [ ]  Problem ID
- [ ]  문제 이름 (한 줄)
- [ ]  상세 설명
- [ ]  원인 (Cause)
- [ ]  해결 안 할 경우 영향 (Impact)

---

## 6. Exploration Layer

### 6.1 솔루션 탐색 로직

- [ ]  Problem 입력
- [ ]  LLM 프롬프트: "이 문제를 해결할 수 있는 방법 3가지 제안해줘"
- [ ]  각 솔루션의 장단점, 구현 복잡도 포함

### 6.2 Solution 스키마

- [ ]  Solution ID
- [ ]  이름
- [ ]  설명
- [ ]  장점 리스트
- [ ]  단점 리스트
- [ ]  구현 복잡도 (low/medium/high)
- [ ]  필요한 도구/리소스

---

## 7. Proposal Layer

### 7.1 UI 컴포넌트

- [ ]  문제 요약 카드
- [ ]  솔루션 선택지 3개 표시
- [ ]  각 솔루션 장단점 표시
- [ ]  [승인] [다른 방안] [거절] 버튼

### 7.2 인터랙션

- [ ]  승인 시 → Composition Layer로 전달
- [ ]  거절 시 → 이유 입력받고 World Model 업데이트
- [ ]  다른 방안 시 → Exploration 다시 실행

---

## 8. Composition Layer ⭐ (핵심)

### 8.1 솔루션 → 에이전트 매핑

- [ ]  솔루션 타입별 에이전트 템플릿 정의
    - email_classifier → 분류 에이전트
    - email_prioritizer → 우선순위 에이전트
    - reminder → 리마인더 에이전트

### 8.2 동적 에이전트 생성

- [ ]  솔루션 파라미터 추출 (규칙, 조건 등)
- [ ]  LLM 선택 로직 (MVP에서는 Claude 고정)
- [ ]  도구 선택 로직
    - email_reader (가짜 데이터 읽기)
    - label_applier (라벨 적용 시뮬레이션)
    - priority_scorer (우선순위 점수 계산)
- [ ]  에이전트 빌더 함수

### 8.3 에이전트 구조 (LangGraph 또는 직접 구현)

- [ ]  상태 정의 (State)
- [ ]  노드 정의 (분석 → 판단 → 실행)
- [ ]  엣지 정의 (조건부 분기)

---

## 9. Execution Layer

### 9.1 실행 엔진

- [ ]  생성된 에이전트 실행
- [ ]  각 이메일에 대해 처리
- [ ]  결과 수집

### 9.2 결과 스키마

- [ ]  처리된 이메일 ID
- [ ]  적용된 액션 (라벨, 우선순위 등)
- [ ]  성공/실패 여부

### 9.3 결과 표시 UI

- [ ]  처리 전/후 비교 테이블
- [ ]  변경된 항목 하이라이트

---

## 10. Learning Layer

### 10.1 결과 분석

- [ ]  실행 결과 입력
- [ ]  사용자 피드백 수집 UI ("이 분류가 맞나요?")
- [ ]  정확도 계산

### 10.2 World Model 업데이트

- [ ]  새로운 패턴 추가 로직
- [ ]  기존 Ideal State 조정 로직
- [ ]  변경 사항 저장

### 10.3 업데이트 표시 UI

- [ ]  "World Model이 이렇게 업데이트되었습니다" 표시
- [ ]  Before/After 비교

---

## 11. 전체 UI (Streamlit)

### 11.1 페이지 구성

- [ ]  사이드바: 단계 네비게이션
- [ ]  메인: 현재 단계 콘텐츠

### 11.2 화면별

- [ ]  홈: SIA 소개 + 시작 버튼
- [ ]  World Model 설정/확인
- [ ]  현재 상태 표시 (이메일 목록)
- [ ]  Gap Detection 결과
- [ ]  솔루션 제안 + 선택
- [ ]  에이전트 생성 과정 시각화
- [ ]  실행 결과
- [ ]  학습 결과 + World Model 변화

### 11.3 공통 컴포넌트

- [ ]  진행 상태 표시 (10계층 중 어디인지)
- [ ]  로딩 인디케이터
- [ ]  에러 처리

---

## 12. 기술 인프라

### 12.1 프로젝트 구조

```
sia-mvp/
├── app.py (Streamlit 메인)
├── world_model/
├── layers/
│   ├── sensor.py
│   ├── expectation.py
│   ├── comparison.py
│   ├── interpretation.py
│   ├── exploration.py
│   ├── proposal.py
│   ├── composition.py
│   ├── execution.py
│   └── learning.py
├── agents/
├── data/
│   ├── sample_emails.json
│   └── world_model.json
├── prompts/
└── utils/

```

### 12.2 환경 설정

- [ ]  requirements.txt
- [ ]  .env (API 키)
- [ ]  [README.md](http://readme.md/)

---

## 우선순위 정리

| 순위 | 항목 | 이유 |
| --- | --- | --- |
| 1 | World Model 데이터 구조 | 전체의 기반 |
| 2 | 가짜 이메일 데이터 | 테스트 대상 |
| 3 | Comparison Layer | Gap 찾는 게 핵심 |
| 4 | Composition Layer | 차별점 |
| 5 | Execution Layer | 실제로 돌아가는 걸 봐야 함 |
| 6 | 나머지 Layer | 위 5개 되면 연결만 |
| 7 | UI 다듬기 | 마지막 |