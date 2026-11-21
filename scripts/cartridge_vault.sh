#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# Triad-Omni Cartridge Vault v2.1 (On-Device Rolling Cache & Web Manifest Engine)
# Управление пулом версий LoRA-картриджей прямо в памяти Xiaomi Mi 10T 5G.
# Автоматически синхронизирует web_ui/cartridges/manifest.json для веб-HUD.
# 100% автономно на чистом bash/busybox без сторонних зависимостей.
# ==============================================================================

HOME_DIR="/data/data/com.termux/files/home"
CARTRIDGES_DIR="$HOME_DIR/cartridges"
WEB_CARTRIDGES_DIR="$HOME_DIR/web_ui/cartridges"
MODELS_DIR="$HOME_DIR/models"
ACTIVE_CONFIG="$HOME_DIR/config/active_cartridge.json"
MANIFEST_FILE="$WEB_CARTRIDGES_DIR/manifest.json"

# Настройки квоты памяти на телефоне
MAX_CACHE_MB=${MAX_CACHE_MB:-1024}       # Лимит квоты памяти: 1024 МБ (1 ГБ)
MAX_VERSIONS_PER_SLUG=${MAX_VERSIONS:-5} # До 5 последних версий для каждого типа

mkdir -p "$CARTRIDGES_DIR" "$WEB_CARTRIDGES_DIR" "$MODELS_DIR" "$HOME_DIR/config"

# Текущий активный картридж
get_active_tag() {
    if [ -f "$ACTIVE_CONFIG" ]; then
        grep -o '"build_tag": "[^"]*' "$ACTIVE_CONFIG" 2>/dev/null | cut -d'"' -f4
    else
        echo "none"
    fi
}

