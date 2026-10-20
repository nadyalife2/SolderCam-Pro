@echo off
chcp 65001 >nul
echo ========================================================
echo   SolderCam Pro: Отправка проекта на GitHub
echo ========================================================
echo.

set "GIT_CMD=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe"

if not exist "%GIT_CMD%" (
    set "GIT_CMD=git"
)

echo [1/3] Проверка статуса репозитория...
"%GIT_CMD%" status

echo.
echo [2/3] Настройка remote origin...
rem Если имя репозитория на GitHub отличается, укажите ваш URL ниже:
set /p REPO_URL="Введите URL вашего GitHub репозитория (например, https://github.com/nadyalife2/SolderCam-Pro.git): "

if not "%REPO_URL%"=="" (
    "%GIT_CMD%" remote remove origin 2>nul
    "%GIT_CMD%" remote add origin %REPO_URL%
)

"%GIT_CMD%" remote -v

echo.
echo [3/3] Отправка ветки main на GitHub...
"%GIT_CMD%" push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [OK] Проект успешно опубликован на GitHub!
    echo ========================================================
) else (
    echo.
    echo [!] Ошибка при отправке. Убедитесь, что репозиторий создан на GitHub и авторизован в Git.
)

echo.
pause
