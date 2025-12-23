# SIA MVP

Streamlit과 Anthropic Claude를 사용한 MVP 프로젝트입니다.

## 🚀 시작하기

### 1. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python3 -m venv venv

# 가상환경 활성화 (macOS/Linux)
source venv/bin/activate

# 가상환경 활성화 (Windows)
venv\Scripts\activate
```

### 2. 패키지 설치

```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env.example` 파일을 참고하여 `.env` 파일을 생성하고 Anthropic API 키를 설정하세요:

```bash
cp .env.example .env
```

`.env` 파일에 다음 내용을 추가하세요:
```
ANTHROPIC_API_KEY=your_api_key_here
```

### 4. 애플리케이션 실행

```bash
streamlit run app.py
```

## 📁 프로젝트 구조

```
sia-mvp/
├── app.py              # 메인 애플리케이션
├── requirements.txt    # Python 패키지 의존성
├── .env.example        # 환경 변수 예제
├── .env               # 환경 변수 (git에 포함되지 않음)
├── .gitignore         # Git 무시 파일
└── README.md          # 프로젝트 설명서
```

## 🔧 사용 기술

- **Streamlit**: 웹 애플리케이션 프레임워크
- **Anthropic Claude**: AI 언어 모델
- **python-dotenv**: 환경 변수 관리

## 📝 라이선스

MIT

# SIA
