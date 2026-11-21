@echo off
chcp 65001 > nul
echo ========================================================
echo   УДАЛЕНИЕ ТЯЖЕЛЫХ ПРИЛОЖЕНИЙ И ОПТИМИЗАЦИЯ ДИСКА C:
echo ========================================================
echo.

:: Проверка прав администратора
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] ОШИБКА: Запустите этот файл от имени Администратора!
    echo Щелкните правой кнопкой мыши по файлу и выберите:
    echo "Запуск от имени администратора"
    echo.
    pause
    exit /b 1
)

echo [+] 1. Отключение файла гибернации (освобождает 4.76 ГБ)...
powercfg -h off
echo     [OK] Гибернация отключена.
echo.

echo [+] 2. Удаление LibreOffice 7.5.1.2...
msiexec.exe /x {BFAC9A9B-8A3E-47A6-97AE-53DC3266ACE1} /passive /norestart
echo     [OK] LibreOffice удален.
echo.

echo [+] 3. Удаление PDF24 Creator...
if exist "D:\програмки\PDF24\unins000.exe" (
    "D:\програмки\PDF24\unins000.exe" /SILENT /VERYSILENT /SUPPRESSMSGBOXES /NORESTART
    echo     [OK] PDF24 Creator удален.
) else (
    echo     [!] PDF24 uninstaller не найден, пропускаем.
)
echo.

echo [+] 4. Удаление Visual Studio Enterprise 2022...
if exist "C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe" (
    "C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe" uninstall --installPath "C:\Program Files\Microsoft Visual Studio\2022\Enterprise" --passive --norestart
    echo     [OK] Visual Studio 2022 Enterprise удалена.
) else (
    echo     [!] VS Installer не найден.
)
echo.

echo [+] 5. Удаление Visual Studio Build Tools 2019...
if exist "C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe" (
    "C:\Program Files (x86)\Microsoft Visual Studio\Installer\setup.exe" uninstall --installPath "C:\Program Files (x86)\Microsoft Visual Studio\2019\BuildTools" --passive --norestart
    echo     [OK] Visual Studio 2019 Build Tools удален.
)
echo.

echo [+] 6. Удаление Windows SDK 10.0.19041...
if exist "C:\ProgramData\Package Cache\{4591faf1-a2db-4a3d-bfda-aa5a4ebb1587}\winsdksetup.exe" (
    "C:\ProgramData\Package Cache\{4591faf1-a2db-4a3d-bfda-aa5a4ebb1587}\winsdksetup.exe" /uninstall /quiet
    echo     [OK] Windows SDK удален.
)
echo.

echo ========================================================
echo   ВСЕ ВЫБРАННЫЕ ПРИЛОЖЕНИЯ УДАЛЕНЫ!
echo   KMPlayer и DriverPack сохранены без изменений.
echo ========================================================
echo.
pause
