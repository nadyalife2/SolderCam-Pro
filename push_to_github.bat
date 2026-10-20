@echo off
chcp 65001 >nul
echo ========================================================
echo   SolderCam Pro: Отправка проекта на GitHub (nadyalife2)
echo ========================================================
echo.

set "GIT_CMD=C:\Program Files\Microsoft Visual Studio\2022\Enterprise\Common7\IDE\CommonExtensions\Microsoft\TeamFoundation\Team Explorer\Git\cmd\git.exe"

if not exist "%GIT_CMD%" (
    set "GIT_CMD=git"
)

echo [1/3] Проверка статуса локального репозитория...
"%GIT_CMD%" status

echo.
echo [2/3] Текущий remote:
"%GIT_CMD%" remote -v

echo.
echo [3/3] Отправка ветки main на GitHub...
"%GIT_CMD%" push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================================
    echo   [OK] Проект успешно опубликован на GitHub!
    echo   URL: https://github.com/nadyalife2/SolderCam-Pro
    echo ========================================================
) else (
    echo.
    echo ========================================================
    echo   [!] Не удалось отправить.
    echo   Если репозиторий еще не создан на GitHub:
    echo   1. Откройте в браузере: https://github.com/new
    echo   2. Имя репозитория (Repository name): SolderCam-Pro
    echo   3. Сделайте его Public (или Private) и нажмите "Create repository"
    echo   4. Запустите этот файл снова!
    echo ========================================================
)

echo.
pause
