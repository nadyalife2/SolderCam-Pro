"""
SoC & Hardware Knowledge Base for Melvin Edge AI
Contains physical specifications, fabrication process node (nm), CPU/GPU architectures,
and eMMC/UFS manufacturer identification.
"""

# Производители чипов памяти по JEDEC CID manfid
MEMORY_MANUFACTURERS = {
    "0x15": "Samsung",
    "15": "Samsung",
    "0x90": "SK Hynix",
    "90": "SK Hynix",
    "0x11": "Toshiba / Kioxia",
    "11": "Toshiba / Kioxia",
    "0x13": "Micron",
    "13": "Micron",
    "0x45": "SanDisk / Western Digital",
    "45": "SanDisk / Western Digital",
    "0x70": "Kingston",
    "70": "Kingston",
    "0x2c": "Micron",
    "2c": "Micron",
    "0x88": "Foresee (Longsys)",
    "88": "Foresee (Longsys)",
    "0xfe": "Micron",
    "fe": "Micron"
}

# База чипсетов: нанометры, архитектура ядер, видеоядро, назначение
SOC_DATABASE = {
    # === AMLOGIC (ТВ-боксы, проекторы, Smart TV) ===
    "s905x4": {
        "vendor": "Amlogic",
        "model": "S905X4 (SC2)",
        "process_nm": "12 нм",
        "cpu": "4x ARM Cortex-A55 @ до 2.0 ГГц (ARMv8.2-A 64-bit)",
        "gpu": "ARM Mali-G31 MP2 (Vulkan 1.1, OpenGL ES 3.2)",
        "features": "Аппаратное декодирование AV1 4K@60fps, HDR10+, Dolby Vision"
    },
    "s905x3": {
        "vendor": "Amlogic",
        "model": "S905X3 (SM1)",
        "process_nm": "12 нм",
        "cpu": "4x ARM Cortex-A55 @ до 1.9 ГГц (ARMv8.2-A 64-bit)",
        "gpu": "ARM Mali-G31 MP2 (Vulkan 1.1, OpenGL ES 3.2)",
        "features": "Холодный чип, 4K@60fps VP9/H.265, идеален для TV-боксов (X96 Max+, Vontar X3)"
    },
    "s905x2": {
        "vendor": "Amlogic",
        "model": "S905X2 (U211)",
        "process_nm": "12 нм",
        "cpu": "4x ARM Cortex-A53 @ до 1.8 ГГц (ARMv8-A 64-bit)",
        "gpu": "ARM Mali-G31 MP2",
        "features": "Первый 12нм чип Amlogic, USB 3.0, 4K@60fps"
    },
    "s905x": {
        "vendor": "Amlogic",
        "model": "S905X (P212)",
        "process_nm": "28 нм",
        "cpu": "4x ARM Cortex-A53 @ до 1.5 ГГц (ARMv8-A 64-bit)",
        "gpu": "ARM Mali-450 MP3 @ 750 МГц",
        "features": "Классика Xiaomi Mi Box S, греется до 70-80°C, 4K VP9"
    },
    "s905w": {
        "vendor": "Amlogic",
        "model": "S905W (P281)",
        "process_nm": "28 нм",
        "cpu": "4x ARM Cortex-A53 @ до 1.2 ГГц (порезаны частоты)",
        "gpu": "ARM Mali-450 MP3",
        "features": "Бюджетник (X96 Mini), аппаратно ограничен 4K@30fps / 1080p@60fps"
    },
    "s905w2": {
        "vendor": "Amlogic",
        "model": "S905W2",
        "process_nm": "12 нм",
        "cpu": "4x ARM Cortex-A35 @ до 1.8 ГГц (энергоэффективный ARMv8-A)",
        "gpu": "ARM Mali-G31 MP2",
        "features": "12нм ультрабюджетник с поддержкой AV1 4K@60fps (Tanix W2, X98 Plus)"
    },
    "s912": {
        "vendor": "Amlogic",
        "model": "S912 (GXM)",
        "process_nm": "28 нм",
        "cpu": "8x ARM Cortex-A53 (4x 1.5 ГГц + 4x 1.0 ГГц big.LITTLE)",
        "gpu": "ARM Mali-T820 MP3",
        "features": "8-ядерная печка прошлых лет, без доп. охлаждения ловит троттлинг"
    },
    "s922x": {
        "vendor": "Amlogic",
        "model": "S922X (G12B)",
        "process_nm": "12 нм",
        "cpu": "6 ядер (4x Cortex-A73 @ 2.2 ГГц + 2x Cortex-A53 @ 1.8 ГГц)",
        "gpu": "ARM Mali-G52 MP4",
        "features": "Флагманский монстр (Ugoos AM6B Plus, Beelink GT-King), мощный гейминг"
    },
    "a311d": {
        "vendor": "Amlogic",
        "model": "A311D",
        "process_nm": "12 нм",
        "cpu": "6 ядер (4x Cortex-A73 @ 2.2 ГГц + 2x Cortex-A53 @ 1.8 ГГц) + 5.0 TOPS NPU",
        "gpu": "ARM Mali-G52 MP4",
        "features": "Версия S922X со встроенным нейроускорителем для AI-зрения"
    },

    # === ALLWINNER ===
    "h616": {
        "vendor": "Allwinner",
        "model": "H616",
        "process_nm": "28 нм",
        "cpu": "4x ARM Cortex-A53 @ до 1.5 ГГц",
        "gpu": "ARM Mali-G31 MP2",
        "features": "Популярный дешевый чип (Tanix TX6s, T95), сильный нагрев"
    },
    "h618": {
        "vendor": "Allwinner",
        "model": "H618",
        "process_nm": "28 нм",
        "cpu": "4x ARM Cortex-A53 @ до 1.5 ГГц",
        "gpu": "ARM Mali-G31 MP2",
        "features": "Ревизия H616 с поддержкой Android 12"
    },
    "h313": {
        "vendor": "Allwinner",
        "model": "H313",
        "process_nm": "28 нм",
        "cpu": "4x ARM Cortex-A53 @ до 1.35 ГГц",
        "gpu": "ARM Mali-G31 MP2",
        "features": "Урезанный сверхдешевый чип без гигабитного LAN"
    },

    # === ROCKCHIP ===
    "rk3588": {
        "vendor": "Rockchip",
        "model": "RK3588 / RK3588S",
        "process_nm": "8 нм (Samsung)",
        "cpu": "8 ядер (4x Cortex-A76 @ 2.4 ГГц + 4x Cortex-A55 @ 1.8 ГГц)",
        "gpu": "ARM Mali-G610 MP4 + 6.0 TOPS NPU",
        "features": "Топовый комбайн: 8K@60fps видео, PCIe 3.0, тянет локальные LLM"
    },
    "rk3566": {
        "vendor": "Rockchip",
        "model": "RK3566",
        "process_nm": "22 нм",
        "cpu": "4x ARM Cortex-A55 @ до 1.8 ГГц",
        "gpu": "ARM Mali-G52 2EE + 0.8 TOPS NPU",
        "features": "Энергоэффективный чип для читалок, ТВ-стиков и одноплатников"
    },
    "rk3399": {
        "vendor": "Rockchip",
        "model": "RK3399",
        "process_nm": "28 нм HKMG",
        "cpu": "6 ядер (2x Cortex-A72 @ 1.8 ГГц + 4x Cortex-A53 @ 1.4 ГГц)",
        "gpu": "ARM Mali-T860 MP4",
        "features": "Классика одноплатников и ТВ-боксов среднего уровня"
    },

    # === REALTEK (Телевизоры TCL, KIVI, Haier) ===
    "rtd1319": {
        "vendor": "Realtek",
        "model": "RTD1319",
        "process_nm": "12 нм",
        "cpu": "4x ARM Cortex-A55 @ 1.4 ГГц",
        "gpu": "ARM Mali-G31 MP2",
        "features": "Стандарт современных Smart TV с Google TV и AV1"
    },

    # === QUALCOMM SNAPDRAGON ===
    "sm6350": {
        "vendor": "Qualcomm",
        "model": "Snapdragon 690 5G (OnePlus Nord N10)",
        "process_nm": "8 нм (Samsung LPP)",
        "cpu": "8 ядер (2x Kryo 560 Gold Cortex-A77 @ 2.0 ГГц + 6x Silver A55 @ 1.7 ГГц)",
        "gpu": "Adreno 619L @ 565 МГц",
        "features": "Отличная однопоточная производительность, аппаратный ISP Spectra 355L"
    },
    "sm6375": {
        "vendor": "Qualcomm",
        "model": "Snapdragon 695 5G",
        "process_nm": "6 нм (TSMC N6)",
        "cpu": "8 ядер (2x Kryo 660 Gold Cortex-A78 @ 2.2 ГГц + 6x Silver A55 @ 1.7 ГГц)",
        "gpu": "Adreno 619",
        "features": "Холодный 6нм чип, высокая энергоэффективность"
    },
    "sm6225": {
        "vendor": "Qualcomm",
        "model": "Snapdragon 680 4G",
        "process_nm": "6 нм (TSMC N6)",
        "cpu": "8 ядер (4x Kryo 265 Gold Cortex-A73 @ 2.4 ГГц + 4x Silver A53 @ 1.9 ГГц)",
        "gpu": "Adreno 610",
        "features": "Популярен в планшетах и бюджетных смартфонах"
    },
    "msm8953": {
        "vendor": "Qualcomm",
        "model": "Snapdragon 625 (Redmi Note 4 Mido)",
        "process_nm": "14 нм (FinFET)",
        "cpu": "8x ARM Cortex-A53 @ 2.0 ГГц",
        "gpu": "Adreno 506",
        "features": "Легендарный энергоэффективный долгожитель 2016-2018 годов"
    },

    # === MEDIATEK ===
    "mt6797": {
        "vendor": "MediaTek",
        "model": "Helio X20 (Redmi Note 4 Nikel)",
        "process_nm": "20 нм (TSMC)",
        "cpu": "10 ядер Tri-Cluster (2x Cortex-A72 @ 2.1 ГГц + 4x A53 @ 1.85 ГГц + 4x A53 @ 1.4 ГГц)",
        "gpu": "ARM Mali-T880 MP4 @ 780 МГц",
        "features": "Первый в мире 10-ядерник, горячий нрав, высокая сырая вычислительная мощь"
    },
    "mt8695": {
        "vendor": "MediaTek",
        "model": "MT8695 (Amazon Fire TV Stick 4K)",
        "process_nm": "12 нм",
        "cpu": "4x ARM Cortex-A53 @ 1.7 ГГц",
        "gpu": "PowerVR GE8300",
        "features": "Штатный чип Amazon Fire TV, поддержка Dolby Vision и HDR10+"
    },
    "mt8696": {
        "vendor": "MediaTek",
        "model": "MT8696 (Fire TV Stick 4K Max)",
        "process_nm": "12 нм",
        "cpu": "4x ARM Cortex-A55 @ 1.8 ГГц",
        "gpu": "PowerVR GE9215 @ 750 МГц",
        "features": "Быстрый 12нм стик с Wi-Fi 6 и AV1"
    }
}

