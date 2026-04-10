/**
 * HealthGuard AI — Chatbot Logic & API Integration
 *
 * Handles symptom input with auto-complete, chat message rendering,
 * prediction API calls, and result display with typing animations.
 */

// ─── State ──────────────────────────────────────────────────────
let allSymptoms = [];
let selectedSymptoms = [];
let highlightedIndex = -1;
let chatStarted = false;

// ─── DOM Elements ───────────────────────────────────────────────
const welcomeScreen = document.getElementById('welcome-screen');
const chatMessages = document.getElementById('chat-messages');
const symptomInput = document.getElementById('symptom-input');
const sendBtn = document.getElementById('send-btn');
const autocompleteDropdown = document.getElementById('autocomplete-dropdown');
const selectedSymptomsContainer = document.getElementById('selected-symptoms');

// ─── Initialize ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    loadSymptoms();
    setupEventListeners();
});

async function loadSymptoms() {
    try {
        const res = await fetch('/api/symptoms');
        const data = await res.json();
        allSymptoms = data.symptoms || [];
    } catch (err) {
        console.warn('Could not load symptom list:', err);
    }
}

function setupEventListeners() {
    // Input events
    symptomInput.addEventListener('input', handleInput);
    symptomInput.addEventListener('keydown', handleKeydown);
    symptomInput.addEventListener('focus', () => {
        if (symptomInput.value.trim()) handleInput();
    });

    // Send button
    sendBtn.addEventListener('click', sendSymptoms);

    // Quick actions
    document.querySelectorAll('.quick-action').forEach(btn => {
        btn.addEventListener('click', () => {
            const symptoms = btn.dataset.symptoms.split(',');
            symptoms.forEach(s => addSymptom(s.trim()));
            sendSymptoms();
        });
    });

    // Close dropdown on outside click
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.input-container')) {
            hideDropdown();
        }
    });
}

// ─── Autocomplete ───────────────────────────────────────────────
function handleInput() {
    const query = symptomInput.value.toLowerCase().trim();
    if (!query || query.length < 1) {
        hideDropdown();
        return;
    }

    const matches = allSymptoms.filter(s =>
        !selectedSymptoms.includes(s.value) &&
        (s.label.toLowerCase().includes(query) || s.value.includes(query.replace(/\s/g, '_')))
    ).slice(0, 8);

    if (matches.length === 0) {
        hideDropdown();
        return;
    }

    highlightedIndex = -1;
    autocompleteDropdown.innerHTML = matches.map((s, i) => {
        const label = highlightMatch(s.label, query);
        return `<div class="autocomplete-item" data-value="${s.value}" data-index="${i}">${label}</div>`;
    }).join('');

    // Click events
    autocompleteDropdown.querySelectorAll('.autocomplete-item').forEach(item => {
        item.addEventListener('click', () => {
            addSymptom(item.dataset.value);
            symptomInput.value = '';
            hideDropdown();
            symptomInput.focus();
        });
    });

    showDropdown();
}

function highlightMatch(text, query) {
    const idx = text.toLowerCase().indexOf(query.toLowerCase());
    if (idx === -1) return text;
    return text.substring(0, idx) +
        `<mark>${text.substring(idx, idx + query.length)}</mark>` +
        text.substring(idx + query.length);
}

function handleKeydown(e) {
    const items = autocompleteDropdown.querySelectorAll('.autocomplete-item');

    if (e.key === 'ArrowDown') {
        e.preventDefault();
        highlightedIndex = Math.min(highlightedIndex + 1, items.length - 1);
        updateHighlight(items);
    } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        highlightedIndex = Math.max(highlightedIndex - 1, -1);
        updateHighlight(items);
    } else if (e.key === 'Enter') {
        e.preventDefault();
        if (highlightedIndex >= 0 && items[highlightedIndex]) {
            addSymptom(items[highlightedIndex].dataset.value);
            symptomInput.value = '';
            hideDropdown();
        } else if (symptomInput.value.trim()) {
            // Add as custom symptom
            const val = symptomInput.value.trim().toLowerCase().replace(/\s+/g, '_');
            addSymptom(val);
            symptomInput.value = '';
            hideDropdown();
        } else if (selectedSymptoms.length > 0) {
            sendSymptoms();
        }
    } else if (e.key === 'Backspace' && !symptomInput.value) {
        // Remove last chip
        if (selectedSymptoms.length > 0) {
            removeSymptom(selectedSymptoms[selectedSymptoms.length - 1]);
        }
    }
}

function updateHighlight(items) {
    items.forEach((item, i) => {
        item.classList.toggle('highlighted', i === highlightedIndex);
    });
}

function showDropdown() {
    autocompleteDropdown.classList.add('show');
}

function hideDropdown() {
    autocompleteDropdown.classList.remove('show');
    highlightedIndex = -1;
}

// ─── Symptom Chips ──────────────────────────────────────────────
function addSymptom(value) {
    if (selectedSymptoms.includes(value)) return;
    selectedSymptoms.push(value);
    renderChips();
}

