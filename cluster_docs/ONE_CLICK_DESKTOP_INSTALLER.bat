@echo off
chcp 65001 >nul
title Triad-Omni v4.6 - Автоматический 1-Кнопочный Установщик Узлов Кластера
color 0B

echo ===============================================================================
echo        ⚡ TRIAD-OMNI v4.6: АВТОМАТИЧЕСКАЯ УСТАНОВКА ИИ-УЗЛОВ СМАРТФОНОВ
echo ===============================================================================
echo  Этот скрипт сделает ВСЁ сам за вас:
echo   - Проверит подключение телефона через USB
echo   - Настроит спящий режим Wi-Fi (запретит телефону засыпать)
echo   - Очистит системный мусор (деблоат) для освобождения памяти ОЗУ
echo   - Зальет нужные скрипты автозапуска и запустит сервера
echo ===============================================================================
echo.

:: Проверка наличия adb
where adb >nul 2>nul
if %errorlevel% neq 0 (
    echo [ОШИБКА] ADB не найден в системе! 
    echo Убедитесь, что Android SDK Platform-tools установлены и путь к ним добавлен в PATH.
    pause
    exit /b 1
)

:CHECK_DEVICE
echo [*] Поиск подключенного смартфона по USB...
adb get-state >nul 2>nul
if %errorlevel% neq 0 (
    echo.
    echo [!] Смартфон не обнаружен!
    echo     1. Включите на телефоне "Отладку по USB" (Настройки - Для разработчиков).
    echo     2. Подключите телефон кабелем к ПК.
    echo     3. Подтвердите на экране телефона запрос "Разрешить отладку с этого компьютера".
    echo.
    pause
    goto CHECK_DEVICE
)

for /f "tokens=*" %%i in ('adb shell getprop ro.product.model') do set MODEL=%%i
for /f "tokens=*" %%i in ('adb shell getprop ro.board.platform') do set PLATFORM=%%i
echo [+] Обнаружено устройство: %MODEL% (Платформа: %PLATFORM%)
echo.

echo Выберите, какую роль должен выполнять этот смартфон в кластере:
echo   [1] Главный Мозг (Xiaomi Mi 10T / Snapdragon 865 - 9B STEM + Vision / 7B Coder)
echo   [2] Быстрый Рефлекс (OnePlus Nord N10 - 3B Coder + BGE-M3 RAG Векторы)
echo   [3] Главный Шлюз и Пульт (Redmi Note 4 - Веб-интерфейс, SQLite и Диспетчер)
echo   [4] Выход
echo.
set /p CHOICE="Введите номер роли (1, 2 или 3): "

if "%CHOICE%"=="1" goto SETUP_MI10T
if "%CHOICE%"=="2" goto SETUP_NORD10
if "%CHOICE%"=="3" goto SETUP_NOTE4
if "%CHOICE%"=="4" exit /b 0
goto CHECK_DEVICE

:SETUP_MI10T
echo.
echo [*] Настройка Xiaomi Mi 10T (NODE-1: Главный Мозг)...
adb shell cmd wifi set-wifi-enabled enabled
adb shell settings put global wifi_sleep_policy 2

echo [*] Снятие ограничений Android 15 (Отключение Phantom Process Killer)...
adb shell dumpsys deviceidle whitelist +com.termux +com.termux.boot 2>nul
adb shell settings put global settings_enable_monitor_phantom_procs false 2>nul
adb shell device_config put activity_manager max_phantom_processes 2147483647 2>nul
adb shell cmd appops set com.termux RUN_IN_BACKGROUND allow 2>nul
echo [+] Phantom Process Killer обезврежен (процессы llama-server не будут убиваться).

echo [*] Восстановление прав SELinux для Termux...
adb shell su -c "restorecon -R -F /data/data/com.termux/files" 2>nul
echo [+] Права доступа SELinux восстановлены.

echo [*] Разворачиваем скрипт переключения профилей...
adb shell "mkdir -p /data/data/com.termux/files/home/models /data/data/com.termux/files/home/adapters /data/data/com.termux/files/home/.termux/boot" 2>nul
adb push "%~dp001_Сеть,_Прошивки_и_Вычислительные_Узлы_Mi_10T_+_Nord_N10.md" /sdcard/cluster_spec.md 2>nul
echo [+] Готово! Откройте Termux на телефоне и запустите: ~/reload_brain.sh stem
pause
exit /b 0

:SETUP_NORD10
echo.
echo [*] Настройка OnePlus Nord N10 (NODE-2: Быстрый Рефлекс и Векторы)...
echo [*] Отключение сна Wi-Fi и фонового киллера...
adb shell cmd wifi set-wifi-enabled enabled
adb shell settings put global wifi_sleep_policy 2
adb shell dumpsys deviceidle whitelist +com.termux +com.termux.boot 2>nul
adb shell cmd appops set com.termux RUN_IN_BACKGROUND allow 2>nul

echo [*] Очистка фонового системного мусора OnePlus (освобождение ~900 МБ ОЗУ)...
for %%P in (com.oneplus.brickmode com.oneplus.gamespace net.oneplus.odm net.oneplus.odm.provider com.google.android.music com.google.android.videos com.google.android.youtube) do (
    adb shell pm uninstall -k --user 0 %%P 2>nul
    echo  - Удален: %%P
)
echo [+] Память успешно освобождена!
pause
exit /b 0

:SETUP_NOTE4
echo.
echo [*] Настройка Redmi Note 4 (NODE-3: Оркестратор и Пульт)...
adb shell cmd wifi set-wifi-enabled enabled
adb shell settings put global wifi_sleep_policy 2
adb shell dumpsys deviceidle whitelist +com.termux +com.termux.boot 2>nul
adb shell cmd appops set com.termux RUN_IN_BACKGROUND allow 2>nul
adb shell "mkdir -p /sdcard/OmniCluster_Data/db /sdcard/OmniCluster_Data/datasets" 2>nul
echo [+] Каталоги данных созданы в /sdcard/OmniCluster_Data/
adb push "%~dp0async_omni_gateway.py" /sdcard/omni_gateway.py 2>nul
echo [+] Асинхронный шлюз скопирован. Для запуска откройте Termux и введите:
echo     python /sdcard/omni_gateway.py
pause
exit /b 0
