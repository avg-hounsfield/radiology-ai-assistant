#!/usr/bin/env python3
"""
Session persistence manager for the radiology AI assistant
Handles saving and loading user data between sessions
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

class SessionManager:
    """Manages persistence of user session data"""
    
    def __init__(self, data_dir: str = "data/sessions"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Define file paths for different data types
        self.conversation_file = self.data_dir / "conversation_history.json"
        self.performance_file = self.data_dir / "performance_data.json"
        self.quiz_file = self.data_dir / "quiz_progress.json"
        self.settings_file = self.data_dir / "user_settings.json"
        
        self.logger = logging.getLogger(__name__)
        
    def save_conversation_history(self, conversations: List[Dict[str, Any]]) -> bool:
        """Save conversation history to disk"""
        try:
            # Keep only the last 100 conversations to prevent file size issues
            conversations_to_save = conversations[-100:] if len(conversations) > 100 else conversations
            
            data = {
                'conversations': conversations_to_save,
                'last_updated': datetime.now().isoformat(),
                'total_conversations': len(conversations)
            }
            
            with open(self.conversation_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(conversations_to_save)} conversations to disk")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save conversation history: {e}")
            return False
    
    def load_conversation_history(self) -> List[Dict[str, Any]]:
        """Load conversation history from disk"""
        try:
            if not self.conversation_file.exists():
                return []
            
            with open(self.conversation_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            conversations = data.get('conversations', [])
            self.logger.info(f"Loaded {len(conversations)} conversations from disk")
            return conversations
            
        except Exception as e:
            self.logger.error(f"Failed to load conversation history: {e}")
            return []
    
    def save_performance_data(self, performance_data: Dict[str, Any]) -> bool:
        """Save performance tracking data"""
        try:
            data = {
                'performance_metrics': performance_data,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.performance_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            self.logger.info("Saved performance data to disk")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save performance data: {e}")
            return False
    
    def load_performance_data(self) -> Dict[str, Any]:
        """Load performance tracking data"""
        try:
            if not self.performance_file.exists():
                return {}
            
            with open(self.performance_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            performance_data = data.get('performance_metrics', {})
            self.logger.info("Loaded performance data from disk")
            return performance_data
            
        except Exception as e:
            self.logger.error(f"Failed to load performance data: {e}")
            return {}
    
    def save_quiz_progress(self, quiz_data: Dict[str, Any]) -> bool:
        """Save quiz progress and scores"""
        try:
            existing_data = self.load_quiz_progress()
            
            # Update existing data with new data
            existing_data.update(quiz_data)
            existing_data['last_updated'] = datetime.now().isoformat()
            
            with open(self.quiz_file, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=2)
            
            self.logger.info("Saved quiz progress to disk")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save quiz progress: {e}")
            return False
    
    def load_quiz_progress(self) -> Dict[str, Any]:
        """Load quiz progress and scores"""
        try:
            if not self.quiz_file.exists():
                return {}
            
            with open(self.quiz_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info("Loaded quiz progress from disk")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load quiz progress: {e}")
            return {}
    
    def save_user_settings(self, settings: Dict[str, Any]) -> bool:
        """Save user preferences and settings"""
        try:
            settings['last_updated'] = datetime.now().isoformat()
            
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2)
            
            self.logger.info("Saved user settings to disk")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to save user settings: {e}")
            return False
    
    def load_user_settings(self) -> Dict[str, Any]:
        """Load user preferences and settings"""
        try:
            if not self.settings_file.exists():
                return {}
            
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info("Loaded user settings from disk")
            return data
            
        except Exception as e:
            self.logger.error(f"Failed to load user settings: {e}")
            return {}
    
    def save_all_session_data(self, session_data: Dict[str, Any]) -> bool:
        """Save all session data at once"""
        success = True
        
        # Save conversation history
        if 'conversation_history' in session_data:
            success &= self.save_conversation_history(session_data['conversation_history'])
        
        # Save performance data
        if 'performance_data' in session_data:
            success &= self.save_performance_data(session_data['performance_data'])
        
        # Save quiz progress
        quiz_data = {}
        for key in ['quiz_score', 'quiz_questions', 'study_progress', 'questions_today']:
            if key in session_data:
                quiz_data[key] = session_data[key]
        
        if quiz_data:
            success &= self.save_quiz_progress(quiz_data)
        
        # Save user settings
        settings = {}
        for key in ['current_mode', 'demo_mode']:
            if key in session_data:
                settings[key] = session_data[key]
        
        if settings:
            success &= self.save_user_settings(settings)
        
        return success
    
    def load_all_session_data(self) -> Dict[str, Any]:
        """Load all session data at once"""
        session_data = {}
        
        # Load conversation history
        session_data['conversation_history'] = self.load_conversation_history()
        
        # Load performance data
        session_data['performance_data'] = self.load_performance_data()
        
        # Load quiz progress
        quiz_data = self.load_quiz_progress()
        for key in ['quiz_score', 'quiz_questions', 'study_progress', 'questions_today']:
            if key == 'study_progress':
                session_data[key] = quiz_data.get(key, {})  # Dictionary for study progress
            elif 'score' in key or 'today' in key:
                session_data[key] = quiz_data.get(key, 0)  # Integer for scores/counts
            else:
                session_data[key] = quiz_data.get(key, [])  # List for other items
        
        # Load user settings
        settings = self.load_user_settings()
        session_data['current_mode'] = settings.get('current_mode', 'main')
        session_data['demo_mode'] = settings.get('demo_mode', True)
        
        return session_data
    
    def clear_all_data(self) -> bool:
        """Clear all saved session data"""
        try:
            for file_path in [self.conversation_file, self.performance_file, 
                             self.quiz_file, self.settings_file]:
                if file_path.exists():
                    file_path.unlink()
            
            self.logger.info("Cleared all session data")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear session data: {e}")
            return False
    
    def get_data_summary(self) -> Dict[str, Any]:
        """Get summary of saved data"""
        summary = {}
        
        # Conversation history summary
        conversations = self.load_conversation_history()
        summary['conversations_count'] = len(conversations)
        summary['last_conversation'] = conversations[-1]['timestamp'] if conversations else None
        
        # Performance data summary
        performance_data = self.load_performance_data()
        summary['has_performance_data'] = bool(performance_data)
        
        # Quiz progress summary
        quiz_data = self.load_quiz_progress()
        summary['quiz_progress'] = bool(quiz_data)
        
        # File sizes
        for name, file_path in [
            ('conversations', self.conversation_file),
            ('performance', self.performance_file),
            ('quiz', self.quiz_file),
            ('settings', self.settings_file)
        ]:
            if file_path.exists():
                size_kb = file_path.stat().st_size / 1024
                summary[f'{name}_size_kb'] = round(size_kb, 2)
            else:
                summary[f'{name}_size_kb'] = 0
        
        return summary