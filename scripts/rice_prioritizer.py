#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RICE Feature Prioritization Tool for Triad-Omni & SolderCam Pro
Formula: RICE = (Reach * Impact * Confidence) / Effort
"""

import sys
import json
from typing import List, Dict

def calculate_rice(features: List[Dict]) -> List[Dict]:
    scored = []
    for f in features:
        name = f.get("name", "Unnamed")
        reach = float(f.get("reach", 100))
        # Impact: 3 = Massive, 2 = High, 1 = Medium, 0.5 = Low, 0.25 = Minimal
        impact = float(f.get("impact", 1.0))
        # Confidence: 1.0 (100%), 0.8 (80%), 0.5 (50%)
        conf = float(f.get("confidence", 0.8))
        # Effort: person-weeks / days
        effort = max(0.1, float(f.get("effort", 1.0)))
        
        score = (reach * impact * conf) / effort
        scored.append({
            "name": name,
            "reach": reach,
            "impact": impact,
            "confidence": f"{int(conf*100)}%",
            "effort": effort,
            "rice_score": round(score, 1),
            "tier": "🔥 P0 (Immediate)" if score >= 1000 else ("⚡ P1 (High)" if score >= 300 else "⏳ P2 (Backlog)")
        })
    scored.sort(key=lambda x: x["rice_score"], reverse=True)
    return scored

def main():
    sample = [
        {"name": "Прямой байпас батареи в SolderCam Pro (sysfs)", "reach": 1500, "impact": 3.0, "confidence": 1.0, "effort": 1.0},
        {"name": "Термо-оверлей NTC 60 FPS на видоискателе (Camera2)", "reach": 2000, "impact": 2.5, "confidence": 0.9, "effort": 2.0},
        {"name": "Поддержка внешних USB тепловизоров (UVC)", "reach": 800, "impact": 3.0, "confidence": 0.7, "effort": 4.0},
        {"name": "Экспорт JSON-LD Schema.org для всех статей кластера", "reach": 5000, "impact": 2.0, "confidence": 1.0, "effort": 0.5},
        {"name": "Анимация смены темной темы в Master HUD", "reach": 400, "impact": 0.5, "confidence": 0.8, "effort": 1.5}
    ]
    results = calculate_rice(sample)
    print(f"{'Рейтинг':<6} | {'Фича':<50} | {'Score':<8} | {'Приоритет'}")
    print("-" * 85)
    for i, r in enumerate(results, 1):
        print(f"#{i:<5} | {r['name']:<50} | {r['rice_score']:<8} | {r['tier']}")

if __name__ == "__main__":
    main()
