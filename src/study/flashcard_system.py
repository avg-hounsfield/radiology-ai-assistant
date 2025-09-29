#!/usr/bin/env python3
"""
Anki-Compatible Flashcard System with Spaced Repetition
Imports Anki decks and implements SM-2 spaced repetition algorithm
"""

import os
import json
import sqlite3
import zipfile
import shutil
import base64
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
import math
import random
import re

@dataclass
class FlashCard:
    """Represents a single flashcard"""
    card_id: str
    deck_name: str
    front: str
    back: str
    tags: List[str]
    created: str
    modified: str

    # Spaced repetition data (SM-2 algorithm)
    ease_factor: float = 2.5  # Default ease factor
    interval: int = 1  # Days until next review
    repetitions: int = 0  # Number of times reviewed
    next_review: str = ""  # Next review date
    last_review: str = ""  # Last review date

    # Performance tracking
    total_reviews: int = 0
    correct_reviews: int = 0

    # Images and media
    images: List[str] = None
    audio: str = ""

    def __post_init__(self):
        if self.images is None:
            self.images = []
        if not self.next_review:
            self.next_review = datetime.now().isoformat()

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

@dataclass
class ReviewSession:
    """Represents a flashcard review session"""
    session_id: str
    deck_name: str
    start_time: str
    end_time: str = ""
    cards_reviewed: int = 0
    cards_correct: int = 0
    cards_wrong: int = 0
    average_response_time: float = 0.0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)

