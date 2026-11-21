#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni Cluster Hub APK Builder & Signer v2.0
Собирает, патчит и подписывает нативный Android APK-клиент Triad-Omni Cluster Hub для Xiaomi Mi 10T 5G (apollo).
- Встраивает официальную кибердек-иконку ic_launcher.png (192x192 px, 32-bit RGBA).
- Патчит resources.arsc (путь к иконке res/drawable/ic_launcher.png, имя приложения TriadOmni).
- Патчит classes.dex (URL http://127.0.0.1:8080/, онлайн-статус IP:192.168.1.4:8080).
- Патчит activity_main.xml (заголовок 192.168.1.4 :8080, бэдж PORT:8080).
- Подписывает APK криптографическим сертификатом v1 (JAR Signature).
"""

import os
import sys
import zlib
import zipfile
import hashlib
import datetime
import struct
import base64
from pathlib import Path

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import pkcs7

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_APK = BASE_DIR / "melvin_src" / "ai.melvin.app.apk"
OUTPUT_APK = BASE_DIR / "TriadOmni_Cluster_Hub.apk"
ICON_PNG = BASE_DIR / "ic_launcher_192.png"

def patch_dex_bytes(dex: bytearray) -> bytearray:
    """Патчит URL-адреса, заголовок и порты в classes.dex с пересчетом Adler32 и SHA1."""
    # 1. Заменяем URL: http://127.0.0.1:5000/ -> http://127.0.0.1:8080/ (ровно 22 байта)
    old_url = b"http://127.0.0.1:5000/"
    new_url = b"http://127.0.0.1:8080/"
    dex = bytearray(bytes(dex).replace(old_url, new_url))

    # 2. Заменяем port строки "5000" -> "8000" / "8080"
    old_port = b": 127.0.0.1:5000 "
    new_port = b": 127.0.0.1:8080 "
    dex = bytearray(bytes(dex).replace(old_port, new_port))

    # 3. Заменяем статус ONLINE (19 байт) строго с сохранением лексикографического порядка DEX:
    # \x13MELVIN AI // ONLINE -> \x13MELVIN: 192.168.1.4
    old_online = b"\x13MELVIN AI // ONLINE"
    new_online = b"\x13MELVIN: 192.168.1.4"
    dex = bytearray(bytes(dex).replace(old_online, new_online))

    # 4. Заменяем статус OFFLINE (20 байт) строго с сохранением лексикографического порядка DEX:
    # \x14MELVIN AI // OFFLINE -> \x14MELVIN / 192.168.1.4
    old_offline = b"\x14MELVIN AI // OFFLINE"
    new_offline = b"\x14MELVIN / 192.168.1.4"
    dex = bytearray(bytes(dex).replace(old_offline, new_offline))

    # 5. Пересчитываем SHA1 signature (bytes 12..31) от содержимого с 32 байта до конца
    sha1_digest = hashlib.sha1(dex[32:]).digest()
    dex[12:32] = sha1_digest

    # 6. Пересчитываем Adler32 checksum (bytes 8..11, little-endian) от байта 12 до конца
    adler = zlib.adler32(dex[12:]) & 0xffffffff
    dex[8:12] = struct.pack("<I", adler)

    return dex

def patch_resources_arsc(arsc: bytearray) -> bytearray:
    """Патчит имя приложения и путь к иконке в бинарных ресурсах resources.arsc."""
    # "Melvin AI" (9 байт) -> "TriadOmni" (9 байт)
    old_name = b"Melvin AI"
    new_name = b"TriadOmni"
    arsc = bytearray(bytes(arsc).replace(old_name, new_name))

    # "res/drawable/ic_launcher.xml" (28 байт) -> "res/drawable/ic_launcher.png" (28 байт)
    old_icon = b"res/drawable/ic_launcher.xml"
    new_icon = b"res/drawable/ic_launcher.png"
    arsc = bytearray(bytes(arsc).replace(old_icon, new_icon))

    return arsc

def patch_activity_main_layout(layout: bytearray) -> bytearray:
    """Патчит стартовые текстовые плашки в AXML макете activity_main.xml."""
    # "Helio X20" (9 байт) -> "PORT:8080" (9 байт)
    old_soc = b"Helio X20"
    new_soc = b"PORT:8080"
    layout = bytearray(bytes(layout).replace(old_soc, new_soc))

    # "MELVIN AI // CORE" (17 байт) -> "192.168.1.4 :8080" (17 байт)
    old_title = b"MELVIN AI // CORE"
    new_title = b"192.168.1.4 :8080"
    layout = bytearray(bytes(layout).replace(old_title, new_title))

    return layout

KEY_FILE = BASE_DIR / "scripts" / "triad_omni_key.pem"
CERT_FILE = BASE_DIR / "scripts" / "triad_omni_cert.pem"

def generate_signing_credentials():
    """Загружает или генерирует постоянный RSA ключ и самоподписанный X.509 сертификат."""
    if KEY_FILE.exists() and CERT_FILE.exists():
        key = serialization.load_pem_private_key(KEY_FILE.read_bytes(), password=None)
        cert = x509.load_pem_x509_certificate(CERT_FILE.read_bytes())
        return key, cert

    key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "Triad-Omni Developer"),
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Triad-Omni Edge AI Cluster"),
        x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Hardware Engineering"),
        x509.NameAttribute(NameOID.COUNTRY_NAME, "RU"),
    ])

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(13377331)
        .not_valid_before(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1))
        .not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        .sign(key, hashes.SHA256())
    )

    KEY_FILE.write_bytes(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))
    CERT_FILE.write_bytes(cert.public_bytes(serialization.Encoding.PEM))

    return key, cert

def build_signed_apk():
    print(f"📦 Чтение исходного шаблона: {SOURCE_APK.name}...")
    if not SOURCE_APK.exists():
        raise FileNotFoundError(f"Файл {SOURCE_APK} не найден!")

    with zipfile.ZipFile(SOURCE_APK, "r") as z_in:
        apk_entries = {}
        for item in z_in.infolist():
            # Пропускаем старые подписи META-INF
            if item.filename.startswith("META-INF/"):
                continue
            apk_entries[item.filename] = z_in.read(item.filename)

    print("⚡ Патчинг classes.dex (роутинг на :8080, заголовок IP:192.168.1.4:8080)...")
    if "classes.dex" in apk_entries:
        apk_entries["classes.dex"] = bytes(patch_dex_bytes(bytearray(apk_entries["classes.dex"])))

    print("🎨 Патчинг resources.arsc (имя: TriadOmni, иконка: ic_launcher.png)...")
    if "resources.arsc" in apk_entries:
        apk_entries["resources.arsc"] = bytes(patch_resources_arsc(bytearray(apk_entries["resources.arsc"])))

    print("📐 Патчинг layout activity_main.xml (192.168.1.4 :8080, PORT:8080)...")
    if "res/layout/activity_main.xml" in apk_entries:
        apk_entries["res/layout/activity_main.xml"] = bytes(patch_activity_main_layout(bytearray(apk_entries["res/layout/activity_main.xml"])))

    print("🖼️ Добавление PNG иконки в res/drawable/ic_launcher.png...")
    if ICON_PNG.exists():
        apk_entries["res/drawable/ic_launcher.png"] = ICON_PNG.read_bytes()
        print(f"  Встроена иконка {ICON_PNG.name} ({len(apk_entries['res/drawable/ic_launcher.png'])} байт)")
    else:
        print(f"  ⚠️ Предупреждение: {ICON_PNG} не найден!")

    print("🔐 Генерация криптографической подписи APK v1 (JAR Signature)...")
    private_key, cert = generate_signing_credentials()

    # 1. Формируем MANIFEST.MF
    manifest_lines = [
        "Manifest-Version: 1.0",
        "Created-By: 2.0 (Triad-Omni Hub Builder)",
        ""
    ]
    manifest_entries = {}
    for fname, data in sorted(apk_entries.items()):
        digest = hashlib.sha256(data).digest()
        b64_digest = base64.b64encode(digest).decode("ascii")
        manifest_entries[fname] = b64_digest
        manifest_lines.append(f"Name: {fname}")
        manifest_lines.append(f"SHA-256-Digest: {b64_digest}")
        manifest_lines.append("")

    manifest_bytes = "\r\n".join(manifest_lines).encode("utf-8")
    apk_entries["META-INF/MANIFEST.MF"] = manifest_bytes

    # 2. Формируем CERT.SF
    sf_lines = [
        "Signature-Version: 1.0",
        "Created-By: 2.0 (Triad-Omni Hub Builder)",
        f"SHA-256-Digest-Manifest: {base64.b64encode(hashlib.sha256(manifest_bytes).digest()).decode('ascii')}",
        ""
    ]
    for fname, b64_digest in manifest_entries.items():
        entry_spec = f"Name: {fname}\r\nSHA-256-Digest: {b64_digest}\r\n\r\n".encode("utf-8")
        entry_sf_digest = base64.b64encode(hashlib.sha256(entry_spec).digest()).decode("ascii")
        sf_lines.append(f"Name: {fname}")
        sf_lines.append(f"SHA-256-Digest: {entry_sf_digest}")
        sf_lines.append("")

    sf_bytes = "\r\n".join(sf_lines).encode("utf-8")
    apk_entries["META-INF/CERT.SF"] = sf_bytes

    # 3. Формируем CERT.RSA (PKCS#7 SignedData) без S/MIME атрибутов
    pkcs7_builder = (
        pkcs7.PKCS7SignatureBuilder()
        .set_data(sf_bytes)
        .add_signer(cert, private_key, hashes.SHA256())
    )
    rsa_bytes = pkcs7_builder.sign(
        serialization.Encoding.DER,
        [pkcs7.PKCS7Options.DetachedSignature, pkcs7.PKCS7Options.NoAttributes]
    )
    apk_entries["META-INF/CERT.RSA"] = rsa_bytes

    print(f"🚀 Сборка готового APK: {OUTPUT_APK}...")
    with zipfile.ZipFile(OUTPUT_APK, "w", compression=zipfile.ZIP_DEFLATED) as z_out:
        for fname, data in apk_entries.items():
            z_out.writestr(fname, data)

    apk_size = OUTPUT_APK.stat().st_size
    print(f"✅ TriadOmni_Cluster_Hub.apk v2.0 успешно собран и подписан! Размер: {apk_size} байт ({apk_size/1024:.1f} KB)")

    import shutil
    user_downloads = Path.home() / "Downloads" / "TriadOmni_Cluster_Hub.apk"
    try:
        shutil.copy2(OUTPUT_APK, user_downloads)
        print(f"📥 Копия сохранена в папку Загрузки: {user_downloads}")
    except Exception as e:
        print(f"  Не удалось скопировать в Загрузки: {e}")

    return OUTPUT_APK

if __name__ == "__main__":
    build_signed_apk()
