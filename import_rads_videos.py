#!/usr/bin/env python3
"""
Import script for Radiology HDD video collection
Scans X:\Subfolders\Rads HDD recursively for video files and imports them
"""

import os
import sys
import shutil
from pathlib import Path
import logging
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Video file extensions to look for
VIDEO_EXTENSIONS = {
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
    '.m4v', '.3gp', '.f4v', '.asf', '.rm', '.rmvb', '.vob'
}

def scan_for_videos(source_dir):
    """Scan directory recursively for video files"""

    videos_found = defaultdict(list)
    total_size = 0

    logging.info(f"Scanning {source_dir} for video files...")

    try:
        for root, dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                file_ext = file_path.suffix.lower()

                if file_ext in VIDEO_EXTENSIONS:
                    try:
                        file_size = file_path.stat().st_size
                        size_mb = file_size / (1024 * 1024)

                        # Categorize by parent directory name
                        parent_dir = Path(root).name

                        video_info = {
                            'file_path': str(file_path),
                            'filename': file,
                            'size_mb': round(size_mb, 2),
                            'parent_dir': parent_dir,
                            'relative_path': str(file_path.relative_to(source_dir))
                        }

                        videos_found[parent_dir].append(video_info)
                        total_size += size_mb

                        logging.info(f"Found: {file} ({size_mb:.1f}MB) in {parent_dir}")

                    except (OSError, PermissionError) as e:
                        logging.warning(f"Could not access {file_path}: {e}")

    except Exception as e:
        logging.error(f"Error scanning directory: {e}")
        return None, 0

    logging.info(f"Scan complete: {sum(len(v) for v in videos_found.values())} videos found ({total_size:.1f}MB total)")
    return videos_found, total_size

def categorize_videos(videos_found):
    """Categorize videos based on directory names and content"""

    categorized = {
        'lectures': [],
        'cases': [],
        'tutorials': [],
        'reviews': [],
        'physics': [],
        'uncategorized': []
    }

    # Keywords for categorization
    lecture_keywords = ['lecture', 'course', 'teaching', 'symposium', 'conference', 'review']
    case_keywords = ['case', 'cases', 'differential', 'diagnosis']
    tutorial_keywords = ['tutorial', 'how', 'guide', 'intro', 'basic']
    review_keywords = ['review', 'prep', 'board', 'exam', 'core']
    physics_keywords = ['physics', 'technical', 'protocol']

    for parent_dir, videos in videos_found.items():
        dir_lower = parent_dir.lower()

        for video in videos:
            filename_lower = video['filename'].lower()

            # Determine category based on directory and filename
            if any(keyword in dir_lower or keyword in filename_lower for keyword in physics_keywords):
                categorized['physics'].append(video)
            elif any(keyword in dir_lower or keyword in filename_lower for keyword in case_keywords):
                categorized['cases'].append(video)
            elif any(keyword in dir_lower or keyword in filename_lower for keyword in tutorial_keywords):
                categorized['tutorials'].append(video)
            elif any(keyword in dir_lower or keyword in filename_lower for keyword in review_keywords):
                categorized['reviews'].append(video)
            elif any(keyword in dir_lower or keyword in filename_lower for keyword in lecture_keywords):
                categorized['lectures'].append(video)
            else:
                categorized['uncategorized'].append(video)

    return categorized