class AnkiImporter:
    """Imports Anki .apkg files and extracts cards with media"""

    def __init__(self, data_dir: str = "data/flashcards"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.media_dir = self.data_dir / "media"
        self.media_dir.mkdir(parents=True, exist_ok=True)

    def import_apkg(self, apkg_path: str) -> Tuple[List[FlashCard], List[str]]:
        """Import an Anki .apkg file and return cards and media files"""
        cards = []
        media_files = []

        try:
            # Extract .apkg file (it's a zip file)
            temp_dir = self.data_dir / "temp_extract"
            temp_dir.mkdir(exist_ok=True)

            with zipfile.ZipFile(apkg_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)

            # Read the SQLite database
            db_path = temp_dir / "collection.anki2"
            if db_path.exists():
                cards, media_files = self._extract_from_db(db_path, temp_dir)

            # Clean up temp directory
            shutil.rmtree(temp_dir, ignore_errors=True)

            logging.info(f"Imported {len(cards)} cards from {Path(apkg_path).name}")
            return cards, media_files

        except Exception as e:
            logging.error(f"Error importing {apkg_path}: {e}")
            return [], []

    def _extract_from_db(self, db_path: Path, temp_dir: Path) -> Tuple[List[FlashCard], List[str]]:
        """Extract cards from Anki SQLite database"""
        cards = []
        media_files = []

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Get deck information
            cursor.execute("SELECT decks FROM col")
            decks_json = cursor.fetchone()[0]
            decks = json.loads(decks_json)

            # Get notes and cards
            cursor.execute("""
                SELECT n.id, n.flds, n.tags, c.id, c.did, n.mod
                FROM notes n
                JOIN cards c ON n.id = c.nid
                WHERE c.queue >= 0
            """)

            for note_id, fields, tags, card_id, deck_id, modified in cursor.fetchall():
                # Find deck name
                deck_name = "Default"
                for did, deck_info in decks.items():
                    if str(deck_id) == did:
                        deck_name = deck_info.get('name', 'Default')
                        break

                # Split fields (Anki uses \x1f separator)
                field_list = fields.split('\x1f')

                if len(field_list) >= 2:
                    front = field_list[0]
                    back = field_list[1]

                    # Extract images from HTML
                    front_images = self._extract_images(front, temp_dir)
                    back_images = self._extract_images(back, temp_dir)
                    all_images = front_images + back_images
                    media_files.extend(all_images)

                    # Clean HTML but preserve basic formatting
                    front_clean = self._clean_html(front)
                    back_clean = self._clean_html(back)

                    card = FlashCard(
                        card_id=str(card_id),
                        deck_name=deck_name,
                        front=front_clean,
                        back=back_clean,
                        tags=tags.strip().split() if tags.strip() else [],
                        created=datetime.now().isoformat(),
                        modified=datetime.fromtimestamp(modified).isoformat(),
                        images=all_images
                    )
                    cards.append(card)

            conn.close()

        except Exception as e:
            logging.error(f"Error extracting from database: {e}")

        return cards, media_files

    def _extract_images(self, html_content: str, temp_dir: Path) -> List[str]:
        """Extract image references from HTML and copy to media directory"""
        images = []

        # Find all img tags
        img_pattern = r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>'
        matches = re.findall(img_pattern, html_content, re.IGNORECASE)

        for img_src in matches:
            # Copy image file to media directory
            source_path = temp_dir / img_src
            if source_path.exists():
                dest_path = self.media_dir / img_src
                try:
                    shutil.copy2(source_path, dest_path)
                    images.append(str(dest_path))
                    logging.info(f"Copied image: {img_src}")
                except Exception as e:
                    logging.warning(f"Failed to copy image {img_src}: {e}")

        return images

    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content while preserving essential formatting"""
        # Remove script and style tags completely
        html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

        # Convert common HTML entities
        html_content = html_content.replace('&nbsp;', ' ')
        html_content = html_content.replace('&lt;', '<')
        html_content = html_content.replace('&gt;', '>')
        html_content = html_content.replace('&amp;', '&')

        # Keep essential formatting tags but clean up attributes
        html_content = re.sub(r'<(b|strong|i|em|u|br|p|div)[^>]*>', r'<\1>', html_content, flags=re.IGNORECASE)
        html_content = re.sub(r'</(b|strong|i|em|u|br|p|div)>', r'</\1>', html_content, flags=re.IGNORECASE)

        # Remove all other HTML tags
        html_content = re.sub(r'<[^>]+>', '', html_content)

        # Clean up whitespace
        html_content = re.sub(r'\s+', ' ', html_content)
        html_content = html_content.strip()

        return html_content

class SpacedRepetitionEngine:
    """Implements SM-2 spaced repetition algorithm"""

    @staticmethod
    def calculate_next_review(card: FlashCard, quality: int) -> FlashCard:
        """
        Calculate next review date using SM-2 algorithm
        quality: 0-5 (0=blackout, 1=incorrect, 2=incorrect but remembered,
                      3=correct with difficulty, 4=correct, 5=perfect)
        """
        card.total_reviews += 1
        card.last_review = datetime.now().isoformat()

        if quality >= 3:
            card.correct_reviews += 1

            if card.repetitions == 0:
                card.interval = 1
            elif card.repetitions == 1:
                card.interval = 6
            else:
                card.interval = round(card.interval * card.ease_factor)

            card.repetitions += 1
        else:
            # Reset if answer was incorrect
            card.repetitions = 0
            card.interval = 1

        # Update ease factor
        card.ease_factor = max(1.3, card.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))

        # Calculate next review date
        next_review_date = datetime.now() + timedelta(days=card.interval)
        card.next_review = next_review_date.isoformat()

        return card

    @staticmethod
    def get_due_cards(cards: List[FlashCard]) -> List[FlashCard]:
        """Get cards that are due for review"""
        now = datetime.now()
        due_cards = []

        for card in cards:
            try:
                next_review = datetime.fromisoformat(card.next_review.replace('Z', '+00:00'))
                if next_review <= now:
                    due_cards.append(card)
            except:
                # If parsing fails, consider card due
                due_cards.append(card)

        return due_cards

    @staticmethod
    def get_new_cards(cards: List[FlashCard], limit: int = 20) -> List[FlashCard]:
        """Get new cards that haven't been reviewed yet"""
        new_cards = [card for card in cards if card.repetitions == 0]
        return new_cards[:limit]

class FlashcardManager:
    """Manages flashcard collections and review sessions"""

    def __init__(self, data_dir: str = "data/flashcards"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.cards_file = self.data_dir / "cards.json"
        self.sessions_file = self.data_dir / "sessions.json"

        self.cards = self._load_cards()
        self.sessions = self._load_sessions()

        self.importer = AnkiImporter(data_dir)
        self.engine = SpacedRepetitionEngine()

        logging.info(f"FlashcardManager initialized with {len(self.cards)} cards")

    def _load_cards(self) -> Dict[str, FlashCard]:
        """Load flashcards from file"""
        if not self.cards_file.exists():
            return {}

        try:
            with open(self.cards_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return {card_id: FlashCard.from_dict(card_data)
                   for card_id, card_data in data.items()}
        except Exception as e:
            logging.error(f"Error loading cards: {e}")
            return {}

    def _save_cards(self):
        """Save flashcards to file"""
        try:
            data = {card_id: card.to_dict() for card_id, card in self.cards.items()}
            with open(self.cards_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving cards: {e}")

    def _load_sessions(self) -> List[ReviewSession]:
        """Load review sessions from file"""
        if not self.sessions_file.exists():
            return []

        try:
            with open(self.sessions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return [ReviewSession.from_dict(session_data) for session_data in data]
        except Exception as e:
            logging.error(f"Error loading sessions: {e}")
            return []

    def _save_sessions(self):
        """Save review sessions to file"""
        try:
            data = [session.to_dict() for session in self.sessions]
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logging.error(f"Error saving sessions: {e}")

    def import_anki_deck(self, apkg_path: str) -> int:
        """Import an Anki deck and return number of cards imported"""
        cards, media_files = self.importer.import_apkg(apkg_path)

        imported_count = 0
        for card in cards:
            if card.card_id not in self.cards:
                self.cards[card.card_id] = card
                imported_count += 1

        self._save_cards()
        logging.info(f"Imported {imported_count} new cards from {Path(apkg_path).name}")
        return imported_count

    def import_all_from_downloads(self, downloads_path: str = None) -> Dict[str, int]:
        """Import all Anki decks from downloads folder"""
        if downloads_path is None:
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")

        downloads_dir = Path(downloads_path)
        results = {}

        # Find all .apkg files
        apkg_files = list(downloads_dir.glob("*.apkg"))

        for apkg_file in apkg_files:
            try:
                count = self.import_anki_deck(str(apkg_file))
                results[apkg_file.name] = count
            except Exception as e:
                logging.error(f"Failed to import {apkg_file.name}: {e}")
                results[apkg_file.name] = 0

        return results

    def get_due_cards(self, deck_name: str = None) -> List[FlashCard]:
        """Get cards due for review"""
        cards_list = list(self.cards.values())
        if deck_name:
            cards_list = [card for card in cards_list if card.deck_name == deck_name]

        return self.engine.get_due_cards(cards_list)

    def get_new_cards(self, deck_name: str = None, limit: int = 20) -> List[FlashCard]:
        """Get new cards for review"""
        cards_list = list(self.cards.values())
        if deck_name:
            cards_list = [card for card in cards_list if card.deck_name == deck_name]

        return self.engine.get_new_cards(cards_list, limit)

    def review_card(self, card_id: str, quality: int) -> FlashCard:
        """Review a card and update its spaced repetition data"""
        if card_id in self.cards:
            card = self.cards[card_id]
            updated_card = self.engine.calculate_next_review(card, quality)
            self.cards[card_id] = updated_card
            self._save_cards()
            return updated_card
        else:
            raise ValueError(f"Card {card_id} not found")

    def start_review_session(self, deck_name: str = None) -> str:
        """Start a new review session"""
        session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"

        session = ReviewSession(
            session_id=session_id,
            deck_name=deck_name or "All Decks",
            start_time=datetime.now().isoformat()
        )

        self.sessions.append(session)
        return session_id

    def end_review_session(self, session_id: str, cards_reviewed: int, cards_correct: int):
        """End a review session"""
        for session in self.sessions:
            if session.session_id == session_id:
                session.end_time = datetime.now().isoformat()
                session.cards_reviewed = cards_reviewed
                session.cards_correct = cards_correct
                session.cards_wrong = cards_reviewed - cards_correct
                break

        self._save_sessions()

    def get_deck_stats(self, deck_name: str = None) -> Dict[str, Any]:
        """Get statistics for a deck or all decks"""
        cards_list = list(self.cards.values())
        if deck_name:
            cards_list = [card for card in cards_list if card.deck_name == deck_name]

        total_cards = len(cards_list)
        new_cards = len([card for card in cards_list if card.repetitions == 0])
        due_cards = len(self.engine.get_due_cards(cards_list))

        # Calculate accuracy
        total_reviews = sum(card.total_reviews for card in cards_list)
        correct_reviews = sum(card.correct_reviews for card in cards_list)
        accuracy = (correct_reviews / total_reviews * 100) if total_reviews > 0 else 0

        return {
            'total_cards': total_cards,
            'new_cards': new_cards,
            'due_cards': due_cards,
            'total_reviews': total_reviews,
            'accuracy': accuracy,
            'deck_name': deck_name or 'All Decks'
        }

    def get_all_decks(self) -> List[str]:
        """Get list of all deck names"""
        deck_names = set(card.deck_name for card in self.cards.values())
        return sorted(list(deck_names))

if __name__ == "__main__":
    # Test the flashcard system
    manager = FlashcardManager()

    # Import all Anki decks from downloads
    print("Importing Anki decks from Downloads folder...")
    results = manager.import_all_from_downloads()

    for deck_name, count in results.items():
        print(f"{deck_name}: {count} cards imported")

    # Show deck statistics
    print("\nDeck Statistics:")
    for deck_name in manager.get_all_decks():
        stats = manager.get_deck_stats(deck_name)
        print(f"{deck_name}: {stats['total_cards']} total, {stats['new_cards']} new, {stats['due_cards']} due")