def identify_soc(platform_str: str, hardware_str: str, cpuinfo_str: str = "") -> dict:
    """
    Интеллектуальное сопоставление платформы устройства со справочником SoC.
    """
    raw_query = f"{platform_str} {hardware_str} {cpuinfo_str}".lower()
    
    # 1. Прямой поиск по ключам базы
    for key, data in SOC_DATABASE.items():
        if key in raw_query:
            return data
            
    # 2. Поиск по алиасам кодовых имен Amlogic
    if "sm1" in raw_query:
        return SOC_DATABASE["s905x3"]
    if "sc2" in raw_query:
        return SOC_DATABASE["s905x4"]
    if "u211" in raw_query:
        return SOC_DATABASE["s905x2"]
    if "g12b" in raw_query:
        return SOC_DATABASE["s922x"]
    if "gxm" in raw_query:
        return SOC_DATABASE["s912"]
    if "p212" in raw_query:
        return SOC_DATABASE["s905x"]
    if "p281" in raw_query:
        return SOC_DATABASE["s905w"]
        
    # 3. Общая эвристика для нераспознанных
    vendor = "Неизвестный вендор"
    if "amlogic" in raw_query or "meson" in raw_query:
        vendor = "Amlogic"
    elif "qcom" in raw_query or "qualcomm" in raw_query or "snapdragon" in raw_query:
        vendor = "Qualcomm Snapdragon"
    elif "mt" in raw_query or "mediatek" in raw_query or "helio" in raw_query:
        vendor = "MediaTek"
    elif "sunxi" in raw_query or "allwinner" in raw_query:
        vendor = "Allwinner"
    elif "rk" in raw_query or "rockchip" in raw_query:
        vendor = "Rockchip"
        
    return {
        "vendor": vendor,
        "model": platform_str or hardware_str or "Универсальный ARM-чипсет",
        "process_nm": "Техпроцесс не определен (нет в оффлайн-базе)",
        "cpu": "ARM архитектура (см. /proc/cpuinfo)",
        "gpu": "Определяется через SurfaceFlinger",
        "features": "Базовый набор инструкций"
    }

def decode_storage_manfid(manfid_hex_or_dec: str) -> str:
    """Декодирует CID manfid производителя eMMC/UFS."""
    clean = str(manfid_hex_or_dec).strip().lower()
    return MEMORY_MANUFACTURERS.get(clean, f"Неизвестный производитель ({clean})")