function removeSymptom(value) {
    selectedSymptoms = selectedSymptoms.filter(s => s !== value);
    renderChips();
}

function renderChips() {
    selectedSymptomsContainer.innerHTML = selectedSymptoms.map(s => {
        const label = s.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        return `<span class="symptom-chip" data-value="${s}">
            ${label}
            <span class="remove" onclick="removeSymptom('${s}')">×</span>
        </span>`;
    }).join('');

    sendBtn.disabled = selectedSymptoms.length === 0;
}

// ─── Chat Flow ──────────────────────────────────────────────────
function startChat() {
    if (chatStarted) return;
    chatStarted = true;
    welcomeScreen.style.display = 'none';
    chatMessages.style.display = 'flex';

    addBotMessage("👋 Hello! I'm <strong>HealthGuard AI</strong>. Tell me your symptoms and I'll analyze them to suggest possible conditions.\n\n<em>Remember: This is for educational purposes only — not a substitute for professional medical advice.</em>");
}

function addBotMessage(html) {
    const msg = document.createElement('div');
    msg.className = 'message bot';
    msg.innerHTML = `
        <div class="message-avatar">🛡️</div>
        <div class="message-bubble">${html}</div>
    `;
    chatMessages.appendChild(msg);
    scrollToBottom();
}

function addUserMessage(text) {
    const msg = document.createElement('div');
    msg.className = 'message user';
    msg.innerHTML = `
        <div class="message-avatar">👤</div>
        <div class="message-bubble">${text}</div>
    `;
    chatMessages.appendChild(msg);
    scrollToBottom();
}

function addTypingIndicator() {
    const msg = document.createElement('div');
    msg.className = 'message bot';
    msg.id = 'typing-indicator';
    msg.innerHTML = `
        <div class="message-avatar">🛡️</div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        </div>
    `;
    chatMessages.appendChild(msg);
    scrollToBottom();
}

function removeTypingIndicator() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ─── Send & Predict ─────────────────────────────────────────────
async function sendSymptoms() {
    if (selectedSymptoms.length === 0) return;

    startChat();

    const symptoms = [...selectedSymptoms];
    const displayText = symptoms
        .map(s => s.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()))
        .join(', ');

    // User message
    addUserMessage(`I'm experiencing: <strong>${displayText}</strong>`);

    // Clear chips
    selectedSymptoms = [];
    renderChips();
    symptomInput.value = '';
    sendBtn.disabled = true;

    // Typing indicator
    addTypingIndicator();

    try {
        const res = await fetch('/api/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ symptoms })
        });

        removeTypingIndicator();

        if (!res.ok) throw new Error(`API error: ${res.status}`);

        const data = await res.json();
        showPredictionResult(data);
    } catch (err) {
        removeTypingIndicator();
        addBotMessage(`❌ <strong>Error:</strong> Could not get a prediction. ${err.message}<br><br>Please make sure the server is running.`);
    }
}

function showPredictionResult(data) {
    const matchedChips = data.symptoms_matched.map(s => {
        const label = s.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        return `<span class="symptom-chip">${label}</span>`;
    }).join('');

    const topPredictionsHTML = data.top_predictions.map(p => `
        <div class="prediction-row">
            <span class="prediction-row-name">${p.disease}</span>
            <span class="prediction-row-conf">${p.confidence.toFixed(1)}%</span>
        </div>
    `).join('');

    const confClass = data.confidence >= 70 ? 'conf-high' :
                      data.confidence >= 40 ? 'conf-medium' : 'conf-low';

    const html = `
        Based on your symptoms, here's my analysis:

        <div class="prediction-card">
            <div class="prediction-header">
                <div class="prediction-icon">🔬</div>
                <div>
                    <div class="prediction-disease">${data.disease}</div>
                    <div class="prediction-confidence">
                        <span class="conf-badge ${confClass}">${data.confidence.toFixed(1)}% confidence</span>
                    </div>
                </div>
            </div>

            <div class="confidence-bar-container">
                <div class="confidence-bar" style="width: 0%;" data-target="${data.confidence}"></div>
            </div>

            <div class="top-predictions">
                <h4>Other Possible Conditions</h4>
                ${topPredictionsHTML}
            </div>

            <div style="margin-top: 0.75rem;">
                <h4 style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 0.4rem;">Symptoms Matched</h4>
                <div class="symptom-chips">${matchedChips || '<span style="color: var(--text-muted); font-size: 0.8rem;">No exact matches found</span>'}</div>
            </div>

            <div class="disclaimer-badge">
                <span>⚠️</span>
                <span>${data.disclaimer}</span>
            </div>
        </div>
    `;

    addBotMessage(html);

    // Animate confidence bar
    setTimeout(() => {
        const bar = chatMessages.querySelector('.confidence-bar[data-target]');
        if (bar) {
            bar.style.width = bar.dataset.target + '%';
        }
    }, 100);

    // Follow-up prompt
    setTimeout(() => {
        addBotMessage("Do you have any other symptoms you'd like me to analyze? Just type them below! 👇");
    }, 800);
}
