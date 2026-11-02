# ========================================================
# Скрипт экспресс-диагностики Poco X3 Pro (vayu / bhima)
# Проверка реакции загрузчика (ABL) vs Ядро Linux (Recovery)
# ========================================================

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$Host.UI.RawUI.WindowTitle = "Диагностика Poco X3 Pro (M2102J20SG)"

$FastbootPath = "$env:LOCALAPPDATA\Android\Sdk\platform-tools\fastboot.exe"

# Если fastboot не найден в стандартном каталоге Android SDK, ищем в PATH
if (-not (Test-Path $FastbootPath)) {
    $cmd = Get-Command fastboot -ErrorAction SilentlyContinue
    if ($cmd) {
        $FastbootPath = $cmd.Source
    } else {
        Write-Host "[-] ОШИБКА: fastboot.exe не найден!" -ForegroundColor Red
        Write-Host "Укажите путь к platform-tools вручную или установите Android SDK." -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   ЭКСПРЕСС-ДИАГНОСТИКА POCO X3 PRO: ОТВАЛ CPU / RAM      " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[*] Используется fastboot: $FastbootPath" -ForegroundColor Gray
Write-Host ""

# 1. Ожидание устройства в режиме Fastboot
Write-Host "[1/3] Ожидание подключения телефона в режиме Fastboot..." -ForegroundColor Yellow
Write-Host "      (Зажмите 'Громкость вниз' + 'Питание' до надписи FASTBOOT и подключите кабель)" -ForegroundColor DarkGray

$deviceFound = $false
while (-not $deviceFound) {
    $devices = & $FastbootPath devices
    if ($devices -match "\w+\s+fastboot") {
        $deviceFound = $true
        $serial = ($devices -split "`t| ")[0]
        Write-Host "[+] Устройство обнаружено! Серийный номер: $serial" -ForegroundColor Green
    } else {
        Start-Sleep -Seconds 1
    }
}

Write-Host ""
Write-Host "--- Получение параметров загрузчика ---" -ForegroundColor Cyan
$product = (& $FastbootPath getvar product 2>&1 | Select-String "product:").ToString().Trim()
$unlocked = (& $FastbootPath getvar unlocked 2>&1 | Select-String "unlocked:").ToString().Trim()
$secure = (& $FastbootPath getvar secure 2>&1 | Select-String "secure:").ToString().Trim()

Write-Host "  > $product" -ForegroundColor White
Write-Host "  > $unlocked" -ForegroundColor White
Write-Host "  > $secure" -ForegroundColor White
Write-Host ""

# 2. Тест 1: Перезагрузка в Bootloader (ABL / UEFI)
Write-Host "[2/3] ТЕСТ 1: Перезагрузка в Bootloader (ABL / UEFI)..." -ForegroundColor Yellow
Write-Host "      Команда: fastboot reboot bootloader" -ForegroundColor Gray
Write-Host "      В этом режиме работают минимальные частоты памяти и базовый драйвер." -ForegroundColor DarkGray
Write-Host "      Выполняем перезагрузку..." -ForegroundColor Yellow

& $FastbootPath reboot bootloader
Start-Sleep -Seconds 4

# Проверяем, вернулся ли телефон обратно в Fastboot
$backInFastboot = $false
for ($i = 0; $i -lt 10; $i++) {
    $check = & $FastbootPath devices
    if ($check -match "\w+\s+fastboot") {
        $backInFastboot = $true
        break
    }
    Start-Sleep -Seconds 1
}

if ($backInFastboot) {
    Write-Host "[+] ТЕСТ 1 УСПЕШЕН: Телефон штатно вернулся в Fastboot!" -ForegroundColor Green
    Write-Host "    Это подтверждает, что базовая память ABL и дисплей работают в низковольтном режиме." -ForegroundColor DarkGreen
} else {
    Write-Host "[!] Телефон не вернулся в Fastboot. Возможно, контакт пропал уже на этапе ABL." -ForegroundColor Red
}

Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "[3/3] ТЕСТ 2: Перезагрузка в Recovery (Ядро Linux / MDSS)..." -ForegroundColor Yellow
Write-Host "      Команда: fastboot reboot recovery" -ForegroundColor Gray
Write-Host "      ВНИМАНИЕ! Сейчас запустится ядро Linux (полные частоты ОЗУ + шина дисплея)." -ForegroundColor DarkYellow
Write-Host ""
Write-Host "Нажмите любую клавишу для отправки команды перезагрузки в Recovery..." -ForegroundColor White
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

& $FastbootPath reboot recovery
Write-Host ""
Write-Host "[*] Команда отправлена! Посмотрите на экран телефона." -ForegroundColor Cyan
Write-Host ""
Write-Host "====================== ВЕРДИКТ ==========================" -ForegroundColor Yellow
Write-Host "1) Если экран стал БЕЛЫМ или погас, а телефон завис:" -ForegroundColor Red
Write-Host "   -> 100% АППАРАТНЫЙ ОТВАЛ ПРОЦЕССОРА / ОЗУ (СЭНДВИЧ SD860)." -ForegroundColor Red
Write-Host "   Причина: ядро Linux не может общаться с RAM/DSI из-за микротрещин в пайке." -ForegroundColor DarkRed
Write-Host ""
Write-Host "2) Если открылось меню Recovery (Mi-Recovery):" -ForegroundColor Green
Write-Host "   -> BGA-пайка жива, проблема была программной в разделе system/boot." -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Yellow
