#!/bin/bash

# Print header
print_header() {
    local msg="$1"
    local len=${#msg}
    local width=80
    local pad=$(( (width - len - 2) / 2 ))
    printf '=%.0s' $(seq 1 $pad)
    printf ' %s ' "$msg"
    printf '=%.0s' $(seq 1 $((width - len - pad - 2)))
    echo
}

# Check if Python 3.11 is installed
if ! command -v python3.11 &> /dev/null; then
    print_header "Python 3.11 설치 중..."
    
    # 패키지 캐시 정리 및 소스 목록 업데이트
    sudo rm -rf /var/lib/apt/lists/*
    sudo apt clean
    sudo apt update --fix-missing
    
    # 필요한 도구 설치
    sudo apt install -y software-properties-common
    
    # deadsnakes PPA 추가
    sudo add-apt-repository -y ppa:deadsnakes/ppa
    
    # 패키지 목록 업데이트 (에러 무시)
    sudo apt update || true
    
    # Python 3.11 설치 시도
    sudo apt install -y --allow-unauthenticated \
        python3.11 \
        python3.11-venv \
        python3.11-dev \
        python3.11-distutils
    
    # Python 3.11이 설치되었는지 다시 확인
    if ! command -v python3.11 &> /dev/null; then
        echo -e "\n\033[0;31mPython 3.11 설치에 실패했습니다. 수동으로 설치해 주세요.\033[0m"
        echo "다음 명령어로 시도해 보세요:"
        echo "  sudo add-apt-repository ppa:deadsnakes/ppa"
        echo "  sudo apt update"
        echo "  sudo apt install python3.11 python3.11-venv python3.11-dev"
        echo -e "\n또는 Python 3.11을 직접 다운로드하여 설치할 수 있습니다:"
        echo "  https://www.python.org/downloads/"
        exit 1
    fi
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    print_header "가상환경 생성 중..."
    python3.11 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip and install wheel
    pip install --upgrade pip
    pip install wheel
    
    # Install Python dependencies
    print_header "Python 의존성 설치 중..."
    pip install -r requirements.txt
else
    # Activate existing virtual environment
    source venv/bin/activate
    
    # Install Python dependencies
    print_header "Python 의존성 설치 중..."
    pip install -r requirements.txt
fi

# Install Docker image
print_header "Docker 이미지 다운로드 중..."
docker pull handsonsecurity/seed-ubuntu:large
print_header "Docker 이미지 준비 완료"

# Install xterm.js addons
print_header "xterm.js 애드온 설치 중..."
npm install -g xterm-addon-fit
print_header "xterm.js 애드온 설치 완료"

# Start the server
print_header "서버 시작 중..."
python3.11 run_terminal.py