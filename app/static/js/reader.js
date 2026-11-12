/**
 * ReadEase - Interactive Reader & Web Speech API TTS Controller
 */

document.addEventListener('DOMContentLoaded', function () {
    const readerTextEl = document.getElementById('reader-content');
    const playBtn = document.getElementById('tts-play-btn');
    const pauseBtn = document.getElementById('tts-pause-btn');
    const resumeBtn = document.getElementById('tts-resume-btn');
    const stopBtn = document.getElementById('tts-stop-btn');
    const speedSelect = document.getElementById('tts-speed');
    const voiceSelect = document.getElementById('tts-voice');
    const ttsStatus = document.getElementById('tts-status');
    const ttsAlert = document.getElementById('tts-unsupported-alert');

    let synth = window.speechSynthesis;
    let utterance = null;
    let voices = [];
    let isSpeaking = false;

    // Check Web Speech API support
    if (!('speechSynthesis' in window)) {
        if (ttsAlert) {
            ttsAlert.classList.remove('d-none');
        }
        if (playBtn) playBtn.disabled = true;
        return;
    }

    // Populate browser voices
    function populateVoices() {
        if (!synth) return;
        voices = synth.getVoices().filter(v => v.lang.startsWith('en'));
        if (voiceSelect) {
            voiceSelect.innerHTML = '';
            if (voices.length === 0) {
                const opt = document.createElement('option');
                opt.textContent = 'Default Device Voice';
                opt.value = '';
                voiceSelect.appendChild(opt);
                return;
            }
            voices.forEach((voice, index) => {
                const option = document.createElement('option');
                option.textContent = `${voice.name} (${voice.lang})`;
                option.value = index;
                if (voice.default || voice.name.includes('Natural') || voice.name.includes('Google')) {
                    option.selected = true;
                }
                voiceSelect.appendChild(option);
            });
        }
    }

    populateVoices();
    if (synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = populateVoices;
    }

    // Helper: update status badge
    function setStatus(text, badgeClass = 'bg-secondary') {
        if (ttsStatus) {
            ttsStatus.textContent = text;
            ttsStatus.className = `badge ${badgeClass}`;
        }
    }

    // Play action
    if (playBtn) {
        playBtn.addEventListener('click', function () {
            if (synth.speaking && synth.paused) {
                synth.resume();
                setStatus('Playing', 'bg-success');
                return;
            }

            if (synth.speaking) {
                synth.cancel();
            }

            const rawText = readerTextEl ? readerTextEl.innerText.trim() : '';
            if (!rawText) {
                alert('No readable text found to narrate.');
                return;
            }

            utterance = new SpeechSynthesisUtterance(rawText);
            
            // Apply speed
            if (speedSelect) {
                utterance.rate = parseFloat(speedSelect.value) || 1.0;
            }

            // Apply voice
            if (voiceSelect && voices.length > 0 && voiceSelect.value !== '') {
                const selectedVoice = voices[parseInt(voiceSelect.value, 10)];
                if (selectedVoice) {
                    utterance.voice = selectedVoice;
                }
            }

            utterance.onstart = function () {
                isSpeaking = true;
                setStatus('Reading aloud...', 'bg-success');
                if (playBtn) playBtn.classList.add('d-none');
                if (pauseBtn) pauseBtn.classList.remove('d-none');
            };

            utterance.onend = function () {
                isSpeaking = false;
                setStatus('Completed', 'bg-secondary');
                if (playBtn) playBtn.classList.remove('d-none');
                if (pauseBtn) pauseBtn.classList.add('d-none');
                if (resumeBtn) resumeBtn.classList.add('d-none');
            };

            utterance.onerror = function (e) {
                console.warn('TTS error:', e);
                isSpeaking = false;
                setStatus('Voice interrupted', 'bg-warning');
                if (playBtn) playBtn.classList.remove('d-none');
                if (pauseBtn) pauseBtn.classList.add('d-none');
                if (resumeBtn) resumeBtn.classList.add('d-none');
            };

            synth.speak(utterance);
        });
    }

    // Pause action
    if (pauseBtn) {
        pauseBtn.addEventListener('click', function () {
            if (synth.speaking && !synth.paused) {
                synth.pause();
                setStatus('Paused', 'bg-warning text-dark');
                pauseBtn.classList.add('d-none');
                if (resumeBtn) resumeBtn.classList.remove('d-none');
            }
        });
    }

    // Resume action
    if (resumeBtn) {
        resumeBtn.addEventListener('click', function () {
            if (synth.paused) {
                synth.resume();
                setStatus('Reading aloud...', 'bg-success');
                resumeBtn.classList.add('d-none');
                if (pauseBtn) pauseBtn.classList.remove('d-none');
            }
        });
    }

    // Stop action
    if (stopBtn) {
        stopBtn.addEventListener('click', function () {
            synth.cancel();
            isSpeaking = false;
            setStatus('Stopped', 'bg-secondary');
            if (playBtn) playBtn.classList.remove('d-none');
            if (pauseBtn) pauseBtn.classList.add('d-none');
            if (resumeBtn) resumeBtn.classList.add('d-none');
        });
    }

    // Rate change while playing
    if (speedSelect) {
        speedSelect.addEventListener('change', function () {
            if (synth.speaking) {
                const currentText = readerTextEl ? readerTextEl.innerText.trim() : '';
                synth.cancel();
                if (playBtn) playBtn.click();
            }
        });
    }

    // Clean up speech on page exit
    window.addEventListener('beforeunload', function () {
        if (synth && synth.speaking) {
            synth.cancel();
        }
    });

    // Reader Font & Theme Controls
    const fontInc = document.getElementById('btn-font-inc');
    const fontDec = document.getElementById('btn-font-dec');
    const fontReset = document.getElementById('btn-font-reset');
    const themeButtons = document.querySelectorAll('[data-reader-theme]');

    let currentFontSize = 16;

    if (fontInc && readerTextEl) {
        fontInc.addEventListener('click', function () {
            if (currentFontSize < 26) {
                currentFontSize += 2;
                readerTextEl.style.fontSize = `${currentFontSize}px`;
            }
        });
    }

    if (fontDec && readerTextEl) {
        fontDec.addEventListener('click', function () {
            if (currentFontSize > 12) {
                currentFontSize -= 2;
                readerTextEl.style.fontSize = `${currentFontSize}px`;
            }
        });
    }

    if (fontReset && readerTextEl) {
        fontReset.addEventListener('click', function () {
            currentFontSize = 16;
            readerTextEl.style.fontSize = '1.05rem';
        });
    }

    themeButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const theme = this.getAttribute('data-reader-theme');
            if (!readerTextEl) return;
            readerTextEl.classList.remove('reader-theme-sepia', 'reader-theme-dark');
            if (theme === 'sepia') {
                readerTextEl.classList.add('reader-theme-sepia');
            } else if (theme === 'dark') {
                readerTextEl.classList.add('reader-theme-dark');
            }
        });
    });
});
