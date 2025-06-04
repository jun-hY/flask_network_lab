@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo Flask 네트워크 실습실 서버를 시작합니다...

ECHO Python 3.11 버전 확인
%LOCALAPPDATA%\Programs\Python\Python311\python.exe --version 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Python 3.11이 설치되어 있지 않습니다.
    echo [INFO] Python 3.11을 자동으로 설치합니다...
    
    ECHO winget을 사용하여 Python 3.11 설치
    winget install -e --id Python.Python.3.11
    
    ECHO Python 3.11 버전 설치 확인
    %LOCALAPPDATA%\Programs\Python\Python311\python.exe --version >nul 2>&1
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        echo [INFO] Python 3.11이 성공적으로 설치되었습니다.
        echo [INFO] 배치 파일을 다시 실행합니다...
        call "%~f0"
        exit /b
    ) else (
        echo [ERROR] Python 3.11 설치에 실패했습니다. 수동으로 설치해주세요.
        pause
        exit /b 1
    )
)

ECHO 가상환경이 없으면 생성
if not exist venv (
    echo [INFO] 가상환경을 생성합니다...
    %LOCALAPPDATA%\Programs\Python\Python311\python.exe -m venv venv
)

ECHO 가상환경 활성화
call venv\Scripts\activate.bat

ECHO pip 업그레이드
python -m pip install --upgrade pip

ECHO 필요한 패키지 설치
echo [INFO] 필요한 패키지를 설치합니다...
python -m pip install -r requirements.txt

ECHO 서버 실행
echo [INFO] 서버를 시작합니다...
python app.py

ECHO 오류 발생 시 일시 정지
if errorlevel 1 (
    echo [ERROR] 오류가 발생했습니다. 아무 키나 누르면 종료됩니다...
    pause
)