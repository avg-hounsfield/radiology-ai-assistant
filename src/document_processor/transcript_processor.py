# src/document_processor/transcript_processor.py
"""
Specialized processor for lecture video transcripts
"""

import re
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from pathlib import Path

class LectureTranscriptProcessor:
    def __init__(self):
        self.chunk_size = 800  # Smaller for spoken content
        self.overlap = 150
        self.logger = logging.getLogger(__name__)
        
        # Patterns for lecture-specific content
        self.timestamp_patterns = [
            r'\b(\d{1,2}:\d{2}:\d{2})\b',  # HH:MM:SS
            r'\b(\d{1,2}:\d{2})\b',       # MM:SS or HH:MM
            r'\[(\d{1,2}:\d{2}:\d{2})\]', # [HH:MM:SS]
            r'(\d{1,3}:\d{2})',           # Extended minutes
        ]
        
        # Common lecture speaker patterns
        self.speaker_patterns = [
            r'^(Dr\.|Professor|Instructor|Speaker)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*:',
            r'^([A-Z_]+)\s*:',  # ALL_CAPS names
            r'^\[([^\]]+)\]\s*:',  # [Speaker Name]:
        ]
        
        # Lecture transition phrases
        self.transition_phrases = [
            'next slide', 'moving on', 'let\'s talk about', 'now we\'ll discuss',
            'so in summary', 'to summarize', 'in conclusion', 'key takeaway',
            'important to remember', 'make sure you understand', 'this is testable',
            'for the exam', 'clinically relevant', 'in practice'
        ]
        
        # Medical education keywords for enhanced tagging
        self.medical_lecture_keywords = {
            'educational_level': {
                'basic': ['introduction to', 'basics of', 'fundamentals', 'overview'],
                'intermediate': ['pathophysiology', 'mechanism', 'clinical presentation'],
                'advanced': ['differential', 'complications', 'management', 'prognosis']
            },
            'content_type': {
                'anatomy': ['anatomy', 'structure', 'location', 'position'],
                'physiology': ['function', 'mechanism', 'process', 'pathway'],
                'pathology': ['disease', 'disorder', 'abnormal', 'pathology'],
                'clinical': ['patient', 'symptoms', 'signs', 'presentation', 'case'],
                'imaging': ['image', 'scan', 'study', 'appearance', 'findings'],
                'treatment': ['treatment', 'therapy', 'management', 'intervention']
            },
            'emphasis': {
                'high_yield': ['important', 'key', 'critical', 'essential', 'must know'],
                'exam_relevant': ['test', 'exam', 'board', 'question', 'likely to see'],
                'clinical_pearls': ['pearl', 'tip', 'remember', 'don\'t forget', 'common mistake']
            }
        }
    
    def process_transcript(self, transcript_path: str) -> Dict:
        """Process lecture transcript with specialized handling"""
        
        # Read transcript
        try:
            with open(transcript_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()
        except UnicodeDecodeError:
            # Try different encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            for encoding in encodings:
                try:
                    with open(transcript_path, 'r', encoding=encoding) as f:
                        raw_text = f.read()
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode {transcript_path} with any common encoding")
        
        # Extract metadata from filename and content
        metadata = self._extract_metadata(transcript_path, raw_text)
        
        # Clean and structure transcript
        structured_content = self._structure_transcript(raw_text)
        
        # Create searchable segments
        segments = self._create_lecture_segments(structured_content, metadata)
        
        return {
            'metadata': metadata,
            'structured_content': structured_content,
            'segments': segments,
            'raw_text': raw_text,
            'processing_stats': {
                'total_segments': len(segments),
                'estimated_duration': self._estimate_duration(structured_content),
                'speaker_count': len(structured_content.get('speakers', [])),
                'topic_coverage': self._analyze_topic_coverage(raw_text)
            }
        }
    
    def _extract_metadata(self, file_path: str, content: str) -> Dict:
        """Extract metadata from transcript file and content"""
        path = Path(file_path)
        
        metadata = {
            'source': file_path,
            'filename': path.name,
            'file_type': 'lecture_transcript',
            'processed_date': datetime.now().isoformat()
        }
        
        # Extract info from filename
        filename_lower = path.stem.lower()
        
        # Detect lecture series/course
        course_patterns = [
            r'(radiology|anatomy|physiology|pathology|medicine|surgery)',
            r'(core|board|review|prep)',
            r'(lecture|session|chapter|unit)[\s_-]*(\d+)',
        ]
        
        for pattern in course_patterns:
            match = re.search(pattern, filename_lower)
            if match:
                metadata['course_info'] = match.group(0)
                break
        
        # Extract lecture number/title from filename
        title_match = re.search(r'(?:lecture|session|chapter)[\s_-]*(\d+)', filename_lower)
        if title_match:
            metadata['lecture_number'] = int(title_match.group(1))
        
        # Look for title in content (usually in first few lines)
        lines = content.split('\n')[:10]
        for line in lines:
            line_clean = line.strip()
            if line_clean and len(line_clean) > 10 and len(line_clean) < 200:
                if not re.search(r'\d{1,2}:\d{2}', line_clean):  # Not a timestamp
                    metadata['inferred_title'] = line_clean
                    break
        
        return metadata
    
    def _structure_transcript(self, raw_text: str) -> Dict:
        """Structure transcript with timestamps, speakers, and segments"""
        
        structured = {
            'segments': [],
            'speakers': set(),
            'timestamps': [],
            'has_timestamps': False,
            'has_speakers': False
        }
        
        lines = raw_text.split('\n')
        current_segment = {
            'timestamp': None,
            'speaker': None,
            'text': '',
            'line_start': 0
        }
        
        for line_num, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check for timestamp
            timestamp = self._extract_timestamp(line_stripped)
            if timestamp:
                # Save previous segment
                if current_segment['text'].strip():
                    structured['segments'].append(current_segment.copy())
                
                # Start new segment
                current_segment = {
                    'timestamp': timestamp,
                    'speaker': None,
                    'text': '',
                    'line_start': line_num
                }
                structured['timestamps'].append(timestamp)
                structured['has_timestamps'] = True
                continue
            
            # Check for speaker
            speaker = self._extract_speaker(line_stripped)
            if speaker:
                # If we have text accumulated, save it first
                if current_segment['text'].strip():
                    structured['segments'].append(current_segment.copy())
                    current_segment = {
                        'timestamp': current_segment['timestamp'],
                        'speaker': speaker,
                        'text': '',
                        'line_start': line_num
                    }
                else:
                    current_segment['speaker'] = speaker
                
                structured['speakers'].add(speaker)
                structured['has_speakers'] = True
                
                # Remove speaker name from line
                line_stripped = re.sub(self._get_speaker_pattern(speaker), '', line_stripped).strip()
                if line_stripped:
                    current_segment['text'] += line_stripped + ' '
            else:
                # Regular content line
                current_segment['text'] += line_stripped + ' '
        
        # Add final segment
        if current_segment['text'].strip():
            structured['segments'].append(current_segment)
        
        structured['speakers'] = list(structured['speakers'])
        return structured
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Extract timestamp from line"""
        for pattern in self.timestamp_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group(1)
        return None
    
    def _extract_speaker(self, line: str) -> Optional[str]:
        """Extract speaker name from line"""
        for pattern in self.speaker_patterns:
            match = re.search(pattern, line)
            if match:
                # Return the name part (not title)
                groups = match.groups()
                return groups[-1] if groups else None
        return None
    
    def _get_speaker_pattern(self, speaker: str) -> str:
        """Get regex pattern to remove speaker name"""
        return rf'^(Dr\.|Professor|Instructor)?\s*{re.escape(speaker)}\s*:\s*'
    
    def _create_lecture_segments(self, structured_content: Dict, metadata: Dict) -> List[Dict]:
        """Create searchable segments from structured content"""
        segments = []
        
        for i, segment in enumerate(structured_content['segments']):
            # Create base chunk
            chunk_text = segment['text'].strip()
            if not chunk_text:
                continue
            
            # Split long segments
            if len(chunk_text) > self.chunk_size:
                sub_chunks = self._split_lecture_segment(chunk_text)
                for j, sub_chunk in enumerate(sub_chunks):
                    chunk_metadata = self._create_segment_metadata(
                        segment, metadata, f"{i}_{j}", sub_chunk
                    )
                    segments.append({
                        'text': sub_chunk,
                        'metadata': chunk_metadata
                    })
            else:
                chunk_metadata = self._create_segment_metadata(
                    segment, metadata, str(i), chunk_text
                )
                segments.append({
                    'text': chunk_text,
                    'metadata': chunk_metadata
                })
        
        return segments
    
    def _create_segment_metadata(self, segment: Dict, base_metadata: Dict, 
                                segment_id: str, text: str) -> Dict:
        """Create metadata for lecture segment"""
        
        metadata = {
            **base_metadata,
            'segment_id': segment_id,
            'chunk_type': 'lecture_segment',
            'timestamp': segment.get('timestamp'),
            'speaker': segment.get('speaker'),
            'line_start': segment.get('line_start')
        }
        
        # Add lecture-specific tags
        lecture_tags = self._analyze_segment_content(text)
        metadata.update(lecture_tags)
        
        return metadata
    
    def _analyze_segment_content(self, text: str) -> Dict:
        """Analyze lecture segment for educational tags"""
        text_lower = text.lower()
        
        analysis = {
            'educational_level': [],
            'content_type': [],
            'emphasis_level': [],
            'transitions': [],
            'medical_relevance_score': 0
        }
        
        # Analyze content using medical lecture keywords
        for category, subcategories in self.medical_lecture_keywords.items():
            for subcat, keywords in subcategories.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        analysis[category].append(subcat)
                        analysis['medical_relevance_score'] += 2
        
        # Check for transition phrases
        for phrase in self.transition_phrases:
            if phrase in text_lower:
                analysis['transitions'].append(phrase)
                analysis['medical_relevance_score'] += 1
        
        # Remove duplicates
        for key in ['educational_level', 'content_type', 'emphasis_level', 'transitions']:
            analysis[key] = list(set(analysis[key]))
        
        # Add CORE exam relevance
        core_indicators = [
            'core exam', 'board exam', 'important for test', 'likely question',
            'differential diagnosis', 'first-line imaging', 'contraindication'
        ]
        analysis['core_exam_relevant'] = any(indicator in text_lower for indicator in core_indicators)
        
        return analysis
    
    def _split_lecture_segment(self, text: str) -> List[str]:
        """Split lecture segment preserving sentence boundaries"""
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with small overlap
                overlap_sentences = current_chunk[-1:] if current_chunk else []
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]
    
    def _estimate_duration(self, structured_content: Dict) -> Optional[str]:
        """Estimate lecture duration from timestamps"""
        timestamps = structured_content.get('timestamps', [])
        if len(timestamps) < 2:
            return None
        
        try:
            # Parse first and last timestamps
            first_time = self._parse_timestamp(timestamps[0])
            last_time = self._parse_timestamp(timestamps[-1])
            
            if first_time and last_time:
                duration = last_time - first_time
                hours = duration.seconds // 3600
                minutes = (duration.seconds % 3600) // 60
                
                if hours > 0:
                    return f"{hours}h {minutes}m"
                else:
                    return f"{minutes}m"
        except:
            pass
        
        return None
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime"""
        try:
            # Handle different formats
            if timestamp_str.count(':') == 2:  # HH:MM:SS
                time_obj = datetime.strptime(timestamp_str, '%H:%M:%S')
            elif timestamp_str.count(':') == 1:  # MM:SS or HH:MM
                parts = timestamp_str.split(':')
                if int(parts[0]) > 60:  # Likely extended minutes
                    minutes = int(parts[0])
                    seconds = int(parts[1])
                    time_obj = datetime.strptime(f"{minutes//60}:{minutes%60}:{seconds}", '%H:%M:%S')
                else:  # Regular HH:MM
                    time_obj = datetime.strptime(timestamp_str, '%H:%M')
            else:
                return None
                
            return time_obj
        except:
            return None
    
    def _analyze_topic_coverage(self, text: str) -> Dict:
        """Analyze what medical topics are covered"""
        text_lower = text.lower()
        
        # CORE exam areas
        core_areas = {
            'physics': ['physics', 'radiation', 'dose', 'technique', 'safety'],
            'chest': ['lung', 'chest', 'pulmonary', 'pneumonia', 'nodule'],
            'cardiac': ['heart', 'cardiac', 'coronary', 'echo', 'ekg'],
            'neuro': ['brain', 'head', 'neurologic', 'stroke', 'spine'],
            'gi': ['abdomen', 'liver', 'bowel', 'gi', 'gastrointestinal'],
            'gu': ['kidney', 'bladder', 'pelvis', 'prostate', 'renal'],
            'msk': ['bone', 'joint', 'fracture', 'musculoskeletal', 'spine'],
            'interventional': ['biopsy', 'drainage', 'embolization', 'catheter']
        }
        
        coverage = {}
        for area, keywords in core_areas.items():
            score = sum(text_lower.count(keyword) for keyword in keywords)
            if score > 0:
                coverage[area] = score
        
        return coverage
    
    def create_chunks(self, transcript_data: Dict) -> List[Dict]:
        """Create final chunks for embedding system"""
        return transcript_data['segments']


# Integration with main document processor
def add_transcript_support():
    """Code to add transcript support to main system"""
    return '''
# Add this to src/retrieval/rag_system.py in the process_documents method

elif doc_path.lower().endswith('.txt'):
    # Check if it looks like a transcript
    with open(doc_path, 'r', encoding='utf-8', errors='ignore') as f:
        sample = f.read(1000)
    
    # Simple heuristic: if it has timestamps or speaker patterns, treat as transcript
    if (re.search(r'\\d{1,2}:\\d{2}', sample) or 
        re.search(r'^[A-Z][a-z]+\\s*:', sample, re.MULTILINE)):
        
        transcript_processor = TranscriptProcessor()
        transcript_data = transcript_processor.process_transcript(doc_path)
        chunks = transcript_processor.create_chunks(transcript_data)
    else:
        # Regular text file processing
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        chunks = [{
            'text': content,
            'metadata': {
                'source': doc_path,
                'chunk_type': 'text_file',
                'file_type': 'plain_text'
            }
        }]
    '''