# src/multimedia/video_manager.py
"""
Video management system for radiology study materials
Handles local videos, online resources, and lecture integration
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
import re
from urllib.parse import urlparse, parse_qs
import datetime
import subprocess

# Optional dependencies for video metadata
try:
    from moviepy.editor import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False

class VideoManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Video directories
        self.video_dirs = [
            "data/videos/lectures",
            "data/videos/cases",
            "data/videos/tutorials"
        ]

        # Create directories
        for directory in self.video_dirs:
            Path(directory).mkdir(parents=True, exist_ok=True)

        # Video database
        self.video_db_file = Path("data/videos/video_database.json")
        self.video_database = self.load_video_database()

        # Educational resource links
        self.educational_resources = {
            'radiopaedia': {
                'base_url': 'https://radiopaedia.org',
                'search_url': 'https://radiopaedia.org/search',
                'categories': {
                    'chest': ['pneumonia', 'pulmonary-embolism', 'lung-cancer', 'pneumothorax'],
                    'neuro': ['stroke', 'intracranial-hemorrhage', 'brain-tumor', 'head-trauma'],
                    'abdomen': ['appendicitis', 'bowel-obstruction', 'liver-lesions', 'pancreatitis'],
                    'msk': ['fractures', 'arthritis', 'bone-tumors', 'sports-injuries'],
                    'physics': ['ct-physics', 'mri-physics', 'radiation-safety', 'image-quality']
                }
            },
            'youtube_channels': {
                'radiology_education': [
                    {'name': 'Radiology Education', 'channel_id': 'UC1234567890'},
                    {'name': 'CTisus', 'channel_id': 'UC2345678901'},
                    {'name': 'Radiopaedia', 'channel_id': 'UC3456789012'}
                ],
                'physics_education': [
                    {'name': 'Radiologic Physics', 'channel_id': 'UC4567890123'},
                    {'name': 'Medical Physics', 'channel_id': 'UC5678901234'}
                ]
            }
        }

    def load_video_database(self) -> Dict:
        """Load video database from file"""
        if self.video_db_file.exists():
            try:
                with open(self.video_db_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error loading video database: {e}")

        return {
            'local_videos': {},
            'online_resources': {},
            'playlists': {},
            'last_updated': None
        }

    def save_video_database(self):
        """Save video database to file"""
        try:
            with open(self.video_db_file, 'w') as f:
                json.dump(self.video_database, f, indent=2)
        except Exception as e:
            self.logger.error(f"Error saving video database: {e}")

    def scan_local_videos(self) -> Dict:
        """Scan for local video files and add to database"""

        video_extensions = ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']
        found_videos = {}

        for video_dir in self.video_dirs:
            if not os.path.exists(video_dir):
                continue

            category = os.path.basename(video_dir)
            found_videos[category] = []

            for root, dirs, files in os.walk(video_dir):
                for file in files:
                    if any(file.lower().endswith(ext) for ext in video_extensions):
                        file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(file_path, video_dir)

                        video_info = self.extract_video_metadata(file_path, file)
                        video_info['path'] = file_path
                        video_info['relative_path'] = relative_path
                        video_info['category'] = category

                        found_videos[category].append(video_info)

                        # Add to database
                        video_id = f"{category}_{len(found_videos[category])}"
                        self.video_database['local_videos'][video_id] = video_info

        self.save_video_database()
        self.logger.info(f"Scanned and found {sum(len(videos) for videos in found_videos.values())} local videos")

        return found_videos

    def extract_video_metadata(self, file_path: str, filename: str) -> Dict:
        """Extract comprehensive metadata from video filename and content"""

        # Basic metadata from filename
        name_without_ext = os.path.splitext(filename)[0]

        # Initialize metadata structure
        metadata = {
            'title': self.parse_video_title(name_without_ext),
            'filename': filename,
            'original_filename': name_without_ext,
            'file_size': os.path.getsize(file_path) if os.path.exists(file_path) else 0,
            'duration': self.get_video_duration(file_path),
            'duration_formatted': None,
            'topics': [],
            'difficulty': 'intermediate',
            'speaker': None,
            'video_number': None,
            'series': None,
            'date': None,
            'category': None
        }

        # Format duration if available
        if metadata['duration']:
            metadata['duration_formatted'] = self.format_duration(metadata['duration'])

        # Parse filename for detailed information
        parsed_info = self.parse_filename_details(name_without_ext)
        metadata.update(parsed_info)

        # Extract topics from filename patterns
        radiology_terms = [
            'chest', 'neuro', 'abdomen', 'msk', 'physics', 'safety',
            'ct', 'mri', 'xray', 'ultrasound', 'nuclear', 'mammography',
            'pneumonia', 'stroke', 'fracture', 'tumor', 'cancer', 'angiography',
            'pediatric', 'emergency', 'trauma', 'spine', 'cardiac'
        ]

        filename_lower = filename.lower()
        for term in radiology_terms:
            if term in filename_lower:
                metadata['topics'].append(term)

        return metadata

    def parse_video_title(self, filename: str) -> str:
        """Parse and clean video title from filename"""
        title = filename

        # Remove common prefixes
        prefixes_to_remove = [
            r'^[0-9]+[\-\._\s]*',  # Leading numbers
            r'^boardsbuster[\-\._\s]*[0-9]*[\-\._\s]*',  # BoardsBuster prefix
            r'^boards?[\-\._\s]*buster[\-\._\s]*[0-9]*[\-\._\s]*',  # Boards Buster variations
            r'^lecture[\-\._\s]*[0-9]*[\-\._\s]*',  # Lecture prefix
            r'^video[\-\._\s]*[0-9]*[\-\._\s]*',  # Video prefix
            r'^[^a-zA-Z]*',  # Leading non-letters
        ]

        for prefix in prefixes_to_remove:
            title = re.sub(prefix, '', title, flags=re.IGNORECASE)

        # Replace separators with spaces
        title = re.sub(r'[\-\._]+', ' ', title)

        # Clean up multiple spaces
        title = re.sub(r'\s+', ' ', title)

        # Capitalize properly
        title = title.strip().title()

        return title if title else filename

    def parse_filename_details(self, filename: str) -> Dict:
        """Extract detailed information from filename"""
        details = {
            'speaker': None,
            'video_number': None,
            'series': None,
            'difficulty': 'intermediate'
        }

        filename_lower = filename.lower()

        # Extract video number
        number_patterns = [
            r'(?:video|lecture|part|episode|session)[\s\-_]*(\d+)',
            r'(\d+)[\s\-_]*(?:video|lecture|part|episode|session)',
            r'^(\d+)[\s\-_]',  # Number at start
            r'[\s\-_](\d+)$',  # Number at end
        ]

        for pattern in number_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                details['video_number'] = match.group(1)
                break

        # Extract speaker names
        speaker_patterns = [
            r'dr\.?\s+([a-z]{3,})',  # Dr. Name
            r'prof\.?\s+([a-z]{3,})',  # Prof. Name
            r'([a-z]{3,})\s+lecture',  # Name Lecture
            r'lecture.*?by\s+([a-z]{3,})',  # Lecture by Name
            r'([a-z]{3,})\s+md',  # Name MD
            r'([a-z]{3,})\s+([a-z]{3,})\s+(?:lecture|presentation)',  # Full Name
        ]

        for pattern in speaker_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                speaker_name = match.group(1).title()
                if len(speaker_name) > 2:  # Avoid single letters or short words
                    details['speaker'] = speaker_name
                    break

        # Extract series information
        series_patterns = [
            r'(board\s*buster)', r'(core\s*radiology)', r'(radiology\s*review)',
            r'(physics\s*review)', r'(case\s*review)', r'(subspecialty\s*series)'
        ]

        for pattern in series_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                details['series'] = match.group(1).title()
                break

        # Extract difficulty
        if any(word in filename_lower for word in ['beginner', 'basic', 'intro', 'fundamentals']):
            details['difficulty'] = 'Basic'
        elif any(word in filename_lower for word in ['advanced', 'expert', 'complex', 'fellowship']):
            details['difficulty'] = 'Advanced'
        elif any(word in filename_lower for word in ['intermediate', 'standard', 'core']):
            details['difficulty'] = 'Intermediate'

        return details

    def get_video_duration(self, file_path: str) -> Optional[float]:
        """Get video duration in seconds using multiple methods"""
        if not os.path.exists(file_path):
            return None

        # Method 1: Try MoviePy (most accurate)
        if MOVIEPY_AVAILABLE:
            try:
                with VideoFileClip(file_path) as clip:
                    return clip.duration
            except Exception:
                pass

        # Method 2: Try ffprobe (if available)
        try:
            result = subprocess.run([
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_entries', 'format=duration', file_path
            ], capture_output=True, text=True, timeout=10)

            if result.returncode == 0:
                import json
                data = json.loads(result.stdout)
                return float(data['format']['duration'])
        except Exception:
            pass

        # Method 3: Try ffmpeg (if available)
        try:
            result = subprocess.run([
                'ffmpeg', '-i', file_path, '-f', 'null', '-'
            ], capture_output=True, text=True, timeout=10)

            duration_line = None
            for line in result.stderr.split('\n'):
                if 'Duration:' in line:
                    duration_line = line
                    break

            if duration_line:
                time_match = re.search(r'Duration: (\d+):(\d+):(\d+\.?\d*)', duration_line)
                if time_match:
                    hours, minutes, seconds = time_match.groups()
                    total_seconds = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
                    return total_seconds
        except Exception:
            pass

        return None

    def format_duration(self, seconds: float) -> str:
        """Format duration in seconds to readable format"""
        if seconds is None:
            return "Unknown"

        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"

    def add_online_resource(self, resource_type: str, topic: str,
                          url: str, title: str, description: str = "") -> str:
        """Add online educational resource"""

        resource_id = f"{resource_type}_{topic}_{len(self.video_database['online_resources'])}"

        resource_info = {
            'type': resource_type,  # 'radiopaedia', 'youtube', 'other'
            'topic': topic,
            'url': url,
            'title': title,
            'description': description,
            'added_date': Path().stat().st_mtime,
            'view_count': 0,
            'rating': None
        }

        self.video_database['online_resources'][resource_id] = resource_info
        self.save_video_database()

        return resource_id

    def get_radiopaedia_links(self, topic: str, section: str = None) -> List[Dict]:
        """Generate Radiopaedia links for specific topics"""

        links = []

        # Get relevant search terms for the topic
        search_terms = []

        if section and section.lower() in self.educational_resources['radiopaedia']['categories']:
            search_terms = self.educational_resources['radiopaedia']['categories'][section.lower()]

        # Add topic-specific terms
        topic_terms = self.generate_topic_search_terms(topic)
        search_terms.extend(topic_terms)

        # Create Radiopaedia links
        for term in search_terms[:5]:  # Limit to top 5 most relevant
            link = {
                'title': f"Radiopaedia: {term.replace('-', ' ').title()}",
                'url': f"https://radiopaedia.org/articles/{term}",
                'type': 'radiopaedia',
                'relevance': self.calculate_relevance(topic, term)
            }
            links.append(link)

        # Sort by relevance
        links.sort(key=lambda x: x['relevance'], reverse=True)

        return links

    def get_youtube_recommendations(self, topic: str, section: str = None) -> List[Dict]:
        """Generate YouTube search recommendations"""

        # Create search queries for YouTube
        search_queries = self.generate_youtube_searches(topic, section)

        recommendations = []
        for query in search_queries[:3]:  # Top 3 searches
            youtube_link = {
                'title': f"YouTube: {query}",
                'url': f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
                'type': 'youtube_search',
                'query': query,
                'relevance': len(query.split())  # Simple relevance scoring
            }
            recommendations.append(youtube_link)

        return recommendations

    def generate_topic_search_terms(self, topic: str) -> List[str]:
        """Generate relevant search terms for a topic"""

        # Topic mappings for better search results
        topic_mappings = {
            'pneumonia': ['pneumonia', 'consolidation', 'air-bronchograms', 'lung-infection'],
            'stroke': ['stroke', 'cerebral-infarction', 'ischemia', 'hemorrhage'],
            'fracture': ['fracture', 'bone-break', 'trauma', 'orthopaedic-injury'],
            'appendicitis': ['appendicitis', 'acute-abdomen', 'appendix', 'inflammation'],
            'pe': ['pulmonary-embolism', 'pe', 'blood-clot', 'pulmonary-artery'],
            'ct': ['ct-scan', 'computed-tomography', 'ct-physics', 'hounsfield-units'],
            'mri': ['mri', 'magnetic-resonance', 'mri-physics', 'signal-intensity']
        }

        topic_lower = topic.lower()

        # Direct mapping
        if topic_lower in topic_mappings:
            return topic_mappings[topic_lower]

        # Partial matching
        for key, terms in topic_mappings.items():
            if key in topic_lower or topic_lower in key:
                return terms

        # Default: use the topic itself
        return [topic.lower().replace(' ', '-')]

    def generate_youtube_searches(self, topic: str, section: str = None) -> List[str]:
        """Generate YouTube search queries"""

        base_queries = [
            f"radiology {topic} tutorial",
            f"{topic} imaging board review",
            f"{topic} radiology lecture"
        ]

        if section:
            section_specific = [
                f"{section} {topic} radiology",
                f"{topic} {section} imaging"
            ]
            base_queries.extend(section_specific)

        return base_queries

    def calculate_relevance(self, topic: str, search_term: str) -> float:
        """Calculate relevance score between topic and search term"""

        topic_words = set(topic.lower().split())
        term_words = set(search_term.lower().replace('-', ' ').split())

        # Simple Jaccard similarity
        intersection = len(topic_words.intersection(term_words))
        union = len(topic_words.union(term_words))

        if union == 0:
            return 0.0

        return intersection / union

    def create_study_playlist(self, topic: str, include_local: bool = True,
                            include_online: bool = True) -> Dict:
        """Create a comprehensive study playlist for a topic"""

        playlist = {
            'topic': topic,
            'created_date': Path().stat().st_mtime,
            'local_videos': [],
            'online_resources': [],
            'total_duration': 0,
            'difficulty_mix': {'easy': 0, 'intermediate': 0, 'hard': 0}
        }

        # Add local videos
        if include_local:
            for video_id, video_info in self.video_database['local_videos'].items():
                if topic.lower() in [t.lower() for t in video_info.get('topics', [])] or \
                   topic.lower() in video_info.get('title', '').lower():
                    playlist['local_videos'].append({
                        'id': video_id,
                        'title': video_info['title'],
                        'path': video_info['path'],
                        'difficulty': video_info.get('difficulty', 'intermediate'),
                        'duration': video_info.get('duration')
                    })

                    # Update difficulty mix
                    difficulty = video_info.get('difficulty', 'intermediate')
                    playlist['difficulty_mix'][difficulty] += 1

        # Add online resources
        if include_online:
            # Radiopaedia links
            radiopaedia_links = self.get_radiopaedia_links(topic)
            for link in radiopaedia_links[:3]:  # Top 3
                playlist['online_resources'].append(link)

            # YouTube recommendations
            youtube_links = self.get_youtube_recommendations(topic)
            for link in youtube_links[:2]:  # Top 2
                playlist['online_resources'].append(link)

        # Save playlist
        playlist_id = f"playlist_{topic.lower().replace(' ', '_')}"
        self.video_database['playlists'][playlist_id] = playlist
        self.save_video_database()

        return playlist

    def get_video_embed_html(self, video_path: str) -> str:
        """Generate HTML for embedding local video"""

        if not os.path.exists(video_path):
            return f"<p>Video not found: {video_path}</p>"

        # Convert to relative path for web serving
        relative_path = os.path.relpath(video_path, os.getcwd()).replace('\\', '/')

        return f"""
        <video width="100%" height="400" controls>
            <source src="{relative_path}" type="video/mp4">
            <source src="{relative_path}" type="video/webm">
            <source src="{relative_path}" type="video/ogg">
            Your browser does not support the video tag.
        </video>
        """

    def get_youtube_embed_html(self, youtube_url: str) -> str:
        """Generate YouTube embed HTML"""

        # Extract video ID from various YouTube URL formats
        video_id = self.extract_youtube_id(youtube_url)

        if not video_id:
            return f"<p>Invalid YouTube URL: {youtube_url}</p>"

        return f"""
        <iframe width="100%" height="400"
                src="https://www.youtube.com/embed/{video_id}"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen>
        </iframe>
        """

    def extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""

        # Common YouTube URL patterns
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([^&\n?#]+)',
            r'youtube\.com/watch\?.*?v=([^&\n?#]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)

        return None

    def get_multimedia_study_plan(self, topic: str, study_time_minutes: int = 60) -> Dict:
        """Create a multimedia study plan for a topic"""

        plan = {
            'topic': topic,
            'total_time_minutes': study_time_minutes,
            'segments': [],
            'resources': []
        }

        # Time allocation
        video_time = int(study_time_minutes * 0.4)  # 40% for videos
        reading_time = int(study_time_minutes * 0.3)  # 30% for reading
        practice_time = int(study_time_minutes * 0.3)  # 30% for practice

        # Add video segment
        playlist = self.create_study_playlist(topic)
        if playlist['local_videos'] or playlist['online_resources']:
            plan['segments'].append({
                'type': 'video_review',
                'duration_minutes': video_time,
                'content': 'Watch lectures and educational videos',
                'resources': playlist
            })

        # Add reading segment
        plan['segments'].append({
            'type': 'knowledge_base_review',
            'duration_minutes': reading_time,
            'content': f'Review knowledge base materials on {topic}',
            'resources': {'query': topic}
        })

        # Add practice segment
        plan['segments'].append({
            'type': 'practice_questions',
            'duration_minutes': practice_time,
            'content': f'Practice questions related to {topic}',
            'resources': {'topic': topic, 'question_count': 10}
        })

        return plan

    def get_recommended_videos_for_question(self, question_topic: str,
                                          question_section: str) -> List[Dict]:
        """Get recommended videos for a specific question topic"""

        recommendations = []

        # Local videos
        for video_id, video_info in self.video_database['local_videos'].items():
            relevance = 0

            # Check topic match
            if question_topic.lower() in [t.lower() for t in video_info.get('topics', [])]:
                relevance += 3

            # Check title match
            if question_topic.lower() in video_info.get('title', '').lower():
                relevance += 2

            # Check section match
            if question_section.lower() in video_info.get('title', '').lower():
                relevance += 1

            if relevance > 0:
                recommendations.append({
                    'type': 'local',
                    'title': video_info['title'],
                    'path': video_info['path'],
                    'relevance': relevance,
                    'id': video_id
                })

        # Online resources
        radiopaedia_links = self.get_radiopaedia_links(question_topic, question_section)
        for link in radiopaedia_links[:2]:
            recommendations.append({
                'type': 'radiopaedia',
                'title': link['title'],
                'url': link['url'],
                'relevance': link['relevance']
            })

        youtube_links = self.get_youtube_recommendations(question_topic, question_section)
        for link in youtube_links[:1]:
            recommendations.append({
                'type': 'youtube',
                'title': link['title'],
                'url': link['url'],
                'relevance': link['relevance']
            })

        # Sort by relevance
        recommendations.sort(key=lambda x: x['relevance'], reverse=True)

        return recommendations[:5]  # Top 5 recommendations