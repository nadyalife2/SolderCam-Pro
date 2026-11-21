# -*- coding: utf-8 -*-
import subprocess
import time
import json
import os

ADB = r"C:\Users\MSI\AppData\Local\Android\Sdk\platform-tools\adb.exe"
DEVICE = "50fb497c"

def run_adb(cmd):
    full_cmd = [ADB, "-s", DEVICE] + cmd
    res = subprocess.run(full_cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return res.stdout.strip()

def get_meminfo():
    out = run_adb(["shell", "cat /proc/meminfo"])
    mem = {}
    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) == 2:
            k = parts[0].strip()
            v = parts[1].strip()
            if "kB" in v:
                val = int(v.replace("kB", "").strip())
                mem[k] = val
    return mem

# Список пакетов под снос (потребители RAM, фоновые трекеры AppMetrica, реклама, доставка, соцсети)
PACKAGES_TO_REMOVE = [
    # Еда и доставка
    "ru.foodfox.client",
    "com.deliveryclub",
    "ru.pyaterochka.app.browser",
    "com.delivery_shop_5ka24.delivery_shop_5ka",
    "ru.instamart",
    # Маркетплейсы и ритейл
    "ru.yandex.market",
    "ru.beru.android",
    "ru.ozon.app.android",
    "ru.goods.marketplace",
    "ru.sima_land.spb.market",
    "ru.galamart2023.app",
    "goldapple.ru.goldapple.customers",
    "ru.mvm.eldo",
    "ru.filit.mvideo.b2c",
    "ru.dns.shop.android",
    "com.kazanexpress.ke_app",
    "com.notissimus.allinstruments.android",
    "com.farmlend.android",
    "com.avito.android",
    # Соцсети, видео, музыка
    "com.zhiliaoapp.musically",
    "com.ss.android.tt.creator",
    "com.instagram.android",
    "com.discord",
    "ru.fourpda.client",
    "ru.pepper",
    "ru.rt.video.app.mobile",
    "ru.kinopoisk",
    "ru.plus.bookmate",
    "ru.zen.android",
    "com.aimp.player",
    "com.kmplayer",
    "com.zvooq.openplay",
    "com.media.music.mp3.musicplayer",
    "ru.yandex.music",
    "com.google.android.apps.youtube.creator",
    # Тяжёлая экосистема Яндекса с AppMetrica
    "com.yandex.searchapp",
    "com.yandex.browser",
    "ru.yandex.yandexmaps",
    "ru.yandex.taxi",
    "ru.yandex.disk",
    "ru.yandex.mobile.gasstations",
    "com.yandex.iot",
    "com.yandex.mobile.plus.game.city",
    "ru.yandex.bank",
    "ru.yandex.key",
    # Антивирусы, сканеры, утилиты
    "com.kaspersky.who_calls",
    "com.kms.free",
    "com.kaspersky.qrscanner",
    "com.microsoft.bing",
    "com.microsoft.emmx",
    "com.teamviewer.teamviewer.market.mobile",
    "com.akzonobel.ru.dulux",
    "com.poersmart.smarthome",
    "com.xiaomi.smarthome",
    "com.tuya.smartlife",
    "ru.mail.mailapp",
    "ru.mail.cloud",
    "com.kimcy929.screenrecorder",
    "com.hecorat.screenrecorder.free",
    "de.stocard.stocard",
    "com.tv.cast.screen.mirroring.remote.control",
    "com.eshare.clientv2",
    "com.transsion.letswitch",
    "ru.sbcs.store",
    "ru.vk.store",
    "ru.startandroid.smsactivate",
    "ru.fns.lkfl",
    "com.binance.dev",
    "com.ton_keeper",
    "ch.pboos.android.SleepTimer",
    "org.cohortor.gstrings",
    "com.triplens.android",
    # Операторский софт
    "ru.megafon.mlk",
    "ru.tele2.mytele2",
    "ru.rostel",
    "ru.tinkoff.mvno",
    "ru.mw",
    # Банковские приложения (тяжёлые сервисы безопасности и пушей)
    "ru.sberbankmobile",
    "ru.sberbank.spasibo",
    "ru.vtb24.mobilebanking.android",
    "com.idamob.tinkoff.android",
    "ru.nspk.mirpay",
    "ru.nspk.sbpay",
    "ru.gosuslugi.goskey"
]

print("=== НАЧАЛО ГЛУБОКОГО ДЕБЛОАТА ONEPLUS NORD N10 ===")
mem_before = get_meminfo()
avail_before_mb = mem_before.get('MemAvailable', 0) / 1024.0
swap_before_mb = mem_before.get('SwapFree', 0) / 1024.0
print(f"Память ДО: MemAvailable = {avail_before_mb:.1f} МБ | SwapFree = {swap_before_mb:.1f} МБ")

# Проверяем установленные
installed = run_adb(["shell", "pm list packages -u"]).splitlines()
installed_set = set([p.replace("package:", "").strip() for p in installed])

removed_count = 0
removed_list = []

for pkg in PACKAGES_TO_REMOVE:
    if pkg in installed_set:
        res = run_adb(["shell", f"pm uninstall -k --user 0 {pkg}"])
        if "Success" in res:
            removed_count += 1
            removed_list.append(pkg)
            print(f"[-] Удален: {pkg}")
        else:
            print(f"[!] Ошибка при удалении {pkg}: {res}")

# Сохраняем список удаленных для возможности отката в 1 клик
backup_file = r"d:\для one plus nord n10\heavy_debloat_removed_packages.json"
with open(backup_file, "w", encoding="utf-8") as f:
    json.dump(removed_list, f, ensure_ascii=False, indent=2)

print(f"\nВсего успешно удалено пакетов: {removed_count}")
print(f"Список удаленных сохранен в: {backup_file}")

# Принудительная зачистка зомби-процессов
run_adb(["shell", "am kill-all"])
time.sleep(2)

mem_after = get_meminfo()
avail_after_mb = mem_after.get('MemAvailable', 0) / 1024.0
swap_after_mb = mem_after.get('SwapFree', 0) / 1024.0

gain_avail = avail_after_mb - avail_before_mb
gain_swap = swap_after_mb - swap_before_mb

print(f"\nПамять ПОСЛЕ: MemAvailable = {avail_after_mb:.1f} МБ | SwapFree = {swap_after_mb:.1f} МБ")
print(f"ПРИРОСТ: MemAvailable: +{gain_avail:.1f} МБ | SwapFree: +{gain_swap:.1f} МБ")
print("=== ГЛУБОКИЙ ДЕБЛОАТ ЗАВЕРШЕН ===")
