@echo off
setlocal enabledelayedexpansion

:: 헤더 출력 함수
echo ====================== Python 3.11 환경 설정 ======================

:: Python 3.11 설치 확인
where python3.11 >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.11이 설치되어 있지 않습니다.
    echo Python 3.11을 설치한 후 다시 시도해주세요.
    echo Python 3.11 다운로드: https://www.python.org/downloads/
    pause
    exit /b 1
)

:: 가상환경이 없으면 생성
if not exist "venv\" (
    echo [1/5] 가상환경 생성 중...
    python3.11 -m venv venv
    call venv\Scripts\activate.bat
    
    echo [2/5] pip 업그레이드 및 wheel 설치 중...
    python -m pip install --upgrade pip
    pip install wheel
    
    echo [3/5] Python 의존성 설치 중...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

echo.
echo ====================== Docker 설정 ======================
echo [4/5] Docker 이미지 다운로드 중...
docker pull handsonsecurity/seed-ubuntu:large

:: xterm.js 애드온 설치 (Windows에서는 글로벌 설치 대신 로컬로 설치)
echo.
echo ====================== xterm.js 설정 ======================
echo [5/5] xterm.js 애드온 설치 중...
npm install xterm-addon-fit

:: 서버 실행
echo.
echo ====================== 서버 시작 ======================
python run_terminal.py

pause
