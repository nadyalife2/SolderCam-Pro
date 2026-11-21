---
name: onboarding-cro
description: Conversion rate optimization for user onboarding, first-run user experience (FTUE), friction point audits, empty states, and accelerating time-to-value (AHA moment) for developer tools and mobile apps.
version: 1.0.0
---

# Onboarding CRO & First-Run User Experience (FTUE)

Оптимизация пути пользователя от скачивания до первого успешного запуска (Time-to-Value < 60 секунд).

## 3 правила снижения трения:
1. **Zero-Config First Run:**
   - При первом запуске приложение или дашборд не требует заполнения настроек — сразу стартует с безопасными дефолтными параметрами (автоопределение сенсора камеры, дефолтный порт `:8000`).
2. **Мгновенный «AHA-момент»:**
   - Пользователь должен увидеть результат в первые 10 секунд: живой график температуры батареи или зеленый огонек светофора ноды.
3. **Прогрессивное раскрытие сложности:**
   - Сложные параметры (sysfs-ноды, ручные флаги `llama.cpp`, адреса шлюзов) скрыты в выпадающую секцию «Продвинутые настройки» и не пугают новичка на первом экране.
