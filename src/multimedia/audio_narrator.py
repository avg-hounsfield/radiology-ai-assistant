# src/multimedia/audio_narrator.py
"""
Text-to-speech audio narration system for radiology study materials
Provides audible learning options for hands-free study
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
import logging
import re
import time
from datetime import datetime

class AudioNarrator:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Audio settings
        self.audio_settings = {
            'voice': 'default',  # System default voice
            'speed': 150,        # Words per minute
            'volume': 0.8,       # 0.0 to 1.0
            'pitch': 'normal',   # normal, high, low
            'format': 'mp3',     # mp3, wav
            'quality': 'medium'  # low, medium, high
        }

        # Audio cache directory
        self.audio_cache_dir = Path("data/audio_cache")
        self.audio_cache_dir.mkdir(exist_ok=True)

        # Audio settings file
        self.settings_file = Path("data/audio_settings.json")
        self.load_audio_settings()

        # Available TTS engines (in order of preference)
        self.tts_engines = [
            'edge_tts',      # Microsoft Edge TTS (best quality)
            'pyttsx3',       # Cross-platform TTS
            'espeak',        # Simple TTS
            'festival',      # Unix TTS
            'built_in'       # Browser built-in TTS (fallback)
        ]

        self.active_engine = None
        self.initialize_tts_engine()

    def load_audio_settings(self):
        """Load audio settings from file"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    saved_settings = json.load(f)
                    self.audio_settings.update(saved_settings)
            except Exception as e:
                self.logger.error(f"Error loading audio settings: {e}")

    def save_audio_settings(self):
        """Save audio settings to file"""
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.audio_settings, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving audio settings: {e}")

    def initialize_tts_engine(self):
        """Initialize the best available TTS engine"""

        for engine_name in self.tts_engines:
            try:
                if engine_name == 'edge_tts':
                    self.active_engine = self.init_edge_tts()
                elif engine_name == 'pyttsx3':
                    self.active_engine = self.init_pyttsx3()
                elif engine_name == 'built_in':
                    self.active_engine = self.init_builtin_tts()

                if self.active_engine:
                    self.logger.info(f"Initialized TTS engine: {engine_name}")
                    return

            except Exception as e:
                self.logger.warning(f"Failed to initialize {engine_name}: {e}")

        self.logger.warning("No TTS engine available, using browser-based fallback")
        self.active_engine = self.init_builtin_tts()

    def init_edge_tts(self):
        """Initialize Microsoft Edge TTS (requires edge-tts package)"""
        try:
            import edge_tts
            return {
                'engine': 'edge_tts',
                'module': edge_tts,
                'available_voices': self.get_edge_voices()
            }
        except ImportError:
            return None

    def init_pyttsx3(self):
        """Initialize pyttsx3 TTS engine"""
        try:
            import pyttsx3
            engine = pyttsx3.init()

            # Configure engine
            engine.setProperty('rate', self.audio_settings['speed'])
            engine.setProperty('volume', self.audio_settings['volume'])

            return {
                'engine': 'pyttsx3',
                'module': engine,
                'available_voices': [voice.id for voice in engine.getProperty('voices')]
            }
        except ImportError:
            return None

    def init_builtin_tts(self):
        """Initialize browser built-in TTS (JavaScript-based)"""
        return {
            'engine': 'built_in',
            'module': None,
            'available_voices': ['default']
        }

    def get_edge_voices(self) -> List[str]:
        """Get available Microsoft Edge TTS voices"""
        try:
            import asyncio
            import edge_tts

            async def get_voices():
                voices = await edge_tts.list_voices()
                return [voice['Name'] for voice in voices if 'en' in voice['Locale']]

            return asyncio.run(get_voices())
        except:
            return ['en-US-AriaNeural', 'en-US-GuyNeural']

    def set_voice_settings(self, voice: str = None, speed: int = None,
                          volume: float = None, pitch: str = None):
        """Update voice settings"""

        if voice:
            self.audio_settings['voice'] = voice
        if speed:
            self.audio_settings['speed'] = max(50, min(300, speed))  # 50-300 WPM
        if volume:
            self.audio_settings['volume'] = max(0.0, min(1.0, volume))
        if pitch:
            self.audio_settings['pitch'] = pitch

        # Reinitialize engine with new settings
        if self.active_engine and self.active_engine['engine'] == 'pyttsx3':
            engine = self.active_engine['module']
            engine.setProperty('rate', self.audio_settings['speed'])
            engine.setProperty('volume', self.audio_settings['volume'])

        self.save_audio_settings()

    def prepare_text_for_speech(self, text: str) -> str:
        """Prepare text for better speech synthesis"""

        # Remove markdown formatting
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*(.*?)\*', r'\1', text)      # Italic
        text = re.sub(r'`(.*?)`', r'\1', text)        # Code
        text = re.sub(r'\[(.*?)\]\(.*?\)', r'\1', text)  # Links

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Improve pronunciation of medical terms
        medical_pronunciations = {
            'CT': 'C T',
            'MRI': 'M R I',
            'PE': 'P E',
            'DVT': 'D V T',
            'ICU': 'I C U',
            'ER': 'E R',
            'IV': 'I V',
            'PO': 'P O',
            'bid': 'twice daily',
            'tid': 'three times daily',
            'qid': 'four times daily',
            'prn': 'as needed',
            'NPO': 'nothing by mouth',
            'STAT': 'immediately',
            'vs': 'versus',
            'w/': 'with',
            'w/o': 'without',
            'yr': 'year',
            'yo': 'year old',
            'pt': 'patient',
            'dx': 'diagnosis',
            'tx': 'treatment',
            'hx': 'history',
            'sx': 'symptoms'
        }

        for abbreviation, pronunciation in medical_pronunciations.items():
            text = re.sub(r'\b' + re.escape(abbreviation) + r'\b', pronunciation, text, flags=re.IGNORECASE)

        # Add pauses for better flow
        text = re.sub(r'\.', '. <break time="500ms"/>', text)
        text = re.sub(r'\;', '; <break time="300ms"/>', text)
        text = re.sub(r'\:', ': <break time="200ms"/>', text)

        # Clean up excessive whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def generate_audio_file(self, text: str, filename: str = None) -> Optional[str]:
        """Generate audio file from text"""

        if not text.strip():
            return None

        # Generate filename if not provided
        if not filename:
            text_hash = hash(text + str(self.audio_settings))
            filename = f"narration_{abs(text_hash)}.{self.audio_settings['format']}"

        audio_path = self.audio_cache_dir / filename

        # Return cached file if exists
        if audio_path.exists():
            return str(audio_path)

        # Prepare text
        clean_text = self.prepare_text_for_speech(text)

        try:
            if self.active_engine['engine'] == 'edge_tts':
                return self.generate_edge_audio(clean_text, audio_path)
            elif self.active_engine['engine'] == 'pyttsx3':
                return self.generate_pyttsx3_audio(clean_text, audio_path)
            else:
                # Return text for browser-based TTS
                return self.generate_builtin_audio_html(clean_text)

        except Exception as e:
            self.logger.error(f"Error generating audio: {e}")
            return None

    def generate_edge_audio(self, text: str, audio_path: Path) -> str:
        """Generate audio using Microsoft Edge TTS"""
        try:
            import asyncio
            import edge_tts

            voice = self.audio_settings.get('voice', 'en-US-AriaNeural')

            async def create_audio():
                communicate = edge_tts.Communicate(text, voice)
                await communicate.save(str(audio_path))

            asyncio.run(create_audio())
            return str(audio_path)

        except Exception as e:
            self.logger.error(f"Edge TTS error: {e}")
            return None

    def generate_pyttsx3_audio(self, text: str, audio_path: Path) -> str:
        """Generate audio using pyttsx3"""
        try:
            engine = self.active_engine['module']
            engine.save_to_file(text, str(audio_path))
            engine.runAndWait()
            return str(audio_path)

        except Exception as e:
            self.logger.error(f"pyttsx3 error: {e}")
            return None

    def generate_builtin_audio_html(self, text: str) -> str:
        """Generate HTML for browser-based TTS"""

        # Escape text for JavaScript
        escaped_text = text.replace("'", "\\'").replace('"', '\\"').replace('\n', ' ')

        html = f"""
        <div class="audio-player">
            <button onclick="playText()" class="play-button">🔊 Play Audio</button>
            <button onclick="stopText()" class="stop-button">⏹️ Stop</button>
            <div class="audio-controls">
                <label>Speed: <input type="range" id="speed-slider" min="0.5" max="2" step="0.1" value="1" onchange="updateSpeed()"/></label>
                <label>Volume: <input type="range" id="volume-slider" min="0" max="1" step="0.1" value="0.8" onchange="updateVolume()"/></label>
            </div>
        </div>

        <script>
        let currentUtterance = null;

        function playText() {{
            if ('speechSynthesis' in window) {{
                stopText(); // Stop any current speech

                currentUtterance = new SpeechSynthesisUtterance("{escaped_text}");
                currentUtterance.rate = document.getElementById('speed-slider').value;
                currentUtterance.volume = document.getElementById('volume-slider').value;
                currentUtterance.pitch = 1;

                // Use a clear voice if available
                const voices = speechSynthesis.getVoices();
                const preferredVoice = voices.find(voice => voice.name.includes('Google') || voice.name.includes('Microsoft'));
                if (preferredVoice) {{
                    currentUtterance.voice = preferredVoice;
                }}

                speechSynthesis.speak(currentUtterance);
            }} else {{
                alert('Text-to-speech not supported in this browser');
            }}
        }}

        function stopText() {{
            if (speechSynthesis.speaking) {{
                speechSynthesis.cancel();
            }}
        }}

        function updateSpeed() {{
            // Speed changes will apply to next playback
        }}

        function updateVolume() {{
            // Volume changes will apply to next playback
        }}

        // Load voices when available
        if ('speechSynthesis' in window) {{
            speechSynthesis.onvoiceschanged = function() {{
                // Voices loaded
            }};
        }}
        </script>

        <style>
        .audio-player {{
            background: #2a3441;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border: 1px solid #4a5568;
        }}

        .play-button, .stop-button {{
            background: #00BFFF;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 5px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }}

        .play-button:hover, .stop-button:hover {{
            background: #0099cc;
        }}

        .audio-controls {{
            margin-top: 10px;
            display: flex;
            gap: 20px;
            align-items: center;
        }}

        .audio-controls label {{
            color: #ffffff;
            font-size: 12px;
        }}

        .audio-controls input[type="range"] {{
            margin-left: 8px;
        }}
        </style>
        """

        return html

    def create_question_audio_session(self, question_data: Dict) -> Dict:
        """Create audio-enhanced question session"""

        session = {
            'question_id': question_data.get('id', 'unknown'),
            'audio_components': {},
            'playback_order': [],
            'total_duration_estimate': 0
        }

        # Question text audio
        question_text = question_data.get('question_text', '')
        if question_text:
            question_audio = self.generate_audio_file(question_text, f"question_{session['question_id']}.mp3")
            session['audio_components']['question'] = {
                'file': question_audio,
                'text': question_text,
                'duration_estimate': len(question_text.split()) / (self.audio_settings['speed'] / 60)
            }
            session['playback_order'].append('question')

        # Answer choices audio
        if 'options' in question_data:
            options_text = "The answer choices are: "
            for key, value in question_data['options'].items():
                options_text += f"Option {key}: {value}. "

            options_audio = self.generate_audio_file(options_text, f"options_{session['question_id']}.mp3")
            session['audio_components']['options'] = {
                'file': options_audio,
                'text': options_text,
                'duration_estimate': len(options_text.split()) / (self.audio_settings['speed'] / 60)
            }
            session['playback_order'].append('options')

        # Explanation audio (for after answering)
        explanation = question_data.get('explanation', '')
        if explanation:
            explanation_audio = self.generate_audio_file(explanation, f"explanation_{session['question_id']}.mp3")
            session['audio_components']['explanation'] = {
                'file': explanation_audio,
                'text': explanation,
                'duration_estimate': len(explanation.split()) / (self.audio_settings['speed'] / 60)
            }

        # Calculate total duration
        session['total_duration_estimate'] = sum(
            comp.get('duration_estimate', 0) for comp in session['audio_components'].values()
        )

        return session

    def create_study_material_audio(self, content: str, title: str = "Study Material") -> Dict:
        """Create audio version of study material"""

        # Split content into manageable chunks
        chunks = self.split_content_for_audio(content)

        audio_session = {
            'title': title,
            'chunks': [],
            'total_duration_estimate': 0,
            'navigation': {
                'current_chunk': 0,
                'total_chunks': len(chunks)
            }
        }

        for i, chunk in enumerate(chunks):
            chunk_audio = self.generate_audio_file(chunk, f"{title.lower().replace(' ', '_')}_chunk_{i}.mp3")

            audio_chunk = {
                'index': i,
                'text': chunk,
                'audio_file': chunk_audio,
                'duration_estimate': len(chunk.split()) / (self.audio_settings['speed'] / 60)
            }

            audio_session['chunks'].append(audio_chunk)
            audio_session['total_duration_estimate'] += audio_chunk['duration_estimate']

        return audio_session

    def split_content_for_audio(self, content: str, max_chunk_size: int = 500) -> List[str]:
        """Split content into audio-friendly chunks"""

        # Split by sentences first
        sentences = re.split(r'(?<=[.!?])\s+', content)

        chunks = []
        current_chunk = ""

        for sentence in sentences:
            # If adding this sentence would exceed max size, start new chunk
            if len(current_chunk.split()) + len(sentence.split()) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence
            else:
                current_chunk += " " + sentence if current_chunk else sentence

        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def get_audio_player_html(self, audio_file: str, text: str = "") -> str:
        """Generate HTML audio player"""

        if self.active_engine['engine'] == 'built_in':
            return self.generate_builtin_audio_html(text)

        # For actual audio files
        return f"""
        <div class="audio-player">
            <audio controls style="width: 100%;">
                <source src="{audio_file}" type="audio/mpeg">
                <source src="{audio_file}" type="audio/wav">
                Your browser does not support the audio element.
            </audio>
            <div class="audio-info">
                <small>Audio narration available - listen while reviewing other materials</small>
            </div>
        </div>

        <style>
        .audio-player {{
            background: #2a3441;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border: 1px solid #4a5568;
        }}

        .audio-info {{
            margin-top: 8px;
            color: #9CA3AF;
            font-style: italic;
        }}
        </style>
        """

    def get_available_voices(self) -> List[Dict]:
        """Get list of available voices"""

        if not self.active_engine:
            return [{'id': 'default', 'name': 'Default Voice', 'language': 'en-US'}]

        voices = []

        if self.active_engine['engine'] == 'edge_tts':
            for voice_id in self.active_engine.get('available_voices', []):
                voices.append({
                    'id': voice_id,
                    'name': voice_id.split('-')[-1],  # Extract voice name
                    'language': voice_id.split('-')[1] if '-' in voice_id else 'en',
                    'quality': 'high'
                })

        elif self.active_engine['engine'] == 'pyttsx3':
            try:
                engine = self.active_engine['module']
                system_voices = engine.getProperty('voices')
                for voice in system_voices:
                    voices.append({
                        'id': voice.id,
                        'name': voice.name,
                        'language': getattr(voice, 'languages', ['en'])[0] if hasattr(voice, 'languages') else 'en',
                        'quality': 'medium'
                    })
            except:
                pass

        else:
            voices.append({
                'id': 'browser_default',
                'name': 'Browser Default',
                'language': 'en-US',
                'quality': 'medium'
            })

        return voices

    def get_audio_settings_interface(self) -> str:
        """Generate HTML interface for audio settings"""

        voices = self.get_available_voices()
        voice_options = ""
        for voice in voices:
            selected = "selected" if voice['id'] == self.audio_settings['voice'] else ""
            voice_options += f'<option value="{voice["id"]}" {selected}>{voice["name"]} ({voice["language"]})</option>'

        return f"""
        <div class="audio-settings">
            <h4>🔊 Audio Narration Settings</h4>

            <div class="setting-group">
                <label for="voice-select">Voice:</label>
                <select id="voice-select" onchange="updateAudioSetting('voice', this.value)">
                    {voice_options}
                </select>
            </div>

            <div class="setting-group">
                <label for="speed-range">Speed (WPM): <span id="speed-value">{self.audio_settings['speed']}</span></label>
                <input type="range" id="speed-range" min="50" max="300" value="{self.audio_settings['speed']}"
                       onchange="updateAudioSetting('speed', this.value); document.getElementById('speed-value').textContent = this.value;">
            </div>

            <div class="setting-group">
                <label for="volume-range">Volume: <span id="volume-value">{int(self.audio_settings['volume'] * 100)}%</span></label>
                <input type="range" id="volume-range" min="0" max="100" value="{int(self.audio_settings['volume'] * 100)}"
                       onchange="updateAudioSetting('volume', this.value / 100); document.getElementById('volume-value').textContent = this.value + '%';">
            </div>

            <div class="setting-group">
                <button onclick="testAudioSettings()" class="test-button">🎵 Test Settings</button>
            </div>
        </div>

        <script>
        function updateAudioSetting(setting, value) {{
            // Send AJAX request to update settings
            fetch('/update_audio_setting', {{
                method: 'POST',
                headers: {{'Content-Type': 'application/json'}},
                body: JSON.stringify({{setting: setting, value: value}})
            }});
        }}

        function testAudioSettings() {{
            const testText = "This is a test of your audio settings. The quick brown fox jumps over the lazy dog.";
            if ('speechSynthesis' in window) {{
                const utterance = new SpeechSynthesisUtterance(testText);
                utterance.rate = document.getElementById('speed-range').value / 150; // Convert WPM to rate
                utterance.volume = document.getElementById('volume-range').value / 100;
                speechSynthesis.speak(utterance);
            }}
        }}
        </script>

        <style>
        .audio-settings {{
            background: #2a3441;
            padding: 20px;
            border-radius: 8px;
            margin: 15px 0;
            border: 1px solid #4a5568;
        }}

        .setting-group {{
            margin: 15px 0;
        }}

        .setting-group label {{
            display: block;
            color: #ffffff;
            margin-bottom: 5px;
            font-weight: 500;
        }}

        .setting-group select, .setting-group input[type="range"] {{
            width: 100%;
            margin-bottom: 10px;
        }}

        .test-button {{
            background: #00BFFF;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }}

        .test-button:hover {{
            background: #0099cc;
        }}
        </style>
        """