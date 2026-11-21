#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Triad-Omni App Icon Generator (ui-design-system compliant)
Генерирует официальные иконки приложения по стандарту Industrial OLED Cyberdeck:
- 512x512 (Google Play / High-Res Master)
- 192x192 (xxxhdpi App Launcher)
- 192x192 Round (Adaptive Round Icon)
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE_DIR = Path(__file__).resolve().parent.parent
OUT_512 = BASE_DIR / "TriadOmni_App_Icon.png"
OUT_192 = BASE_DIR / "ic_launcher_192.png"
OUT_ROUND = BASE_DIR / "ic_launcher_round.png"

# Токены дизайн-системы (Industrial OLED Cyberdeck)
COLOR_BG_DARK = (9, 13, 22, 255)       # #090d16
COLOR_SURFACE = (17, 24, 39, 255)      # #111827
COLOR_CYAN = (0, 255, 204, 255)        # #00ffcc
COLOR_EMERALD = (0, 255, 136, 255)     # #00ff88
COLOR_GOLD = (255, 215, 0, 255)        # #ffd700
COLOR_BLUE = (0, 113, 227, 255)        # #0071e3
COLOR_TEXT_WHITE = (243, 244, 246, 255)# #f3f4f6

def draw_squircle(draw, bounds, radius, fill, outline, width=1):
    x0, y0, x1, y1 = bounds
    draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=fill, outline=outline, width=width)

def generate_master_icon(size=512, is_round=False):
    # Создаем холст RGBA
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    scale = size / 512.0

    # 1. Фоновая геометрия
    if is_round:
        draw.ellipse([8 * scale, 8 * scale, (512 - 8) * scale, (512 - 8) * scale], 
                     fill=COLOR_BG_DARK, outline=COLOR_CYAN, width=int(4 * scale))
    else:
        draw_squircle(draw, [12 * scale, 12 * scale, (512 - 12) * scale, (512 - 12) * scale], 
                      radius=int(112 * scale), fill=COLOR_BG_DARK, outline=COLOR_CYAN, width=int(4 * scale))

    # Слой свечения
    glow_layer = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    # 2. Триада связей (Треугольник)
    p_apex = (256 * scale, 120 * scale)    # Node-1 Mi 10T (Snapdragon 865)
    p_right = (384 * scale, 350 * scale)   # Node-2 Nord N10 (Snapdragon 690)
    p_left = (128 * scale, 350 * scale)    # Node-3 Redmi Note 4 (Snapdragon 625)

    glow_draw.line([p_apex, p_right, p_left, p_apex], fill=(0, 255, 204, 90), width=int(3 * scale))

    # 3. Символ Омега (Ω)
    cx, cy = 256 * scale, 245 * scale
    r_outer = 95 * scale
    r_inner = 65 * scale

    # Рисуем дугу омеги
    arc_box = [cx - r_outer, cy - r_outer, cx + r_outer, cy + r_outer]
    glow_draw.arc(arc_box, start=35, end=145, fill=COLOR_CYAN, width=int(16 * scale))

    # Лапки омеги
    foot_y = cy + 62 * scale
    glow_draw.line([(cx - 72 * scale, foot_y), (cx - 110 * scale, foot_y)], fill=COLOR_CYAN, width=int(14 * scale))
    glow_draw.line([(cx + 72 * scale, foot_y), (cx + 110 * scale, foot_y)], fill=COLOR_CYAN, width=int(14 * scale))

    # Внутреннее квантовое ядро
    glow_draw.ellipse([cx - 26 * scale, cy - 26 * scale, cx + 26 * scale, cy + 26 * scale], 
                      fill=(17, 24, 39, 230), outline=COLOR_CYAN, width=int(3 * scale))
    glow_draw.ellipse([cx - 12 * scale, cy - 12 * scale, cx + 12 * scale, cy + 12 * scale], 
                      fill=COLOR_CYAN)
    glow_draw.ellipse([cx - 4 * scale, cy - 4 * scale, cx + 4 * scale, cy + 4 * scale], 
                      fill=COLOR_TEXT_WHITE)

    # 4. Узлы Триады с индивидуальной цветовой семантикой
    def draw_node(center, outer_col, core_col, name=""):
        gx, gy = center
        # Внешнее свечение
        glow_draw.ellipse([gx - 26 * scale, gy - 26 * scale, gx + 26 * scale, gy + 26 * scale], 
                          fill=(outer_col[0], outer_col[1], outer_col[2], 80))
        # Кольцо
        glow_draw.ellipse([gx - 18 * scale, gy - 18 * scale, gx + 18 * scale, gy + 18 * scale], 
                          fill=COLOR_BG_DARK, outline=core_col, width=int(3 * scale))
        # Центр
        glow_draw.ellipse([gx - 8 * scale, gy - 8 * scale, gx + 8 * scale, gy + 8 * scale], 
                          fill=core_col)
        glow_draw.ellipse([gx - 3 * scale, gy - 3 * scale, gx + 3 * scale, gy + 3 * scale], 
                          fill=COLOR_TEXT_WHITE)

    # Node 1: Mi 10T 5G (Apex - Gold Prime)
    draw_node(p_apex, COLOR_GOLD, COLOR_GOLD)
    # Node 2: Nord N10 5G (Right - Cyan Reflex)
    draw_node(p_right, COLOR_CYAN, COLOR_CYAN)
    # Node 3: Redmi Note 4 (Left - Emerald Power)
    draw_node(p_left, COLOR_EMERALD, COLOR_EMERALD)

    # 5. Текст TRIAD OMNI
    try:
        font_large = ImageFont.truetype("arialbd.ttf", int(26 * scale))
        font_small = ImageFont.truetype("consola.ttf", int(13 * scale))
    except Exception:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    glow_draw.text((256 * scale, 422 * scale), "TRIAD OMNI", font=font_large, fill=COLOR_TEXT_WHITE, anchor="mm")
    glow_draw.text((256 * scale, 452 * scale), "EDGE AI CLUSTER", font=font_small, fill=COLOR_CYAN, anchor="mm")

    # Применяем легкий фильтр свечения
    blurred_glow = glow_layer.filter(ImageFilter.GaussianBlur(radius=2 * scale))
    
    # Композитинг
    final_img = Image.alpha_composite(img, blurred_glow)
    final_img = Image.alpha_composite(final_img, glow_layer)
    return final_img

def main():
    print("🎨 Генерация официальных иконок Triad-Omni...")
    
    # 1. Master 512x512
    icon_512 = generate_master_icon(512, is_round=False)
    icon_512.save(OUT_512, "PNG")
    print(f"✅ Сохранено: {OUT_512} ({OUT_512.stat().st_size / 1024:.1f} KB)")

    # 2. App Launcher 192x192
    icon_192 = generate_master_icon(192, is_round=False)
    icon_192.save(OUT_192, "PNG")
    print(f"✅ Сохранено: {OUT_192} ({OUT_192.stat().st_size / 1024:.1f} KB)")

    # 3. Round Adaptive 192x192
    icon_round = generate_master_icon(192, is_round=True)
    icon_round.save(OUT_ROUND, "PNG")
    print(f"✅ Сохранено: {OUT_ROUND} ({OUT_ROUND.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    main()
