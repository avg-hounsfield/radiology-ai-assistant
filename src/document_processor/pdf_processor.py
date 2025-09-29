# src/document_processor/pdf_processor.py
import pymupdf
from typing import List, Dict
import re
import logging

class PDFProcessor:
    def __init__(self):
        self.chunk_size = 1000
        self.overlap = 200
        self.logger = logging.getLogger(__name__)
    
    def extract_text_and_metadata(self, pdf_path: str) -> Dict:
        """Extract text and metadata without problematic image processing"""
        doc = pymupdf.open(pdf_path)
        content = {
            'text': '',
            'metadata': {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'pages': doc.page_count,
                'source': pdf_path
            },
            'pages': []
        }
        
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            
            # Skip image extraction to avoid PNG errors
            # We'll focus on text content for now
            content['pages'].append({
                'page_num': page_num + 1,  # 1-indexed for user display
                'text': text,
                'has_images': len(page.get_images()) > 0  # Just note if images exist
            })
            content['text'] += text + '\n'
        
        doc.close()  # Important: close the document
        return content
    
    def semantic_chunking(self, text: str, metadata: Dict) -> List[Dict]:
        """Medical-specific chunking logic"""
        sections = self._identify_medical_sections(text)
        chunks = []
        
        for section in sections:
            if len(section['text']) > self.chunk_size:
                # Split large sections while preserving context
                sub_chunks = self._split_with_overlap(section['text'])
                for i, chunk_text in enumerate(sub_chunks):
                    chunks.append({
                        'text': chunk_text,
                        'metadata': {
                            **metadata,
                            'section': section['title'],
                            'chunk_id': f"{section['title']}_{i}",
                            'chunk_type': 'text'
                        }
                    })
            else:
                chunks.append({
                    'text': section['text'],
                    'metadata': {
                        **metadata,
                        'section': section['title'],
                        'chunk_type': 'text'
                    }
                })
        
        return chunks
    
    def _identify_medical_sections(self, text: str) -> List[Dict]:
        """Identify medical sections: Anatomy, Pathology, Imaging, etc."""
        section_patterns = [
            # Medical section headers
            r'(?i)^(anatomy|pathology|clinical features|imaging findings|differential diagnosis|treatment|management).*$',
            r'(?i)^(case \d+|patient \d+).*$', 
            r'(?i)^(introduction|conclusion|discussion|references|summary).*$',
            # Radiology-specific sections
            r'(?i)^(technique|protocol|indications|contraindications|complications).*$',
            r'(?i)^(ct findings|mri findings|x-ray findings|ultrasound findings).*$',
            # Physics sections
            r'(?i)^(radiation safety|dose|image quality|artifacts).*$'
        ]
        
        sections = []
        current_section = {'title': 'General Content', 'text': ''}
        
        lines = text.split('\n')
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                current_section['text'] += '\n'
                continue
            
            # Check if line is a section header
            is_header = False
            for pattern in section_patterns:
                if re.search(pattern, line_stripped):
                    # Save previous section if it has content
                    if current_section['text'].strip():
                        sections.append(current_section)
                    
                    # Start new section
                    current_section = {
                        'title': line_stripped[:100],  # Limit title length
                        'text': ''
                    }
                    is_header = True
                    break
            
            if not is_header:
                current_section['text'] += line + '\n'
        
        # Add final section
        if current_section['text'].strip():
            sections.append(current_section)
        
        # If no sections found, create one big section
        if not sections:
            sections = [{
                'title': 'Document Content',
                'text': text
            }]
        
        return sections
    
    def _split_with_overlap(self, text: str) -> List[str]:
        """Split text into overlapping chunks"""
        # Split by sentences first to preserve meaning
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # If adding this sentence would exceed chunk size
            if current_length + sentence_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-2:] if len(current_chunk) >= 2 else current_chunk
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(len(s) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_length += sentence_length
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks if chunks else [text]  # Fallback to original text