# Генерация manifest.json для Web UI
generate_manifest() {
    active_tag=$(get_active_tag)
    total_kb=$(du -s "$CARTRIDGES_DIR" 2>/dev/null | awk '{print $1}')
    total_mb=$(awk "BEGIN {printf \"%.1f\", $total_kb/1024}")
    percent=$(awk "BEGIN {printf \"%.1f\", ($total_mb/$MAX_CACHE_MB)*100}")

    cat <<EOF > "$MANIFEST_FILE"
{
  "quota_max_mb": $MAX_CACHE_MB,
  "quota_used_mb": $total_mb,
  "quota_percent": $percent,
  "active_tag": "$active_tag",
  "cartridges": [
EOF

    first=1
    for dir in "$CARTRIDGES_DIR"/*; do
        if [ -d "$dir" ]; then
            bname=$(basename "$dir")
            size_kb=$(du -s "$dir" 2>/dev/null | awk '{print $1}')
            size_mb=$(awk "BEGIN {printf \"%.1f\", $size_kb/1024}")
            
            is_active=false
            if [ "$bname" = "$active_tag" ] || [ -f "$dir/active.lock" ]; then
                is_active=true
            fi
            
            v_slug="triad-omni-persona"
            v_ver="v1.0"
            v_desc="LoRA-картридж Triad-Omni"
            
            if [ -f "$dir/card.json" ]; then
                read_slug=$(grep -o '"slug": "[^"]*' "$dir/card.json" | cut -d'"' -f4)
                read_ver=$(grep -o '"version": "[^"]*' "$dir/card.json" | cut -d'"' -f4)
                read_desc=$(grep -o '"description": "[^"]*' "$dir/card.json" | cut -d'"' -f4)
                [ -n "$read_slug" ] && v_slug="$read_slug"
                [ -n "$read_ver" ] && v_ver="$read_ver"
                [ -n "$read_desc" ] && v_desc="$read_desc"
            fi
            
            # Копируем файлы в web_ui/cartridges для прямой отдачи через HTTP
            mkdir -p "$WEB_CARTRIDGES_DIR/$bname"
            cp -u "$dir"/* "$WEB_CARTRIDGES_DIR/$bname/" 2>/dev/null

            if [ $first -eq 0 ]; then
                echo "    ," >> "$MANIFEST_FILE"
            fi
            first=0

            cat <<EOF >> "$MANIFEST_FILE"
    {
      "tag": "$bname",
      "slug": "$v_slug",
      "version": "$v_ver",
      "size_mb": $size_mb,
      "is_active": $is_active,
      "description": "$v_desc",
      "adapter_url": "/cartridges/$bname/adapter.gguf",
      "card_url": "/cartridges/$bname/card.json"
    }
EOF
        fi
    done

    cat <<EOF >> "$MANIFEST_FILE"
  ]
}
EOF
}

# Список всех версий
list_vault() {
    active_tag=$(get_active_tag)
    echo "================================================================="
    echo "🗄️  Triad-Omni Cartridge Vault // Пул версий в памяти телефона"
    echo "================================================================="
    
    total_kb=0
    count=0
    
    for dir in "$CARTRIDGES_DIR"/*; do
        if [ -d "$dir" ]; then
            bname=$(basename "$dir")
            size_kb=$(du -s "$dir" 2>/dev/null | awk '{print $1}')
            size_mb=$(awk "BEGIN {printf \"%.1f\", $size_kb/1024}")
            total_kb=$((total_kb + size_kb))
            count=$((count + 1))
            
            status="[В КЭШЕ]"
            if [ "$bname" = "$active_tag" ] || [ -f "$dir/active.lock" ]; then
                status="[АКТИВЕН 🟢]"
            fi
            
            v_info=""
            if [ -f "$dir/card.json" ]; then
                v_slug=$(grep -o '"slug": "[^"]*' "$dir/card.json" | cut -d'"' -f4)
                v_ver=$(grep -o '"version": "[^"]*' "$dir/card.json" | cut -d'"' -f4)
                v_info="($v_slug @ $v_ver)"
            fi
            
            printf "  %-32s %-12s %-10s %s\n" "$bname" "$size_mb MB" "$status" "$v_info"
        fi
    done
    
    total_mb=$(awk "BEGIN {printf \"%.1f\", $total_kb/1024}")
    percent=$(awk "BEGIN {printf \"%.1f\", ($total_mb/$MAX_CACHE_MB)*100}")
    
    echo "-----------------------------------------------------------------"
    echo "📊 Всего версий в памяти: $count"
    echo "💾 Занято под картриджи:   $total_mb МБ / $MAX_CACHE_MB МБ ($percent%)"
    echo "================================================================="
    
    generate_manifest
}

# Активация конкретной версии картриджа
activate_vault() {
    tag="$1"
    if [ -z "$tag" ]; then
        echo "❌ Укажите имя версии (папки) из $CARTRIDGES_DIR"
        exit 1
    fi
    
    target_dir="$CARTRIDGES_DIR/$tag"
    if [ ! -d "$target_dir" ]; then
        echo "❌ Папка $target_dir не найдена!"
        exit 1
    fi
    
    adapter=$(find "$target_dir" -name "*.gguf" | head -n 1)
    if [ -z "$adapter" ]; then
        echo "❌ В папке $target_dir нет файла .gguf!"
        exit 1
    fi
    
    echo "⚡ Активируем картридж: $tag..."
    cp -f "$adapter" "$MODELS_DIR/adapter.gguf"
    if [ -f "$target_dir/card.json" ]; then
        cp -f "$target_dir/card.json" "$MODELS_DIR/card.json"
    fi
    
    # Снимаем старые замки активности
    find "$CARTRIDGES_DIR" -name "active.lock" -delete 2>/dev/null
    touch "$target_dir/active.lock"
    
    # Записываем в active_cartridge.json
    echo "{\"active\": true, \"build_tag\": \"$tag\", \"active_path\": \"$target_dir\", \"scale\": 1.0}" > "$ACTIVE_CONFIG"
    
    echo "✅ Картридж '$tag' успешно активирован в $MODELS_DIR/adapter.gguf!"
    generate_manifest
}

# Очистка по квоте (LRU ротация)
prune_vault() {
    echo "🧹 Проверка квоты памяти картриджей (лимит $MAX_CACHE_MB МБ)..."
    active_tag=$(get_active_tag)
    
    total_kb=$(du -s "$CARTRIDGES_DIR" 2>/dev/null | awk '{print $1}')
    total_mb=$((total_kb / 1024))
    
    if [ "$total_mb" -le "$MAX_CACHE_MB" ]; then
        echo "✅ Объем в норме: $total_mb МБ <= $MAX_CACHE_MB МБ. Очистка не требуется."
        generate_manifest
        return 0
    fi
    
    echo "⚠️ Превышен лимит памяти ($total_mb МБ > $MAX_CACHE_MB МБ)! Начинаем LRU-ротацию..."
    
    find "$CARTRIDGES_DIR" -mindepth 1 -maxdepth 1 -type d | while read -r dir; do
        bname=$(basename "$dir")
        if [ "$bname" != "$active_tag" ] && [ ! -f "$dir/active.lock" ]; then
            stat -c "%Y %n" "$dir" 2>/dev/null || stat -f "%m %N" "$dir" 2>/dev/null
        fi
    done | sort -n | while read -r mtime dir; do
        current_kb=$(du -s "$CARTRIDGES_DIR" 2>/dev/null | awk '{print $1}')
        current_mb=$((current_kb / 1024))
        if [ "$current_mb" -le "$MAX_CACHE_MB" ]; then
            break
        fi
        
        bname=$(basename "$dir")
        echo "  🗑️ Удаляем старую архивную версию: $bname..."
        rm -rf "$dir"
        rm -rf "$WEB_CARTRIDGES_DIR/$bname"
    done
    
    final_kb=$(du -s "$CARTRIDGES_DIR" 2>/dev/null | awk '{print $1}')
    final_mb=$((final_kb / 1024))
    echo "🎉 Очистка завершена. Текущий объем: $final_mb МБ / $MAX_CACHE_MB МБ."
    generate_manifest
}

# Распаковка и установка архива в хранилище
install_zip() {
    zip_file="$1"
    if [ ! -f "$zip_file" ]; then
        echo "❌ Файл $zip_file не найден!"
        exit 1
    fi
    
    fname=$(basename "$zip_file" .omni.zip)
    fname=$(basename "$fname" .zip)
    target_dir="$CARTRIDGES_DIR/$fname"
    
    echo "📦 Распаковка $zip_file в $target_dir..."
    mkdir -p "$target_dir"
    unzip -q -o "$zip_file" -d "$target_dir"
    
    activate_vault "$fname"
    prune_vault
}

# Скачивание картриджа по ссылке из облака (Яндекс / Google / Direct)
download_cloud() {
    url="$1"
    if [ -z "$url" ]; then
        echo "❌ Укажите ссылку на картридж!"
        exit 1
    fi
    
    echo "🌐 Загрузка картриджа из облака: $url..."
    tmp_file="$HOME_DIR/cartridge_download.zip"
    rm -f "$tmp_file"
    
    if echo "$url" | grep -qE "disk.yandex|yadi.sk"; then
        api_url="https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key=${url}"
        direct_url=$(curl -sL "$api_url" | grep -o '"href": "[^"]*' | cut -d'"' -f4)
        if [ -n "$direct_url" ]; then
            curl -sL "$direct_url" -o "$tmp_file"
        else
            echo "❌ Не удалось получить прямую ссылку с Яндекс Диска!"
            exit 1
        fi
    else
        curl -sL "$url" -o "$tmp_file"
    fi
    
    if [ -f "$tmp_file" ] && [ -s "$tmp_file" ]; then
        echo "✅ Картридж скачан ($(du -h "$tmp_file" | cut -f1))! Устанавливаем в Vault..."
        install_zip "$tmp_file"
        rm -f "$tmp_file"
    else
        echo "❌ Ошибка скачивания файла из облака!"
        exit 1
    fi
}

case "$1" in
    list|"")
        list_vault
        ;;
    activate)
        activate_vault "$2"
        ;;
    prune)
        prune_vault
        ;;
    install)
        install_zip "$2"
        ;;
    download)
        download_cloud "$2"
        ;;
    manifest)
        generate_manifest
        ;;
    *)
        echo "Использование: $0 {list|activate <tag>|prune|install <zip>|download <url>|manifest}"
        ;;
esac
