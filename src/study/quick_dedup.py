#!/usr/bin/env python3
"""
Quick Flashcard Deduplication - Focus on exact duplicates
"""

import json
import hashlib
import re
from pathlib import Path
from collections import defaultdict

def normalize_text(text):
    """Quick text normalization"""
    if not text:
        return ""

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove extra whitespace and normalize
    text = ' '.join(text.split())
    text = text.lower().strip()

    return text

def get_card_hash(card_data):
    """Generate hash for card content"""
    front = normalize_text(card_data.get('front', ''))
    back = normalize_text(card_data.get('back', ''))
    combined = f"{front}|{back}"
    return hashlib.md5(combined.encode()).hexdigest()

def quick_dedup():
    cards_file = Path("data/flashcards/cards.json")

    if not cards_file.exists():
        print("ERROR: Cards file not found")
        return

    print("Loading flashcards...")
    with open(cards_file, 'r', encoding='utf-8') as f:
        cards_data = json.load(f)

    print(f"Loaded {len(cards_data)} flashcards")

    # Group cards by hash
    hash_groups = defaultdict(list)
    for card_id, card_data in cards_data.items():
        card_hash = get_card_hash(card_data)
        hash_groups[card_hash].append(card_id)

    # Find exact duplicates
    duplicates = []
    total_duplicates = 0

    for card_hash, card_ids in hash_groups.items():
        if len(card_ids) > 1:
            duplicates.append(card_ids)
            total_duplicates += len(card_ids) - 1  # Keep one

    print(f"Found {len(duplicates)} groups with {total_duplicates} exact duplicates")

    if total_duplicates > 0:
        # Show examples
        print("\nSample duplicates:")
        for i, group in enumerate(duplicates[:3]):
            primary_card = cards_data[group[0]]
            print(f"Group {i+1}: {len(group)} copies")
            print(f"  Front: {primary_card.get('front', '')[:100]}...")

        # Create backup
        backup_file = cards_file.with_suffix('.backup.json')
        print(f"Creating backup: {backup_file}")

        with open(cards_file, 'r', encoding='utf-8') as f:
            original_data = f.read()
        with open(backup_file, 'w', encoding='utf-8') as f:
            f.write(original_data)

        # Remove duplicates (keep first in each group)
        removed_count = 0
        for group in duplicates:
            primary_id = group[0]  # Keep first
            for dup_id in group[1:]:  # Remove rest
                if dup_id in cards_data:
                    del cards_data[dup_id]
                    removed_count += 1

        # Save cleaned data
        with open(cards_file, 'w', encoding='utf-8') as f:
            json.dump(cards_data, f, indent=2, ensure_ascii=False)

        print(f"SUCCESS: Removed {removed_count} exact duplicates")
        print(f"Remaining cards: {len(cards_data)}")

    else:
        print("No exact duplicates found!")

if __name__ == "__main__":
    quick_dedup()