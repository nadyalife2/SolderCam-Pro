with open("melvin_src/agent_orchestrator.py", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Добавляем импорты
old_import = "import phone_tools"
new_import = "import phone_tools\nimport rick_voice\nimport knowledge_rag\nimport web_tools"
assert old_import in content, "old_import not found"
content = content.replace(old_import, new_import, 1)

# 2. Инициализация RAG в init_db
old_init = "def init_db():\n    conn = sqlite3.connect(DB_PATH)"
new_init = "def init_db():\n    try:\n        knowledge_rag.init_knowledge_db()\n    except Exception as e:\n        print(f'RAG init notice: {e}')\n    conn = sqlite3.connect(DB_PATH)"
assert old_init in content, "old_init not found"
content = content.replace(old_init, new_init, 1)

# 3. Добавляем эндпоинт /api/tts перед @app.route("/persona"
old_route = '@app.route("/persona", methods=["GET"])'
new_route = '''@app.route("/api/tts", methods=["GET", "POST"])
def api_tts():
    text = request.args.get("text") or (request.get_json(silent=True) or {}).get("text", "")
    persona = request.args.get("persona") or (request.get_json(silent=True) or {}).get("persona", "") or CURRENT_PERSONA
    if not text:
        return ("Empty text", 400)
    bio = rick_voice.voice_engine.synthesize_to_memory(text, persona=persona)
    bio.seek(0)
    return send_file(bio, mimetype="audio/wav", as_attachment=False, download_name="voice.wav")

@app.route("/persona", methods=["GET"])'''
assert old_route in content, "old_route not found"
content = content.replace(old_route, new_route, 1)

# 4. Обновляем executeVoiceOutput в HTML_TEMPLATE
old_voice_js = '''        function executeVoiceOutput(spoken) {
            applyNativeVoiceSettings();
            // Conservative speech duration (pitch 0.40 bass, Russian words average 480ms + 1200ms latency)
            const words = spoken.trim().split(/\s+/).filter(Boolean);
            const speechDurationMs = Math.max(1600, words.length * 480 + 1200);

            // 1. Android Native TTS
            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.speak === 'function') {
                window.MelvinNativeBridge.speak(spoken);
                setTimeout(onBotSpeechFinished, speechDurationMs);
                return;
            }'''

new_voice_js = '''        function executeVoiceOutput(spoken) {
            applyNativeVoiceSettings();
            const words = spoken.trim().split(/\s+/).filter(Boolean);
            const speechDurationMs = Math.max(1600, words.length * 480 + 1200);

            // 0. Высококачественный серверный DSP-бас через /api/tts
            const ttsUrl = '/api/tts?text=' + encodeURIComponent(spoken) + '&persona=' + encodeURIComponent(currentPersona);
            const neuralAudio = new Audio(ttsUrl);
            neuralAudio.onended = onBotSpeechFinished;
            neuralAudio.onerror = (err) => {
                console.log('[TTS fallback to bridge]:', err);
                if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.speak === 'function') {
                    window.MelvinNativeBridge.speak(spoken);
                    setTimeout(onBotSpeechFinished, speechDurationMs);
                } else if ('speechSynthesis' in window) {
                    window.speechSynthesis.cancel();
                    const utter = new SpeechSynthesisUtterance(spoken);
                    utter.lang = 'ru-RU';
                    utter.rate = TARGET_RATE;
                    utter.pitch = TARGET_PITCH;
                    utter.onend = onBotSpeechFinished;
                    utter.onerror = onBotSpeechFinished;
                    window.speechSynthesis.speak(utter);
                } else {
                    setTimeout(onBotSpeechFinished, speechDurationMs);
                }
            };
            neuralAudio.play().catch(e => {
                console.log('[Audio autoplay catch]:', e);
                neuralAudio.onerror(e);
            });
            return;

            // 1. Android Native TTS
            if (window.MelvinNativeBridge && typeof window.MelvinNativeBridge.speak === 'function') {
                window.MelvinNativeBridge.speak(spoken);
                setTimeout(onBotSpeechFinished, speechDurationMs);
                return;
            }'''
assert old_voice_js in content, "old_voice_js not found"
content = content.replace(old_voice_js, new_voice_js, 1)

# 5. Встраиваем web_tools и knowledge_rag в chat()
old_chat_search = '''    # 5. Поиск в интернет / Perplexity
    if any(w in user_msg.lower() for w in ["найди", "погугли", "кто такой", "что такое", "новости", "курс", "интернет"]):
        web_ans = query_perplexity_or_web(user_msg, persona=persona)
        if web_ans:
            if persona == "rick" and not web_ans.startswith("*рыгает*"):
                web_ans = "*рыгает* " + web_ans
            dt = round(time.time() - t0, 2)
            save_memory("assistant", web_ans)
            return jsonify({
                "response": web_ans,
                "persona": persona,
                "tool_used": "web_search",
                "inference_time_sec": dt,
                "status": "ok"
            })'''

new_chat_search = '''    # 5. Умный поиск фактов: Web-роутер (погода, ЦБ РФ, Wiki) + локальный SQLite FTS5 RAG
    discovered_fact = web_tools.route_web_fact(user_msg)
    if not discovered_fact:
        discovered_fact = knowledge_rag.search_knowledge(user_msg)

    if discovered_fact and any(w in user_msg.lower() for w in ["погода", "курс", "доллар", "евро", "кто такой", "что такое", "найди", "новости"]):
        if persona == "rick":
            final_fact_ans = f"*рыгает* Слушай сюда, Морти: {discovered_fact}"
        else:
            final_fact_ans = f"Данные из глобальной сети: {discovered_fact}"
        dt = round(time.time() - t0, 2)
        save_memory("assistant", final_fact_ans)
        return jsonify({
            "response": final_fact_ans,
            "persona": persona,
            "tool_used": "web_rag",
            "inference_time_sec": dt,
            "status": "ok"
        })

    # 5.1 Fallback Perplexity, если настроен API-ключ
    if any(w in user_msg.lower() for w in ["найди", "погугли", "интернет"]):
        web_ans = query_perplexity_or_web(user_msg, persona=persona)
        if web_ans:
            if persona == "rick" and not web_ans.startswith("*рыгает*"):
                web_ans = "*рыгает* " + web_ans
            dt = round(time.time() - t0, 2)
            save_memory("assistant", web_ans)
            return jsonify({
                "response": web_ans,
                "persona": persona,
                "tool_used": "web_search",
                "inference_time_sec": dt,
                "status": "ok"
            })'''

assert old_chat_search in content, "old_chat_search not found"
content = content.replace(old_chat_search, new_chat_search, 1)

# 6. Добавляем обнаруженный факт в системный контекст LLM, если запрос пошел в локальную нейросеть
old_llm_call = '    prompt = f"<|im_start|>system\\n{sys_prompt}<|im_end|>\\n"'
new_llm_call = '''    if discovered_fact:
        sys_prompt += f"\\nФАКТИЧЕСКИЙ КОНТЕКСТ: {discovered_fact}"
    prompt = f"<|im_start|>system\\n{sys_prompt}<|im_end|>\\n"'''
assert old_llm_call in content, "old_llm_call not found"
content = content.replace(old_llm_call, new_llm_call, 1)

with open("melvin_src/agent_orchestrator.py", "w", encoding="utf-8") as f:
    f.write(content)

print("agent_orchestrator.py patched successfully!")
