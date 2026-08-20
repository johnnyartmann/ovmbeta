@echo off
chcp 65001 > nul
title Painel OVM-SC - Observatório da Violência Contra a Mulher

cd /d "%~dp0"

echo =========================================================
echo    OBSERVATÓRIO DA VIOLÊNCIA CONTRA A MULHER - SC
echo           Inicializando o Painel OVM-SC
echo =========================================================
echo.

if exist ".venv\Scripts\activate.bat" call ".venv\Scripts\activate.bat"
if exist "venv\Scripts\activate.bat" call "venv\Scripts\activate.bat"
if exist "env\Scripts\activate.bat" call "env\Scripts\activate.bat"

echo [INFO] Iniciando o servidor Streamlit...
echo [INFO] O painel será aberto automaticamente no seu navegador.
echo [INFO] Para encerrar o sistema, feche esta janela ou pressione Ctrl + C.
echo.

python -m streamlit run painel_observatorio.py

if errorlevel 1 (
    echo.
    echo [AVISO] Tentando com o executável direto do Python...
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe" -m streamlit run painel_observatorio.py
)

if errorlevel 1 (
    echo.
    echo [ERRO] Não foi possível iniciar o Streamlit.
    echo Verifique a instalação do Python e das dependências.
    echo.
    pause
)