def import_videos(videos_found, target_base_dir, copy_files=False):
    """Import videos into the multimedia system structure"""

    target_base = Path(target_base_dir)

    # Create target directories
    target_dirs = {
        'lectures': target_base / 'videos' / 'lectures',
        'cases': target_base / 'videos' / 'cases',
        'tutorials': target_base / 'videos' / 'tutorials',
        'reviews': target_base / 'videos' / 'reviews',
        'physics': target_base / 'videos' / 'physics',
        'uncategorized': target_base / 'videos' / 'uncategorized'
    }

    for dir_path in target_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {dir_path}")

    # Categorize videos
    categorized = categorize_videos(videos_found)

    # Import videos
    imported_count = 0
    skipped_count = 0

    for category, videos in categorized.items():
        if not videos:
            continue

        logging.info(f"\nProcessing {category} videos ({len(videos)} files)...")

        for video in videos:
            source_path = Path(video['file_path'])

            # Create descriptive filename
            original_name = source_path.stem
            extension = source_path.suffix
            parent_info = video['parent_dir'].replace(' ', '_')

            # Clean filename
            safe_name = f"{parent_info}_{original_name}".replace(' ', '_')
            safe_name = ''.join(c for c in safe_name if c.isalnum() or c in '._-')

            target_file = target_dirs[category] / f"{safe_name}{extension}"

            # Handle duplicate names
            counter = 1
            while target_file.exists():
                target_file = target_dirs[category] / f"{safe_name}_{counter}{extension}"
                counter += 1

            try:
                if copy_files:
                    # Copy file
                    shutil.copy2(source_path, target_file)
                    logging.info(f"Copied: {video['filename']} -> {target_file.name}")
                else:
                    # Create symbolic link (faster, saves space)
                    if os.name == 'nt':  # Windows
                        target_file.symlink_to(source_path)
                    else:  # Unix-like
                        target_file.symlink_to(source_path)
                    logging.info(f"Linked: {video['filename']} -> {target_file.name}")

                imported_count += 1

            except Exception as e:
                logging.error(f"Failed to import {video['filename']}: {e}")
                skipped_count += 1

    logging.info(f"\nImport complete: {imported_count} imported, {skipped_count} skipped")
    return imported_count, skipped_count

def create_video_index(videos_found, target_base_dir):
    """Create an index file of all imported videos"""

    index_file = Path(target_base_dir) / 'videos' / 'video_index.txt'

    with open(index_file, 'w', encoding='utf-8') as f:
        f.write("RADIOLOGY VIDEO COLLECTION INDEX\n")
        f.write("=" * 50 + "\n\n")

        total_videos = sum(len(v) for v in videos_found.values())
        total_size = sum(sum(video['size_mb'] for video in videos) for videos in videos_found.values())

        f.write(f"Total Videos: {total_videos}\n")
        f.write(f"Total Size: {total_size:.1f} MB\n\n")

        for parent_dir, videos in videos_found.items():
            if videos:
                f.write(f"{parent_dir} ({len(videos)} videos)\n")
                f.write("-" * len(parent_dir) + "\n")

                for video in videos:
                    f.write(f"  {video['filename']} ({video['size_mb']} MB)\n")
                    f.write(f"    Path: {video['relative_path']}\n")

                f.write("\n")

    logging.info(f"Video index created: {index_file}")

def main():
    """Main import function"""

    source_directory = r"X:\Subfolders\Rads HDD"
    target_directory = "data"

    print("=" * 60)
    print("RADIOLOGY VIDEO IMPORT SYSTEM")
    print("=" * 60)

    # Check if source exists
    if not Path(source_directory).exists():
        logging.error(f"Source directory not found: {source_directory}")
        return False

    # Scan for videos
    logging.info("Step 1: Scanning for video files...")
    videos_found, total_size = scan_for_videos(source_directory)

    if not videos_found:
        logging.error("No videos found or scan failed")
        return False

    # Show summary
    total_videos = sum(len(v) for v in videos_found.values())
    print(f"\nSCAN RESULTS:")
    print(f"Total videos found: {total_videos}")
    print(f"Total size: {total_size:.1f} MB ({total_size/1024:.1f} GB)")

    print(f"\nDirectory breakdown:")
    for parent_dir, videos in videos_found.items():
        if videos:
            dir_size = sum(video['size_mb'] for video in videos)
            # Clean directory name for display
            clean_dir = ''.join(c if ord(c) < 128 else '?' for c in parent_dir)
            print(f"  {clean_dir}: {len(videos)} videos ({dir_size:.1f} MB)")

    # Ask user preference
    print(f"\nImport options:")
    print("1. Create symbolic links (fast, saves space)")
    print("2. Copy files (slower, uses more space)")
    print("3. Index only (no file operations)")

    choice = input("\nChoose option (1-3) [1]: ").strip() or "1"

    if choice == "3":
        # Index only
        logging.info("Step 2: Creating video index...")
        create_video_index(videos_found, target_directory)
        print("Video index created successfully!")
        return True

    copy_files = choice == "2"

    # Import videos
    logging.info(f"Step 2: Importing videos ({'copying' if copy_files else 'linking'})...")
    imported, skipped = import_videos(videos_found, target_directory, copy_files)

    # Create index
    logging.info("Step 3: Creating video index...")
    create_video_index(videos_found, target_directory)

    print(f"\nIMPORT COMPLETE!")
    print(f"Imported: {imported} videos")
    print(f"Skipped: {skipped} videos")
    print(f"Videos organized in: data/videos/")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)