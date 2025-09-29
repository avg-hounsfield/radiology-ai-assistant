#!/usr/bin/env python3
"""
User Authentication and Personalization System for ECHO
Provides secure login, user profiles, and personalized study experiences
"""

import streamlit as st
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List
import uuid
import os

class UserManager:
    """Manages user authentication and personalized experiences"""

    def __init__(self, users_file: str = "data/users/users.json"):
        self.users_file = Path(users_file)
        self.users_file.parent.mkdir(parents=True, exist_ok=True)

        self.users = self._load_users()
        self.session_timeout = timedelta(hours=24)  # 24 hour sessions

    def _load_users(self) -> Dict:
        """Load users from file"""
        if self.users_file.exists():
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.error(f"Error loading users: {e}")

        # Create default admin user if no users exist
        return self._create_default_users()

    def _create_default_users(self) -> Dict:
        """Create default admin user"""
        admin_password = os.getenv('ADMIN_PASSWORD', 'echo2024')

        default_users = {
            'admin': {
                'password_hash': self._hash_password(admin_password),
                'email': 'admin@echo-radiology.com',
                'role': 'admin',
                'profile': {
                    'full_name': 'ECHO Administrator',
                    'specialty': 'Radiology',
                    'exam_date': None,
                    'study_goals': ['Board Preparation'],
                    'preferred_difficulty': 'Intermediate',
                    'daily_study_minutes': 60
                },
                'created_date': datetime.now().isoformat(),
                'last_login': None,
                'is_active': True
            }
        }
        self._save_users(default_users)
        return default_users

    def _save_users(self, users: Dict = None):
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(users or self.users, f, indent=2)
        except Exception as e:
            logging.error(f"Error saving users: {e}")

    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = "echo_radiology_2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()

    def authenticate_user(self, username: str, password: str) -> bool:
        """Authenticate user credentials"""
        if username in self.users:
            stored_hash = self.users[username]['password_hash']
            provided_hash = self._hash_password(password)

            if stored_hash == provided_hash and self.users[username]['is_active']:
                # Update last login
                self.users[username]['last_login'] = datetime.now().isoformat()
                self._save_users()
                return True

        return False

    def register_user(self, username: str, password: str, email: str, profile_data: Dict) -> bool:
        """Register a new user"""
        if username in self.users:
            return False  # User already exists

        user_data = {
            'password_hash': self._hash_password(password),
            'email': email,
            'role': 'user',
            'profile': {
                'full_name': profile_data.get('full_name', ''),
                'specialty': profile_data.get('specialty', 'Radiology'),
                'exam_date': profile_data.get('exam_date'),
                'study_goals': profile_data.get('study_goals', ['Board Preparation']),
                'preferred_difficulty': profile_data.get('preferred_difficulty', 'Intermediate'),
                'daily_study_minutes': profile_data.get('daily_study_minutes', 60),
                'subspecialty_interests': profile_data.get('subspecialty_interests', [])
            },
            'created_date': datetime.now().isoformat(),
            'last_login': None,
            'is_active': True,
            'study_stats': {
                'total_study_minutes': 0,
                'flashcards_reviewed': 0,
                'questions_answered': 0,
                'average_accuracy': 0.0,
                'study_streak_days': 0,
                'last_study_date': None
            },
            'preferences': {
                'theme': 'dark',
                'audio_enabled': True,
                'notifications_enabled': True,
                'spaced_repetition_enabled': True,
                'show_explanations': True
            }
        }

        self.users[username] = user_data
        self._save_users()
        return True

    def get_user_profile(self, username: str) -> Optional[Dict]:
        """Get user profile data"""
        if username in self.users:
            return self.users[username]
        return None

    def update_user_profile(self, username: str, profile_data: Dict):
        """Update user profile"""
        if username in self.users:
            self.users[username]['profile'].update(profile_data)
            self._save_users()

    def update_study_stats(self, username: str, stats_update: Dict):
        """Update user study statistics"""
        if username in self.users:
            if 'study_stats' not in self.users[username]:
                self.users[username]['study_stats'] = {}

            self.users[username]['study_stats'].update(stats_update)
            self.users[username]['study_stats']['last_study_date'] = datetime.now().isoformat()
            self._save_users()

