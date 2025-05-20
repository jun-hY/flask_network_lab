@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 헤더 출력 함수
echo ====================== Python 3.11 환경 설정 ======================

:: Python 3.11 설치 확인 및 자동 설치
python --version 2>nul | findstr /C:"Python 3.11" >nul
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.11이 설치되어 있지 않습니다.
    echo Python 3.11을 자동으로 설치합니다...
    
    :: winget을 사용하여 Python 3.11 설치
    winget install Python.Python.3.11
    
    :: Python 설치 경로를 PATH에 추가
    set "PYTHON_PATH=%LOCALAPPDATA%\Programs\Python\Python311"
    set "PATH=%PYTHON_PATH%;%PYTHON_PATH%\Scripts;%PATH%"
    
    :: 설치 확인
    python --version 2>nul | findstr /C:"Python 3.11" >nul
    if %ERRORLEVEL% NEQ 0 (
        echo Python 3.11 설치에 실패했습니다. 수동으로 설치해주세요.
        pause
        exit /b 1
    )
    echo Python 3.11이 설치되었습니다.
)

:: 가상환경이 없으면 생성
if not exist "venv\" (
    echo [1/4] 가상환경 생성 중...
    python -m venv venv
    call venv\Scripts\activate.bat
    
    echo [2/4] pip 업그레이드 및 wheel 설치 중...
    python -m pip install --upgrade pip
    pip install wheel
    
    echo [3/4] Python 의존성 설치 중...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
    echo Python 의존성 설치 중...
    pip install -r requirements.txt
)

echo.
echo ====================== Docker 설정 ======================
echo [4/4] Docker 이미지 다운로드 중...
docker pull handsonsecurity/seed-ubuntu:large

:: 서버 실행
echo.
echo ====================== 서버 시작 ======================
python run_terminal.py

pause
