#!/bin/bash

# SIA MVP 프로젝트 설정 스크립트

echo "🚀 SIA MVP 프로젝트 설정을 시작합니다..."

# 가상환경 생성
echo "📦 Python 가상환경을 생성합니다..."
python3 -m venv venv

# 가상환경 활성화
echo "🔌 가상환경을 활성화합니다..."
source venv/bin/activate

# 패키지 설치
echo "📥 필요한 패키지를 설치합니다..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ 설정이 완료되었습니다!"
echo ""
echo "다음 명령어로 애플리케이션을 실행하세요:"
echo "  source venv/bin/activate"
echo "  streamlit run app.py"

