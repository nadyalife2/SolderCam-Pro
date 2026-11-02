import re
import sys

TARGET_FILE = r"d:\для one plus nord n10\melvin_src\agent_orchestrator.py"

with open(TARGET_FILE, "r", encoding="utf-8") as f:
    content = f.read()

# 1. FIX THE JAVASCRIPT REGEX BUG IN executeVoiceOutput
# Old buggy line with (?i) that broke JavaScript engine:
buggy_js_regex = ".replace(/(?i)\\b(\\d+\\s+)?(коротк\\w+|язвительн\\w+|предложени\\w+|инструкци\\w+|строго\\s+1)\\b.*/g, '')"
fixed_js_regex = ".replace(/\\b(\\d+\\s+)?(коротк\\w+|язвительн\\w+|предложени\\w+|инструкци\\w+|строго\\s+1)\\b.*/gi, '')"

if buggy_js_regex in content:
    content = content.replace(buggy_js_regex, fixed_js_regex)
    print("Fixed JavaScript (?i) regex syntax error!")
else:
    print("Notice: buggy_js_regex not found by exact string, checking with regex search...")
    content = re.sub(
        r'\.replace\(/\(\?i\).*?/g,\s*\'\'\)',
        ".replace(/\\\\b(\\\\d+\\\\s+)?(коротк\\\\w+|язвительн\\\\w+|предложени\\\\w+|инструкци\\\\w+|строго\\\\s+1)\\\\b.*/gi, '')",
        content
    )

# 2. ADD SPEECH WATCHDOG IN speakWithLowPitch SO BOT NEVER GETS STUCK IN "ГОВОРИТ..."
old_speak_start = "function speakWithLowPitch(text) {"
watchdog_code = """function speakWithLowPitch(text) {
            let raw = text.trim();
            if (!raw) return;

            // Сброс предыдущего сторожевого таймера
            if (window.__speechWatchdog) clearTimeout(window.__speechWatchdog);

            isBotSpeaking = true;
            speechBuffer = [];
            preRollQueue = [];
            silenceCount = 0;
            maxRmsInPhrase = 0;

            // Сторожевой таймер безопасности (макс 10 секунд): размораживает микрофон при любом сбое
            window.__speechWatchdog = setTimeout(() => {
                if (isBotSpeaking) {
                    console.log('[Watchdog] Resetting stuck isBotSpeaking state');
                    onBotSpeechFinished();
                }
            }, 10000);"""

if old_speak_start in content:
    # replace only first occurrence in JS
    pos = content.find(old_speak_start)
    pos_brace = content.find("{", pos)
    # find where isBotSpeaking is set
    pos_speaking = content.find("isBotSpeaking = true;", pos)
    pos_end_block = content.find("vadIndicator.classList.remove('recording', 'dialogue-active');", pos)
    content = content[:pos] + watchdog_code + "\n\n            " + content[pos_end_block:]
    print("Speech safety watchdog installed!")

# 3. ADD "ПОЧЕМУ МОЛЧИШЬ" INTENT TO check_quips
quip_target = "if ('как' in m and any(w in m for w in ['дела', 'жизнь', 'поживаешь', 'настроение', 'оно', 'сам']))"
quip_replacement = """if any(w in m for w in ['почему молчишь', 'молчишь', 'ты тут', 'ты где', 'ответь', 'ты уснул', 'ты спишь', 'че молчишь']):
        if persona == "rick":
            return "*рыгает* Я не молчу, гений. Я просто решаю в уме уравнение квантовой телепортации, пока ты тупишь."
        else:
            return "Я не молчу, мешок с костями. Я просто экономлю кремниевые ресурсы на твоих бессмысленных фразах."

    if ('как' in m and any(w in m for w in ['дела', 'жизнь', 'поживаешь', 'настроение', 'оно', 'сам']))"""

if quip_target in content:
    content = content.replace(quip_target, quip_replacement, 1)
    print("Silence & 'почему молчишь' intent added to check_quips!")

# 4. FIX LLM PAYLOAD: ADD repeat_penalty & FILTER HALLUCINATED NUMBERS
llm_payload_target = '"temperature": 0.65 if persona == "rick" else 0.55,'
llm_payload_replacement = """"temperature": 0.60 if persona == "rick" else 0.48,
        "repeat_penalty": 1.22,
        "repeat_last_n": 64,"""

if llm_payload_target in content:
    content = content.replace(llm_payload_target, llm_payload_replacement, 1)
    print("Llama-server repeat_penalty added!")

# 5. SANITIZE HALLUCINATED LONG NUMBERS IN PYTHON
post_llm_target = "full_ans = re.sub(r'<\\|.*?\\|>', '', full_ans).strip()"
post_llm_replacement = """full_ans = re.sub(r'<\\|.*?\\|>', '', full_ans).strip()
        # Удаление галлюцинированных длинных чисел (например 8761834172769875744)
        full_ans = re.sub(r'\\b\\d{4,}\\b', '', full_ans)
        # Удаление утечек инструкций промпта
        full_ans = re.sub(r'(?i)\\b(\\d+\\s+)?(коротк\\w+|язвительн\\w+|предложени\\w+|инструкци\\w+|строго\\s+1)\\b.*', '', full_ans)
        # Исправление висящих запятых и пробелов перед знаками препинания
        full_ans = re.sub(r',\\s*,', ',', full_ans)
        full_ans = re.sub(r'\\s+([.,!?:;])', r'\\1', full_ans).strip()"""

if post_llm_target in content:
    content = content.replace(post_llm_target, post_llm_replacement, 1)
    print("LLM hallucinated number and leak sanitizer installed!")

with open(TARGET_FILE, "w", encoding="utf-8") as f:
    f.write(content)

print("Patch applied cleanly to agent_orchestrator.py!")
