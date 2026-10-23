---
name: mobile-android-design
description: Master Material Design 3 and Jetpack Compose patterns for building native Android apps. Use when designing Android interfaces, implementing Compose UI, or following Google's Material Design guidelines.
---

# Android Mobile Design

Master Material Design 3 (Material You) and Jetpack Compose to build modern, adaptive Android applications that integrate seamlessly with the Android ecosystem.

## When to Use This Skill

- Designing Android app interfaces following Material Design 3
- Building Jetpack Compose / ViewBinding UI and layouts
- Implementing Android navigation patterns
- Creating adaptive layouts for phones, tablets, and landscape camera interfaces
- Using Material 3 theming with dynamic colors and dark themes
- Building accessible Android interfaces (touch targets >= 48dp, contrast)
- Implementing Android-specific gestures and viewfinder interactions
- Designing for different screen configurations and orientations

## Best Practices

1. **Use Material Theme**: Access colors via `MaterialTheme.colorScheme` or Material3 themes for automatic dark mode support.
2. **Support Dynamic Color**: Enable dynamic color on Android 12+ for personalization.
3. **Adaptive Layouts**: Handle both portrait and landscape orientation cleanly.
4. **Content Descriptions**: Add `contentDescription` to all interactive buttons and camera controls.
5. **Touch Targets**: Minimum 48dp touch targets for accessibility and one-handed operation.
6. **State Hoisting**: Keep UI components decoupled from business logic and sensor streams.
7. **Ergonomics**: Place primary action controls (shutter, zoom toggle, focus slider) within natural thumb reach.

## Common Issues & Solutions

- **Touch Target too small**: Sliders and camera toggle buttons must have at least 48x48dp interactive padding.
- **Orientation Glitches**: Lock viewfinder orientation or handle `configChanges="orientation|screenSize"` to prevent CameraDevice disconnects.
- **High CPU usage in UI**: Decouple 60 FPS Camera2 preview texture updates from telemetry text rendering (throttle to 1–2 Hz).
