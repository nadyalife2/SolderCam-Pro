@echo off
chcp 65001 >nul
title OnePlus Nord N10 5G - Комплексная диагностика АКБ
color 0F

set ADB="C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
if not exist %ADB% (
    set ADB=adb
)

%ADB% devices | findstr /R "device$" >nul
if errorlevel 1 (
    echo [!] ОШИБКА: Телефон OnePlus Nord N10 не обнаружен через ADB!
    echo     Проверьте подключение USB кабеля и включена ли отладка.
    echo.
    pause
    exit /b 1
)

:MENU
cls
echo ======================================================================
echo       OnePlus Nord N10 5G (BE2029) - ДИАГНОСТИЧЕСКИЙ КОМПЛЕКС АКБ
echo ======================================================================
echo.
echo  [1] Запустить постоянный мониторинг в реальном времени (V, mA, NTC)
echo  [2] Выполнить стресс-тест CPU для проверки термодатчика NTC на обманку
echo  [3] Проверить состояние отсечки контроллера питания PMIC (SMBLIB/healthd)
echo  [4] Снять полный инженерный отчет подсистемы питания
echo  [0] Выход
echo.
set /p choice="Выберите режим (0-4): "

if "%choice%"=="1" goto MONITOR
if "%choice%"=="2" goto STRESS_NTC
if "%choice%"=="3" goto PMIC_CHECK
if "%choice%"=="4" goto DUMP_FULL
if "%choice%"=="0" exit /b 0
goto MENU

:: ========================================================================
:: РЕЖИМ 1: МОНИТОРИНГ В РЕАЛЬНОМ ВРЕМЕНИ
:: ========================================================================
:MONITOR
cls
echo ======================================================================
echo    РЕЖИМ 1: ПОСТОЯННЫЙ МОНИТОРИНГ (Нажмите Ctrl+C для возврата в меню)
echo ======================================================================
echo Время: %TIME%
echo.

echo --- СТАТУС БАТАРЕИ ANDROID ---
%ADB% shell "dumpsys battery | grep -e level -e voltage -e temperature -e status -e health -e powered -e current"

echo.
echo --- ТЕПЛОВЫЕ ЗОНЫ (NTC) ---
%ADB% shell "echo -n 'Батарея NTC (Zone 94): '; cat /sys/class/thermal/thermal_zone94/temp 2>/dev/null; echo -n 'BMS чип (Zone 95): '; cat /sys/class/thermal/thermal_zone95/temp 2>/dev/null; echo -n 'Warp зарядка (Zone 78): '; cat /sys/class/thermal/thermal_zone78/temp 2>/dev/null; echo -n 'Корпус (Zone 76): '; cat /sys/class/thermal/thermal_zone76/temp 2>/dev/null"

echo.
echo --- ПОСЛЕДНИЕ СООБЩЕНИЯ ЯДРА (healthd) ---
%ADB% shell "logcat -b kernel -d | grep 'healthd: battery' | tail -n 2"

:: Автоматическая запись строки в лог-файл на ПК
%ADB% shell "dumpsys battery | grep -e level -e voltage -e temperature" >> "%~dp0battery_history.log" 2>nul

echo.
echo ======================================================================
echo   ИНДИКАТОРЫ:
echo   * NTC = ровно 24000 (24.0 C) -> ОБМАНКА 10 кОм вместо термистора!
echo   * V ^> 4350 mV -> Порог для неоригинальной банки!
echo   * V ^> 4400 mV -> ОПАСНОСТЬ: перезаряд и электролиз!
echo   * Журнал непрерывно пишется в battery_history.log
echo ======================================================================
timeout /t 2 /nobreak >nul
goto MONITOR

:: ========================================================================
:: РЕЖИМ 2: СТРЕСС-ТЕСТ ТЕРМОДАТЧИКА NTC
:: ========================================================================
:STRESS_NTC
cls
echo ======================================================================
echo       РЕЖИМ 2: СТРЕСС-ТЕСТ ДЛЯ ПРОВЕРКИ ТЕРМОДАТЧИКА NTC
echo ======================================================================
echo.
echo [1/3] Замер базовой температуры до нагрузки...
%ADB% shell "echo -n 'Батарея NTC до теста: '; cat /sys/class/thermal/thermal_zone94/temp 2>/dev/null; echo -n 'Процессор CPU: '; cat /sys/class/thermal/thermal_zone38/temp 2>/dev/null"
echo.
echo [2/3] Нагрузка 8 ядер процессора Snapdragon 690 на 20 секунд...
echo       Пожалуйста, подождите...
%ADB% shell "(for i in 1 2 3 4; do while :; do :; done & done); sleep 20; pkill -f 'while' 2>/dev/null"

echo.
echo [3/3] Замер температуры после нагрузки...
%ADB% shell "echo -n 'Батарея NTC после теста: '; cat /sys/class/thermal/thermal_zone94/temp 2>/dev/null; echo -n 'Процессор CPU: '; cat /sys/class/thermal/thermal_zone38/temp 2>/dev/null; echo -n 'Корпус Skin: '; cat /sys/class/thermal/thermal_zone76/temp 2>/dev/null"
echo.
echo ======================================================================
echo   ВЕРДИКТ:
echo   * Если батарея NTC осталась ровно 24000 (24.0 C), а CPU нагрелся ->
echo     ЭТО 100%% ОБМАНКА! Термистора нет, на плате впаян постоянный резистор!
echo   * Если температура выросла -> термистор ЖИВОЙ.
echo ======================================================================
echo.
pause
goto MENU

:: ========================================================================
:: РЕЖИМ 3: ТЕСТ ОТСЕЧКИ PMIC
:: ========================================================================
:PMIC_CHECK
cls
echo ======================================================================
echo       РЕЖИМ 3: ПРОВЕРКА КЛЮЧЕЙ И ОТСЕЧКИ КОНТРОЛЛЕРА PMIC
echo ======================================================================
echo.
echo Анализ последних записей контроллеров ядра...
echo.
%ADB% shell "logcat -b kernel -d | grep -e 'healthd: battery' -e 'SMBLIB: op_check_charger_uovp' -e 'bq27541_battery_soc' | tail -n 12"
echo.
echo ----------------------------------------------------------------------
echo  Расшифровка параметров:
echo   v=XXXX   -> Текущее напряжение на банке в милливольтах (mV)
echo   c=XXXX   -> Ток заряда (0 = отсечка сработала, -300000 = идет заряд 300 mA)
echo   st=5     -> Статус FULL (заряд успешно окончен)
echo   fc=XXXX  -> Целевое напряжение отсечки ядра
echo ----------------------------------------------------------------------
echo.
pause
goto MENU

:: ========================================================================
:: РЕЖИМ 4: ПОЛНЫЙ ДАМП ПОДСИСТЕМЫ ПИТАНИЯ
:: ========================================================================
:DUMP_FULL
cls
echo ======================================================================
echo       РЕЖИМ 4: ПОЛНЫЙ ИНЖЕНЕРНЫЙ ДАМП
echo ======================================================================
echo.
echo 1. Версия контроллера TI BQ27541 в ядре:
%ADB% shell "logcat -b kernel -d | grep 'bq27541' | head -n 10"
echo.
echo 2. Конфигурация Devicetree:
%ADB% shell "logcat -b kernel -d | grep '4p45V' | head -n 5"
echo.
echo 3. Сводка Battery Service:
%ADB% shell "dumpsys battery"
echo.
pause
goto MENU
