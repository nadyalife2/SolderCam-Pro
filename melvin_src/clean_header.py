target_file = r"d:\для one plus nord n10\melvin_src\agent_orchestrator.py"
with open(target_file, "r", encoding="utf-8") as f:
    text = f.read()

old_header = """    <header>
        <div class="logo">
            <div class="status-dot"></div> <span id="header-title">МЕЛВИН // HELIO X20</span>
        </div>
        <div class="header-actions">
            <button id="persona-btn" class="persona-btn" onclick="togglePersona()">🤖 МЕЛВИН</button>
            <div id="vad-indicator" class="vad-badge" onclick="triggerManualGoogleVoice()">
                <span class="pulse-dot"></span> <span id="vad-text">СЛУШАЮ: "МЕЛВИН / РИК"</span>
            </div>
        </div>
    </header>"""

new_header = """    <header style="padding: 8px 12px; display: flex; justify-content: space-between; align-items: center;">
        <button id="persona-btn" class="persona-btn" onclick="togglePersona()" style="letter-spacing: 0.5px; padding: 6px 14px; font-size: 12px; font-weight: 900;">МЕЛВИН</button>
        <div id="vad-indicator" class="vad-badge" onclick="triggerManualGoogleVoice()" style="padding: 6px 12px;">
            <span class="pulse-dot"></span> <span id="vad-text">ЖДУ ОКЛИК: "МЕЛВИН" / "РИК"</span>
        </div>
    </header>"""

text = text.replace(old_header, new_header)
text = text.replace("personaBtn.innerHTML = '🧪 РИК';", "personaBtn.innerHTML = 'РИК';")
text = text.replace("personaBtn.innerHTML = '🤖 МЕЛВИН';", "personaBtn.innerHTML = 'МЕЛВИН';")

with open(target_file, "w", encoding="utf-8") as f:
    f.write(text)

print("Header cleaned up!")
