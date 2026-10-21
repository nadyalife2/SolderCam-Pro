# OnePlus Nord N10 5G - Advanced Battery Telemetry & Diagnostics
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$adbPath = "C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
if (-not (Test-Path $adbPath)) { $adbPath = "adb" }

$deviceCheck = & $adbPath devices
if ($deviceCheck -notmatch "device\b") {
    Write-Host "[!] Телефон не подключен или не авторизован в ADB!" -ForegroundColor Red
    exit 1
}

Write-Host "[+] Подключение к BE2029 успешно.`n" -ForegroundColor Green

$dump = & $adbPath shell "dumpsys battery"
$voltage = 0
$temp = 0
$level = 0
$charging = $false

foreach ($line in ($dump -split "`n")) {
    if ($line -match "level:\s*(\d+)") { $level = [int]$matches[1] }
    if ($line -match "voltage:\s*(\d+)") { $voltage = [int]$matches[1] }
    if ($line -match "temperature:\s*(\d+)") { $temp = [float]$matches[1] / 10.0 }
    if ($line -match "status:\s*2") { $charging = $true }
}

$thermal94 = (& $adbPath shell "cat /sys/class/thermal/thermal_zone94/temp 2>/dev/null").Trim()
$thermal78 = (& $adbPath shell "cat /sys/class/thermal/thermal_zone78/temp 2>/dev/null").Trim()
$thermal76 = (& $adbPath shell "cat /sys/class/thermal/thermal_zone76/temp 2>/dev/null").Trim()

$battZoneC = if ($thermal94) { [math]::Round([float]$thermal94 / 1000.0, 1) } else { $temp }
$warpZoneC = if ($thermal78) { [math]::Round([float]$thermal78 / 1000.0, 1) } else { 0 }
$skinZoneC = if ($thermal76) { [math]::Round([float]$thermal76 / 1000.0, 1) } else { 0 }

$klog = & $adbPath shell "logcat -b kernel -d | grep 'healthd: battery' | tail -n 1"

Write-Host "[ ОСНОВНЫЕ ПОКАЗАТЕЛИ ]" -ForegroundColor Yellow
Write-Host "• Уровень заряда:   $level %"

if ($voltage -ge 4400) {
    Write-Host "• Напряжение:       $voltage mV [КРИТИЧЕСКИЙ ПЕРЕЗАРЯД > 4.40V! ЭЛЕКТРОЛИЗ!]" -ForegroundColor Red
} elseif ($voltage -ge 4350) {
    Write-Host "• Напряжение:       $voltage mV [ВНИМАНИЕ: Превышение 4.35V для неоригинала]" -ForegroundColor DarkYellow
} else {
    Write-Host "• Напряжение:       $voltage mV [В норме менее 4.35V]" -ForegroundColor Green
}

if ($battZoneC -eq 24.0 -or $battZoneC -eq 25.0) {
    Write-Host "• Температура АКБ:  $battZoneC °C [ВНИМАНИЕ: ЗАМОРОЖЕНА! ОБМАНКА 10 кОм ВМЕСТО NTC]" -ForegroundColor Red
} else {
    Write-Host "• Температура АКБ:  $battZoneC °C [Живой NTC]" -ForegroundColor Green
}

Write-Host "• Температура Warp: $warpZoneC °C | Корпус: $skinZoneC °C" -ForegroundColor Gray
Write-Host "• Статус зарядки:   $(if ($charging) {'ИДЕТ ЗАРЯД'} else {'РАЗРЯД / ОТКЛЮЧЕН'})"

if ($klog) {
    Write-Host "`n[ ЯДРО LINUX (healthd) ]" -ForegroundColor Yellow
    Write-Host $klog.Trim() -ForegroundColor Gray
}
