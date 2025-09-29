#!/usr/bin/env python3
"""
Flashcard Deduplication Tool
Identifies and removes duplicate or extremely similar flashcards
"""

import os
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from difflib import SequenceMatcher
import hashlib

@dataclass
class DuplicateGroup:
    """Group of similar flashcards"""
    primary_card_id: str
    duplicate_card_ids: List[str]
    similarity_score: float
    group_type: str  # 'exact', 'very_similar', 'similar'

class FlashcardDeduplicator:
    """Detects and removes duplicate flashcards"""

    def __init__(self, cards_file: str = "data/flashcards/cards.json"):
        self.cards_file = Path(cards_file)
        self.cards_data = {}
        self.duplicate_groups = []

        # Similarity thresholds
        self.EXACT_THRESHOLD = 1.0
        self.VERY_SIMILAR_THRESHOLD = 0.95
        self.SIMILAR_THRESHOLD = 0.85

    def load_cards(self):
        """Load flashcards from JSON file"""
        if not self.cards_file.exists():
            print(f"ERROR: Cards file not found: {self.cards_file}")
            return False

        try:
            with open(self.cards_file, 'r', encoding='utf-8') as f:
                self.cards_data = json.load(f)
            print(f"SUCCESS: Loaded {len(self.cards_data)} flashcards")
            return True
        except Exception as e:
            print(f"ERROR: Error loading cards: {e}")
            return False

    def normalize_text(self, text: str) -> str:
        """Normalize text for comparison"""
        if not text:
            return ""

        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)

        # Remove extra whitespace and normalize
        text = ' '.join(text.split())

        # Convert to lowercase
        text = text.lower().strip()

        # Remove common formatting variations
        text = re.sub(r'[^\w\s]', ' ', text)  # Remove punctuation
        text = ' '.join(text.split())  # Normalize spaces again

        return text

    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two texts"""
        norm1 = self.normalize_text(text1)
        norm2 = self.normalize_text(text2)

        if not norm1 or not norm2:
            return 0.0

        if norm1 == norm2:
            return 1.0

        return SequenceMatcher(None, norm1, norm2).ratio()

    def get_card_hash(self, card_data: dict) -> str:
        """Generate hash for card content"""
        front = self.normalize_text(card_data.get('front', ''))
        back = self.normalize_text(card_data.get('back', ''))
        combined = f"{front}|{back}"
        return hashlib.md5(combined.encode()).hexdigest()

    def find_duplicates(self) -> List[DuplicateGroup]:
        """Find all duplicate groups"""
        print("Scanning for duplicates...")

        card_items = list(self.cards_data.items())
        processed_cards = set()
        duplicate_groups = []

        # First pass: Find exact duplicates by hash
        hash_groups = {}
        for card_id, card_data in card_items:
            card_hash = self.get_card_hash(card_data)
            if card_hash not in hash_groups:
                hash_groups[card_hash] = []
            hash_groups[card_hash].append(card_id)

        # Process hash groups with duplicates
        for card_hash, card_ids in hash_groups.items():
            if len(card_ids) > 1:
                primary_id = card_ids[0]  # Keep first one
                duplicates = card_ids[1:]

                duplicate_groups.append(DuplicateGroup(
                    primary_card_id=primary_id,
                    duplicate_card_ids=duplicates,
                    similarity_score=1.0,
                    group_type='exact'
                ))

                processed_cards.update(card_ids)

        # Second pass: Find similar cards (not exact duplicates)
        remaining_cards = [(cid, cdata) for cid, cdata in card_items
                          if cid not in processed_cards]

        for i, (card_id1, card_data1) in enumerate(remaining_cards):
            if card_id1 in processed_cards:
                continue

            similar_cards = []

            for j, (card_id2, card_data2) in enumerate(remaining_cards[i+1:], i+1):
                if card_id2 in processed_cards:
                    continue

                # Compare front and back similarity
                front_sim = self.calculate_similarity(
                    card_data1.get('front', ''),
                    card_data2.get('front', '')
                )
                back_sim = self.calculate_similarity(
                    card_data1.get('back', ''),
                    card_data2.get('back', '')
                )

                # Combined similarity (weighted toward front)
                combined_sim = (front_sim * 0.6) + (back_sim * 0.4)

                if combined_sim >= self.SIMILAR_THRESHOLD:
                    similar_cards.append((card_id2, combined_sim))
                    processed_cards.add(card_id2)

            if similar_cards:
                # Determine group type based on highest similarity
                max_sim = max(sim for _, sim in similar_cards)
                if max_sim >= self.VERY_SIMILAR_THRESHOLD:
                    group_type = 'very_similar'
                else:
                    group_type = 'similar'

                duplicate_groups.append(DuplicateGroup(
                    primary_card_id=card_id1,
                    duplicate_card_ids=[cid for cid, _ in similar_cards],
                    similarity_score=max_sim,
                    group_type=group_type
                ))

                processed_cards.add(card_id1)

        self.duplicate_groups = duplicate_groups
        return duplicate_groups

    def display_duplicates(self):
        """Display found duplicates for review"""
        if not self.duplicate_groups:
            print("SUCCESS: No duplicates found!")
            return

        total_duplicates = sum(len(group.duplicate_card_ids) for group in self.duplicate_groups)
        print(f"\nFOUND: {len(self.duplicate_groups)} duplicate groups containing {total_duplicates} duplicate cards")

        # Group by type
        exact_groups = [g for g in self.duplicate_groups if g.group_type == 'exact']
        very_similar_groups = [g for g in self.duplicate_groups if g.group_type == 'very_similar']
        similar_groups = [g for g in self.duplicate_groups if g.group_type == 'similar']

        print(f"  - Exact duplicates: {len(exact_groups)} groups")
        print(f"  - Very similar: {len(very_similar_groups)} groups")
        print(f"  - Similar: {len(similar_groups)} groups")

        # Show examples
        print("\nSample duplicate groups:")

        for i, group in enumerate(self.duplicate_groups[:5]):  # Show first 5
            primary_card = self.cards_data[group.primary_card_id]

            print(f"\n  Group {i+1} ({group.group_type}, {group.similarity_score:.2f}):")
            print(f"    PRIMARY: {primary_card.get('front', '')[:100]}...")
            print(f"             {primary_card.get('back', '')[:100]}...")

            for dup_id in group.duplicate_card_ids[:2]:  # Show first 2 duplicates
                dup_card = self.cards_data[dup_id]
                print(f"    DUPLICATE: {dup_card.get('front', '')[:100]}...")

            if len(group.duplicate_card_ids) > 2:
                print(f"    ... and {len(group.duplicate_card_ids) - 2} more")

    def remove_duplicates(self, auto_remove_exact: bool = True,
                         auto_remove_very_similar: bool = False) -> Dict:
        """Remove duplicate cards"""
        if not self.duplicate_groups:
            return {"removed": 0, "groups_processed": 0}

        removed_cards = []

        for group in self.duplicate_groups:
            should_remove = False

            if group.group_type == 'exact' and auto_remove_exact:
                should_remove = True
            elif group.group_type == 'very_similar' and auto_remove_very_similar:
                should_remove = True

            if should_remove:
                for dup_id in group.duplicate_card_ids:
                    if dup_id in self.cards_data:
                        del self.cards_data[dup_id]
                        removed_cards.append(dup_id)

        return {
            "removed": len(removed_cards),
            "groups_processed": len([g for g in self.duplicate_groups
                                   if (g.group_type == 'exact' and auto_remove_exact) or
                                      (g.group_type == 'very_similar' and auto_remove_very_similar)])
        }

    def save_cleaned_cards(self, backup: bool = True):
        """Save cleaned flashcard data"""
        if backup:
            backup_file = self.cards_file.with_suffix('.backup.json')
            print(f"Creating backup: {backup_file}")

            try:
                with open(self.cards_file, 'r', encoding='utf-8') as f:
                    original_data = f.read()
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(original_data)
            except Exception as e:
                print(f"WARNING: Backup failed: {e}")

        try:
            with open(self.cards_file, 'w', encoding='utf-8') as f:
                json.dump(self.cards_data, f, indent=2, ensure_ascii=False)
            print(f"SUCCESS: Cleaned flashcards saved: {len(self.cards_data)} cards remaining")
            return True
        except Exception as e:
            print(f"ERROR: Error saving cards: {e}")
            return False

def main():
    """Main deduplication process"""
    print("ECHO Flashcard Deduplicator")
    print("=" * 40)

    deduplicator = FlashcardDeduplicator()

    # Load cards
    if not deduplicator.load_cards():
        return

    # Find duplicates
    duplicates = deduplicator.find_duplicates()

    # Display results
    deduplicator.display_duplicates()

    if duplicates:
        print("\nAuto-removal settings:")
        print("  - Exact duplicates: AUTO-REMOVE")
        print("  - Very similar cards: MANUAL REVIEW")
        print("  - Similar cards: MANUAL REVIEW")

        # Remove exact duplicates automatically
        result = deduplicator.remove_duplicates(
            auto_remove_exact=True,
            auto_remove_very_similar=False
        )

        print(f"\nSUCCESS: Removed {result['removed']} exact duplicate cards")
        print(f"INFO: {result['groups_processed']} groups processed automatically")

        # Save cleaned data
        if result['removed'] > 0:
            deduplicator.save_cleaned_cards(backup=True)

        # Summary
        remaining_similar = len([g for g in duplicates if g.group_type in ['very_similar', 'similar']])
        if remaining_similar > 0:
            print(f"\nINFO: Manual review needed for {remaining_similar} similar groups")
            print("   Run with manual review mode to handle these cases.")

if __name__ == "__main__":
    main()