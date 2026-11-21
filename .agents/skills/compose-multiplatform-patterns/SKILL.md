---
name: compose-multiplatform-patterns
description: Idiomatic Jetpack Compose and Compose Multiplatform patterns for Android apps (such as com.soldercam.pro). Covers state hoisting, recomposition optimization, touch target ergonomics (thumb zone >= 48dp), zero-lag Camera2 viewfinder overlays, and lifecycle-aware coroutines.
version: 1.0.0
---

# Jetpack Compose & Compose Multiplatform Architecture

Руководство по созданию высокопроизводительных нативных интерфейсов на Jetpack Compose для мобильных инструментов реального времени (камеры, термометрия, аппаратный мониторинг).

## 1. Оптимизация производительности и рекомпозиций

При работе с видоискателем камеры (30-60 fps) или живой телеметрией процессора любая лишняя рекомпозиция вызывает микро-фризы и нагрев чипа:

1. **Использование `derivedStateOf` для частых значений:**
   ```kotlin
   // ПЛОХО: рекомпозирует весь экран при каждом изменении температуры на 0.1°C
   val isOverheating = batteryTemp > 450

   // ХОРОШО: рекомпозирует только при смене логического состояния булева флага
   val isOverheating by remember { derivedStateOf { batteryTemp > 450 } }
   ```

2. **Стабильные классы и `@Immutable` аннотации:**
   - Все UI-состояния (UiState) упаковывать в неизменяемые `data class`:
   ```kotlin
   @Immutable
   data class TelemetryState(
       val voltageMv: Int = 4180,
       val tempC: Float = 34.0f,
       val bypassActive: Boolean = true,
       val currentMa: Int = 0
   )
   ```

3. **`Modifier.drawBehind` вместо создания лишних View:**
   - Для отрисовки сетки пайки, перекрестия и тепловой гистограммы использовать `Modifier.drawBehind { ... }` на Canvas, исключая создание тяжелых элементов макета.

---

## 2. Мобильная эргономика (Thumb Zone & Touch Targets)

1. **Минимальный тач-таргет — 48×48 dp:**
   - Каждая кнопка управления экспозицией, зумом и переключением датчиков должна иметь кликабельную область не менее 48dp:
   ```kotlin
   Modifier
       .size(48.dp)
       .clickable(
           interactionSource = remember { MutableInteractionSource() },
           indication = ripple(bounded = false, radius = 24.dp)
       ) { /* действие */ }
   ```
2. **Низовое размещение контролов (One-Handed Operation):**
   - Все интерактивные элементы располагаются в нижней трети экрана (зона досягаемости большого пальца).
   - В верхней трети — только пассивная индикация (статус FPS, заряд, температура NTC).

---

## 3. Интеграция с Camera2 API и Coroutine Lifecycle

1. Использовать `rememberCoroutineScope` и `flowWithLifecycle` для получения кадров и телеметрии.
2. При сворачивании приложения видоискатель обязан немедленно отпускать сессию камеры `cameraDevice.close()` для сохранения ресурса PMIC и исключения фонового дренажа батареи.
