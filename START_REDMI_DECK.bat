@echo off
chcp 65001 > nul
echo ===================================================
echo   ⚡ TRIAD-OMNI: ЗАПУСК ПУЛЬТА REDMI NOTE 4
echo ===================================================
echo.

set ADB="%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"
if not exist %ADB% (
    set ADB=adb.exe
)

echo [*] Проверка подключения Redmi Note 4 через ADB...
%ADB% devices | findstr /R "7LS8SKLV55IZSK7S.*device" > nul
if errorlevel 1 (
    echo [!] Redmi Note 4 не найден по USB кабелю или не авторизован.
    echo [*] Пробую подключиться напрямую по Wi-Fi (192.168.31.48)...
    ssh -o StrictHostKeyChecking=no -o ConnectTimeout=4 -p 8022 192.168.31.48 "nohup sh ~/start_deck.sh >/dev/null 2>&1 &"
    if errorlevel 1 (
        echo [!] Не удалось связаться с Redmi Note 4 по Wi-Fi. Убедитесь, что Termux и SSH запущены.
    ) else (
        echo [+] Сигнал на запуск отправлен по Wi-Fi.
    )
    goto open_browser
)

echo [+] Redmi Note 4 обнаружен по USB.
echo [*] Проброс портов: 8000 (шлюз) и 8022 (SSH)...
%ADB% forward tcp:8000 tcp:8000
%ADB% forward tcp:8022 tcp:8022

echo [*] Запуск Master Router на телефоне в фоновом режиме...
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -p 8022 127.0.0.1 "nohup sh ~/start_deck.sh >/dev/null 2>&1 &"

echo [*] Включение экрана и запуск Kiosk-дашборда на телефоне...
%ADB% shell "input keyevent 224; input keyevent 82"
%ADB% shell "am start -a android.intent.action.VIEW -d 'http://127.0.0.1:8000/?deck=1' -n com.android.chrome/com.google.android.apps.chrome.Main" > nul 2>&1

:open_browser
echo.
echo [+] Кластерный пульт запущен!
echo [+] Веб-интерфейс доступен:
echo       Локально на ПК: http://localhost:8000
echo       В локальной сети: http://192.168.31.48:8000
echo.
pause
