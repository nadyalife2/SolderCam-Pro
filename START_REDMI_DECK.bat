@echo off
chcp 65001 > nul
echo ===================================================
echo   ⚡ TRIAD-OMNI: ЗАПУСК ПУЛЬТА REDMI NOTE 4
echo ===================================================
echo.

set ADB="%LOCALAPPDATA%\Android\Sdk\platform-tools\adb.exe"

echo [*] Проверка подключения Redmi Note 4 через ADB...
%ADB% devices | findstr "7LS8SKLV55IZSK7S" > nul
if errorlevel 1 (
    echo [!] Ошибка: Redmi Note 4 не найден по кабелю.
    echo [*] Пробую подключиться напрямую по Wi-Fi (192.168.31.48)...
    ssh -o StrictHostKeyChecking=no -p 8022 192.168.31.48 "~/start_deck.sh"
    goto open_browser
)

echo [+] Redmi Note 4 обнаружен.
echo [*] Проброс портов: 8000 (шлюз) и 8022 (SSH)...
%ADB% forward tcp:8000 tcp:8000
%ADB% forward tcp:8022 tcp:8022

echo [*] Проверка активности шлюза...
ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -p 8022 127.0.0.1 "~/start_deck.sh"

echo [*] Включение экрана и запуск Kiosk-дашборда на телефоне...
%ADB% shell "input keyevent 224; input keyevent 82"
%ADB% shell "am start -a android.intent.action.VIEW -d 'http://127.0.0.1:8000/?deck=1' -n com.android.chrome/com.google.android.apps.chrome.Main"

:open_browser
echo.
echo [+] Кластерный пульт запущен и готов!
echo [+] Веб-интерфейс открыт на телефоне и доступен на ПК: http://localhost:8000
echo.
pause