class StreamlitAuth:
    """Streamlit authentication interface"""

    def __init__(self):
        self.user_manager = UserManager()

    def show_login_page(self):
        """Display login/registration page"""
        st.markdown("# 🩻 ECHO Radiology System")
        st.markdown("### Comprehensive Board Preparation Platform")

        # Create tabs for login and registration
        tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])

        with tab1:
            self._show_login_form()

        with tab2:
            self._show_registration_form()

        # Demo access
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🎯 Demo Access (No Registration)", type="secondary", use_container_width=True):
                st.session_state.authenticated = True
                st.session_state.username = "demo_user"
                st.session_state.user_profile = self._get_demo_profile()
                st.rerun()

        with col2:
            if st.button("👨‍⚕️ Admin Login", type="secondary", use_container_width=True):
                st.session_state.show_admin_login = True
                st.rerun()

        # Admin login modal
        if st.session_state.get('show_admin_login', False):
            with st.expander("🔒 Administrator Access", expanded=True):
                admin_password = st.text_input("Admin Password", type="password")
                col_login, col_cancel = st.columns(2)

                with col_login:
                    if st.button("Login as Admin", type="primary"):
                        if self.user_manager.authenticate_user("admin", admin_password):
                            st.session_state.authenticated = True
                            st.session_state.username = "admin"
                            st.session_state.user_profile = self.user_manager.get_user_profile("admin")
                            st.session_state.show_admin_login = False
                            st.success("✅ Admin login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid admin password")

                with col_cancel:
                    if st.button("Cancel"):
                        st.session_state.show_admin_login = False
                        st.rerun()

    def _show_login_form(self):
        """Show login form"""
        st.markdown("#### Welcome Back!")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            remember_me = st.checkbox("Remember me")

            submitted = st.form_submit_button("🚀 Login", type="primary", use_container_width=True)

            if submitted:
                if self.user_manager.authenticate_user(username, password):
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.session_state.user_profile = self.user_manager.get_user_profile(username)
                    st.success(f"✅ Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error("❌ Invalid username or password")

    def _show_registration_form(self):
        """Show registration form"""
        st.markdown("#### Join ECHO Community!")

        with st.form("registration_form"):
            col1, col2 = st.columns(2)

            with col1:
                username = st.text_input("Username*")
                full_name = st.text_input("Full Name*")
                email = st.text_input("Email*")
                password = st.text_input("Password*", type="password")

            with col2:
                specialty = st.selectbox("Specialty",
                    ["Radiology", "Emergency Medicine", "Internal Medicine", "Surgery", "Other"])

                exam_date = st.date_input("Target Exam Date (optional)")

                difficulty = st.selectbox("Preferred Study Level",
                    ["Basic", "Intermediate", "Advanced"])

                daily_minutes = st.slider("Daily Study Goal (minutes)", 15, 180, 60)

            # Subspecialty interests
            subspecialties = st.multiselect("Subspecialty Interests (optional)",
                ["Neuroradiology", "Chest Imaging", "Abdominal Imaging",
                 "MSK Imaging", "Breast Imaging", "Pediatric Radiology",
                 "Nuclear Medicine", "Physics & Safety", "Interventional"])

            study_goals = st.multiselect("Study Goals",
                ["Board Preparation", "Continuing Education", "Fellowship Prep",
                 "Case Review", "Research"], default=["Board Preparation"])

            terms_agreed = st.checkbox("I agree to the Terms of Service and Privacy Policy*")

            submitted = st.form_submit_button("📚 Create Account", type="primary", use_container_width=True)

            if submitted:
                if not all([username, full_name, email, password, terms_agreed]):
                    st.error("❌ Please fill all required fields and agree to terms")
                else:
                    profile_data = {
                        'full_name': full_name,
                        'specialty': specialty,
                        'exam_date': exam_date.isoformat() if exam_date else None,
                        'preferred_difficulty': difficulty,
                        'daily_study_minutes': daily_minutes,
                        'subspecialty_interests': subspecialties,
                        'study_goals': study_goals
                    }

                    if self.user_manager.register_user(username, password, email, profile_data):
                        st.success("✅ Account created successfully! Please login.")
                        st.balloons()
                    else:
                        st.error("❌ Username already exists. Please choose a different username.")

    def _get_demo_profile(self) -> Dict:
        """Get demo user profile"""
        return {
            'profile': {
                'full_name': 'Demo User',
                'specialty': 'Radiology',
                'preferred_difficulty': 'Intermediate',
                'daily_study_minutes': 60,
                'study_goals': ['Board Preparation']
            },
            'role': 'demo',
            'preferences': {
                'theme': 'dark',
                'audio_enabled': True,
                'notifications_enabled': False
            }
        }

    def check_authentication(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('authenticated', False)

    def show_user_menu(self):
        """Show user menu in sidebar"""
        if not self.check_authentication():
            return

        user_profile = st.session_state.get('user_profile', {})
        username = st.session_state.get('username', 'User')

        with st.sidebar:
            st.markdown("---")
            st.markdown("### 👤 User Profile")

            full_name = user_profile.get('profile', {}).get('full_name', username)
            st.markdown(f"**{full_name}**")

            role = user_profile.get('role', 'user')
            if role == 'admin':
                st.markdown("🔰 **Administrator**")
            elif role == 'demo':
                st.markdown("🎯 **Demo User**")

            # Study stats if available
            study_stats = user_profile.get('study_stats', {})
            if study_stats:
                st.markdown("**Today's Progress:**")
                if study_stats.get('study_streak_days', 0) > 0:
                    st.markdown(f"🔥 {study_stats['study_streak_days']} day streak")

                accuracy = study_stats.get('average_accuracy', 0)
                if accuracy > 0:
                    st.markdown(f"🎯 {accuracy:.1%} accuracy")

            # User menu buttons
            col1, col2 = st.columns(2)
            with col1:
                if st.button("⚙️ Settings", use_container_width=True):
                    st.session_state.show_settings = True

            with col2:
                if st.button("🚪 Logout", use_container_width=True):
                    self.logout()

    def logout(self):
        """Logout user"""
        # Clear session state
        for key in ['authenticated', 'username', 'user_profile', 'show_settings']:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

    def get_personalized_content(self, username: str) -> Dict:
        """Get personalized content based on user profile"""
        user_profile = self.user_manager.get_user_profile(username)
        if not user_profile:
            return {}

        profile = user_profile.get('profile', {})
        preferences = user_profile.get('preferences', {})

        return {
            'difficulty_filter': profile.get('preferred_difficulty', 'Intermediate'),
            'subspecialty_focus': profile.get('subspecialty_interests', []),
            'study_goals': profile.get('study_goals', []),
            'daily_goal_minutes': profile.get('daily_study_minutes', 60),
            'audio_enabled': preferences.get('audio_enabled', True),
            'show_explanations': preferences.get('show_explanations', True),
            'theme': preferences.get('theme', 'dark')
        }

# Global authentication instance
auth = StreamlitAuth()

def require_authentication():
    """Decorator to require authentication"""
    if not auth.check_authentication():
        auth.show_login_page()
        st.stop()

def get_current_user():
    """Get current authenticated user"""
    return st.session_state.get('username')

def get_user_profile():
    """Get current user profile"""
    return st.session_state.get('user_profile', {})

def update_user_study_progress(minutes_studied: int, flashcards_reviewed: int = 0,
                              questions_answered: int = 0, correct_answers: int = 0):
    """Update user study progress"""
    username = get_current_user()
    if not username or username == 'demo_user':
        return

    accuracy = (correct_answers / questions_answered * 100) if questions_answered > 0 else 0

    stats_update = {
        'total_study_minutes': minutes_studied,
        'flashcards_reviewed': flashcards_reviewed,
        'questions_answered': questions_answered,
        'average_accuracy': accuracy
    }

    auth.user_manager.update_study_stats(username, stats_update)