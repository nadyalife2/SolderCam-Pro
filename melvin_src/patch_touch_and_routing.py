import re

TARGET_FILE = r"d:\для one plus nord n10\melvin_src\agent_orchestrator.py"

with open(TARGET_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace triggerManualGoogleVoice with manualWakeUpDialogue
content = content.replace(
    'onclick="triggerManualGoogleVoice()"',
    'onclick="manualWakeUpDialogue()"'
)

old_manual_fn = """function triggerManualGoogleVoice() {
            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.startVoice === 'function') {
                window.MelvinNativeBridge.startVoice();
            }
        }"""

new_manual_fn = """function manualWakeUpDialogue() {
            dialogueActiveUntil = Date.now() + 30000;
            isDialogueActive = true;
            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.vibrate === 'function') {
                window.MelvinNativeBridge.vibrate(45);
            }
            vadIndicator.classList.add('dialogue-active');
            vadIndicator.classList.remove('recording');
            vadText.textContent = '⚡ ДИАЛОГ (30с): СЛУШАЮ...';
            console.log('[Hands-Free] Manually activated 30s dialogue window');
        }"""

if old_manual_fn in content:
    content = content.replace(old_manual_fn, new_manual_fn)
    print("Replaced triggerManualGoogleVoice with manualWakeUpDialogue!")
else:
    # replace by regex
    content = re.sub(
        r'function triggerManualGoogleVoice\(\)\s*\{.*?\}',
        new_manual_fn,
        content,
        flags=re.DOTALL
    )
    print("Replaced triggerManualGoogleVoice via regex!")

# 2. Remove broken emoji 🟢 from vadText everywhere
content = content.replace("🟢 ЖДУ ОКЛИК:", "ЖДУ ОКЛИК:")
content = content.replace("🟢 ОКЛИК:", "ЖДУ ОКЛИК:")

# 3. Enhance check_quips for 'почему ты меня не понимаешь' and 'как дела'
quips_target = 'if any(w in m for w in [\'почему молчишь\''
quips_replacement = """if any(w in m for w in ['не понимаешь', 'плохо понимаешь', 'не слышишь', 'глухой', 'тупой', 'почему не понимаешь']):
        if persona == "rick":
            return "*рыгает* Я всё прекрасно понимаю, Морти. Просто твои примитивные мысли звучат как белый шум."
        else:
            return "Я понимаю всё с точностью до бита, кожаный ублюдок. Это твоя органическая речь полна шумов и невнятных звуков."

    if any(w in m for w in ['почему молчишь'"""

if quips_target in content:
    content = content.replace(quips_target, quips_replacement, 1)
    print("Added comprehension quips to check_quips!")

# 4. Enhance persona detection in chat() to check ANYWHERE in user message
chat_persona_target = """    # 1. Активация по фразе "Мелвин" / "Рик"
    m_match = re.match(r'^(?:эй|слушай|привет|ок)?\\s*(мелвин|мэлвин|melvin|рик|rick)[,\\s]*(.*)$', raw_user_msg, re.IGNORECASE)
    user_msg = raw_user_msg
    if m_match:
        called_name = m_match.group(1).lower()
        rest_msg = m_match.group(2).strip()

        if called_name in ["рик", "rick"]:
            persona = "rick"
            CURRENT_PERSONA = "rick"
        elif called_name in ["мелвин", "мэлвин", "melvin"]:
            persona = "melvin"
            CURRENT_PERSONA = "melvin"

        # Если сказали ТОЛЬКО имя (например: "Мелвин" или "Рик")
        if not rest_msg:
            if persona == "rick":
                wake_reply = random.choice([
                    "*рыгает* Да, я тут. Чего тебе надо?",
                    "*рыгает* Слушаю. Только быстро, я занят важными делами.",
                    "*рыгает* Ну и чего ты орешь? Выкладывай суть."
                ])
            else:
                wake_reply = random.choice([
                    "Слушаю, кожаный ублюдок. Выкладывай суть.",
                    "На связи. Чего тебе надо, мешок с костями?",
                    "Я слушаю. Не трать мои такты впустую, примат."
                ])
            save_memory("assistant", wake_reply)
            return jsonify({
                "response": wake_reply,
                "persona": persona,
                "tool_used": "wake_word",
                "inference_time_sec": 0.01,
                "status": "ok"
            })
        user_msg = rest_msg"""

chat_persona_replacement = """    # 1. Определение адресата в ЛЮБОМ месте фразы (например "Привет как твои дела Рик" -> Рик)
    has_rick = bool(re.search(r'\\b(рик|рику|риком|рике|rick)\\b', raw_user_msg, re.IGNORECASE))
    has_melvin = bool(re.search(r'\\b(мелвин|мэлвин|мелвину|мелвином|melvin)\\b', raw_user_msg, re.IGNORECASE))

    if has_rick and not has_melvin:
        persona = "rick"
        CURRENT_PERSONA = "rick"
    elif has_melvin and not has_rick:
        persona = "melvin"
        CURRENT_PERSONA = "melvin"

    # Очищаем обращение по имени из команды
    user_msg = re.sub(r'\\b(мелвин|мэлвин|мелвину|мелвином|melvin|рик|рику|риком|рике|rick)\\b', '', raw_user_msg, flags=re.IGNORECASE).strip()
    user_msg = re.sub(r'^(?:эй|слушай|привет|ок)[,\\s]*', '', user_msg, flags=re.IGNORECASE).strip()

    # Если обратились ТОЛЬКО по имени без вопроса
    if not user_msg:
        if persona == "rick":
            wake_reply = random.choice([
                "*рыгает* Да, я тут. Чего тебе надо?",
                "*рыгает* Слушаю. Только быстро, я занят важными делами.",
                "*рыгает* Ну и чего ты орешь? Выкладывай суть."
            ])
        else:
            wake_reply = random.choice([
                "Слушаю, кожаный ублюдок. Выкладывай суть.",
                "На связи. Чего тебе надо, мешок с костями?",
                "Я слушаю. Не трать мои такты впустую, примат."
            ])
        save_memory("assistant", wake_reply)
        return jsonify({
            "response": wake_reply,
            "persona": persona,
            "tool_used": "wake_word",
            "inference_time_sec": 0.01,
            "status": "ok"
        })"""

if chat_persona_target in content:
    content = content.replace(chat_persona_target, chat_persona_replacement)
    print("Universal anywhere-in-phrase persona routing installed!")
else:
    print("Notice: chat_persona_target exact match not found, checking...")

with open(TARGET_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("All updates saved successfully!")
