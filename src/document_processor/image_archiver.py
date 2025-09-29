# src/document_processor/image_archiver.py
"""
Image archiving system for radiology documents with automatic tagging
"""

import os
import json
import hashlib
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import logging
from pathlib import Path
import re

try:
    from PIL import Image
    import io
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available. Install with: pip install Pillow")

class RadiologyImageArchiver:
    def __init__(self, base_archive_path: str = "./data/images"):
        self.base_path = Path(base_archive_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "extracted").mkdir(exist_ok=True)
        (self.base_path / "metadata").mkdir(exist_ok=True)
        (self.base_path / "thumbnails").mkdir(exist_ok=True)
        
        self.logger = logging.getLogger(__name__)
        
        # Medical imaging keywords for tagging
        self.medical_tags = {
            'modality': {
                'ct': ['ct scan', 'computed tomography', 'axial', 'coronal', 'sagittal', 'hounsfield'],
                'mri': ['mri', 'magnetic resonance', 't1', 't2', 'flair', 'dwi', 'adc', 'gadolinium'],
                'xray': ['x-ray', 'radiograph', 'chest x-ray', 'plain film', 'projection'],
                'ultrasound': ['ultrasound', 'sonogram', 'doppler', 'echocardiogram', 'echo'],
                'nuclear': ['pet', 'spect', 'bone scan', 'nuclear medicine', 'scintigraphy'],
                'mammography': ['mammogram', 'tomosynthesis', 'breast imaging', 'bi-rads'],
                'fluoroscopy': ['fluoroscopy', 'barium', 'contrast swallow', 'angiogram']
            },
            'anatomy': {
                'chest': ['lung', 'heart', 'mediastinum', 'pleura', 'chest', 'thorax', 'pulmonary'],
                'abdomen': ['liver', 'kidney', 'spleen', 'pancreas', 'bowel', 'abdomen', 'pelvis'],
                'brain': ['brain', 'cerebral', 'intracranial', 'skull', 'head', 'neurologic'],
                'spine': ['spine', 'vertebra', 'spinal', 'cervical', 'thoracic', 'lumbar'],
                'extremities': ['arm', 'leg', 'hand', 'foot', 'bone', 'joint', 'fracture'],
                'cardiac': ['cardiac', 'coronary', 'myocardial', 'pericardial', 'valve']
            },
            'pathology': {
                'tumor': ['tumor', 'mass', 'neoplasm', 'cancer', 'malignant', 'metastasis'],
                'infection': ['infection', 'pneumonia', 'abscess', 'inflammatory', 'sepsis'],
                'trauma': ['fracture', 'trauma', 'injury', 'hematoma', 'contusion'],
                'vascular': ['aneurysm', 'stenosis', 'occlusion', 'thrombosis', 'embolism'],
                'congenital': ['congenital', 'anomaly', 'developmental', 'agenesis']
            },
            'findings': {
                'normal': ['normal', 'unremarkable', 'within limits', 'no abnormality'],
                'abnormal': ['abnormal', 'lesion', 'opacity', 'enhancement', 'signal', 'density'],
                'acute': ['acute', 'recent', 'new', 'fresh', 'active'],
                'chronic': ['chronic', 'old', 'stable', 'unchanged', 'longstanding']
            }
        }
    
    def extract_and_archive_images(self, pdf_doc, document_metadata: Dict, 
                                 context_text: str = "") -> List[Dict]:
        """Extract images from PDF and archive with tags"""
        archived_images = []
        
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc[page_num]
            page_text = page.get_text()
            
            # Get images from this page
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    # Extract image data safely
                    image_data = self._safe_extract_image(pdf_doc, img, page_num, img_index)
                    
                    if image_data:
                        # Generate tags based on context
                        tags = self._generate_image_tags(
                            page_text, 
                            context_text, 
                            document_metadata, 
                            page_num, 
                            img_index
                        )
                        
                        # Archive the image
                        archived_info = self._archive_image(
                            image_data, 
                            document_metadata, 
                            page_num, 
                            img_index, 
                            tags
                        )
                        
                        if archived_info:
                            archived_images.append(archived_info)
                            
                except Exception as e:
                    self.logger.warning(f"Failed to process image {img_index} on page {page_num}: {e}")
                    continue
        
        return archived_images
    
    def _safe_extract_image(self, pdf_doc, img, page_num: int, img_index: int) -> Optional[bytes]:
        """Safely extract image data with error handling"""
        try:
            xref = img[0]
            
            # Try different extraction methods
            try:
                # Method 1: Direct pixmap extraction
                pix = pdf_doc.extract_image(xref)
                if pix and 'image' in pix:
                    return pix['image']
            except Exception as e1:
                self.logger.debug(f"Method 1 failed for image {img_index}: {e1}")
                
                try:
                    # Method 2: Pixmap conversion
                    pix = pymupdf.Pixmap(pdf_doc, xref)
                    
                    # Handle different colorspaces
                    if pix.n - pix.alpha > 3:  # CMYK or other complex colorspace
                        pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                    
                    # Convert to PNG bytes
                    img_data = pix.tobytes("png")
                    pix = None  # Clean up
                    return img_data
                    
                except Exception as e2:
                    self.logger.debug(f"Method 2 failed for image {img_index}: {e2}")
                    
                    try:
                        # Method 3: JPEG fallback
                        pix = pymupdf.Pixmap(pdf_doc, xref)
                        if pix.n - pix.alpha <= 3:  # RGB or grayscale
                            img_data = pix.tobytes("jpeg")
                            pix = None
                            return img_data
                    except Exception as e3:
                        self.logger.warning(f"All extraction methods failed for image {img_index}: {e3}")
                        return None
        
        except Exception as e:
            self.logger.error(f"Critical error extracting image {img_index} on page {page_num}: {e}")
            return None
    
    def _generate_image_tags(self, page_text: str, context_text: str, 
                           document_metadata: Dict, page_num: int, 
                           img_index: int) -> Dict:
        """Generate descriptive tags for the image based on context"""
        
        # Combine all text for analysis
        full_text = f"{page_text} {context_text}".lower()
        
        tags = {
            'automatic': [],
            'modality': [],
            'anatomy': [],
            'pathology': [],
            'findings': [],
            'metadata': {
                'document_source': document_metadata.get('source', 'unknown'),
                'page_number': page_num + 1,
                'image_index': img_index,
                'extraction_date': datetime.now().isoformat(),
                'document_title': document_metadata.get('title', ''),
                'document_author': document_metadata.get('author', '')
            }
        }
        
        # Analyze text for medical tags
        for category, subcategories in self.medical_tags.items():
            for subcat, keywords in subcategories.items():
                for keyword in keywords:
                    if keyword in full_text:
                        tags[category].append(subcat)
                        tags['automatic'].append(f"{category}:{subcat}")
        
        # Remove duplicates
        for key in ['modality', 'anatomy', 'pathology', 'findings', 'automatic']:
            tags[key] = list(set(tags[key]))
        
        # Add context-based tags
        tags['context'] = {
            'nearby_text': self._extract_nearby_text(page_text, 200),
            'page_title': self._extract_page_title(page_text),
            'figure_caption': self._extract_figure_caption(page_text, img_index)
        }
        
        # Confidence scoring
        tags['confidence'] = {
            'modality_confidence': len(tags['modality']) > 0,
            'anatomy_confidence': len(tags['anatomy']) > 0,
            'pathology_confidence': len(tags['pathology']) > 0,
            'total_tags': len(tags['automatic'])
        }
        
        return tags
    
    def _extract_nearby_text(self, page_text: str, char_limit: int = 200) -> str:
        """Extract text that might describe the image"""
        # Look for figure/image references
        patterns = [
            r'(?i)(figure|fig|image|diagram|illustration).*?[.!?]',
            r'(?i)(shows?|demonstrates?|illustrates?).*?[.!?]',
            r'(?i)(see|refer to|shown in).*?[.!?]'
        ]
        
        relevant_text = []
        for pattern in patterns:
            matches = re.findall(pattern, page_text)
            relevant_text.extend(matches)
        
        if relevant_text:
            return ' '.join(relevant_text)[:char_limit]
        else:
            # Return first few sentences as fallback
            sentences = re.split(r'[.!?]+', page_text)
            return ' '.join(sentences[:3])[:char_limit]
    
    def _extract_page_title(self, page_text: str) -> str:
        """Try to extract page or section title"""
        lines = page_text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line and len(line) < 100:  # Reasonable title length
                # Check if it looks like a title (not a sentence)
                if not line.endswith('.') and len(line.split()) <= 10:
                    return line
        return ""
    
    def _extract_figure_caption(self, page_text: str, img_index: int) -> str:
        """Try to find figure caption"""
        patterns = [
            rf'(?i)figure\s*{img_index + 1}[:\.]?\s*([^.!?]*[.!?])',
            rf'(?i)fig\s*{img_index + 1}[:\.]?\s*([^.!?]*[.!?])',
            r'(?i)(figure|fig)[:\.]?\s*([^.!?]*[.!?])'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, page_text)
            if match:
                return match.group(1) if len(match.groups()) > 0 else match.group(0)
        
        return ""
    
    def _archive_image(self, image_data: bytes, document_metadata: Dict, 
                      page_num: int, img_index: int, tags: Dict) -> Optional[Dict]:
        """Archive image with metadata and tags"""
        
        try:
            # Generate unique filename
            content_hash = hashlib.md5(image_data).hexdigest()[:12]
            doc_name = Path(document_metadata.get('source', 'unknown')).stem
            filename = f"{doc_name}_p{page_num + 1}_img{img_index}_{content_hash}"
            
            # Determine file extension based on data
            if image_data.startswith(b'\x89PNG'):
                ext = '.png'
            elif image_data.startswith(b'\xff\xd8'):
                ext = '.jpg'  
            else:
                ext = '.img'  # Generic
            
            image_path = self.base_path / "extracted" / f"{filename}{ext}"
            metadata_path = self.base_path / "metadata" / f"{filename}.json"
            
            # Save image
            with open(image_path, 'wb') as f:
                f.write(image_data)
            
            # Create thumbnail if PIL is available
            thumbnail_path = None
            if PIL_AVAILABLE:
                thumbnail_path = self._create_thumbnail(image_data, filename)
            
            # Prepare metadata
            archive_metadata = {
                'filename': filename + ext,
                'original_source': document_metadata.get('source'),
                'page_number': page_num + 1,
                'image_index': img_index,
                'file_size': len(image_data),
                'content_hash': content_hash,
                'archived_date': datetime.now().isoformat(),
                'tags': tags,
                'paths': {
                    'image': str(image_path),
                    'metadata': str(metadata_path),
                    'thumbnail': str(thumbnail_path) if thumbnail_path else None
                }
            }
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(archive_metadata, f, indent=2)
            
            self.logger.info(f"✅ Archived image: {filename}{ext}")
            
            return archive_metadata
            
        except Exception as e:
            self.logger.error(f"❌ Failed to archive image: {e}")
            return None
    
    def _create_thumbnail(self, image_data: bytes, filename: str) -> Optional[Path]:
        """Create thumbnail using PIL"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Create thumbnail (max 200x200)
            image.thumbnail((200, 200), Image.Resampling.LANCZOS)
            
            # Save as JPEG for smaller file size
            thumbnail_path = self.base_path / "thumbnails" / f"{filename}_thumb.jpg"
            
            # Convert to RGB if necessary
            if image.mode in ('RGBA', 'P', 'L'):
                rgb_image = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGB')
                elif image.mode == 'RGBA':
                    rgb_image.paste(image, mask=image.split()[-1])
                    image = rgb_image
                else:  # L (grayscale)
                    image = image.convert('RGB')
            
            image.save(thumbnail_path, 'JPEG', quality=85)
            
            return thumbnail_path
            
        except Exception as e:
            self.logger.warning(f"Failed to create thumbnail for {filename}: {e}")
            return None
    
    def search_archived_images(self, query: str, tags: List[str] = None) -> List[Dict]:
        """Search archived images by tags or text"""
        results = []
        metadata_dir = self.base_path / "metadata"
        
        if not metadata_dir.exists():
            return results
        
        query_lower = query.lower() if query else ""
        
        for metadata_file in metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                # Check if query matches
                match = False
                
                # Search in tags
                if tags:
                    image_tags = metadata.get('tags', {}).get('automatic', [])
                    if any(tag in image_tags for tag in tags):
                        match = True
                
                # Search in text content
                if query_lower:
                    searchable_text = json.dumps(metadata.get('tags', {})).lower()
                    if query_lower in searchable_text:
                        match = True
                
                if match:
                    results.append(metadata)
                    
            except Exception as e:
                self.logger.warning(f"Error reading metadata {metadata_file}: {e}")
        
        return results
    
    def get_archive_stats(self) -> Dict:
        """Get statistics about archived images"""
        stats = {
            'total_images': 0,
            'total_size_mb': 0,
            'by_modality': {},
            'by_anatomy': {},
            'most_common_tags': {}
        }
        
        metadata_dir = self.base_path / "metadata"
        if not metadata_dir.exists():
            return stats
        
        all_tags = []
        
        for metadata_file in metadata_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                
                stats['total_images'] += 1
                stats['total_size_mb'] += metadata.get('file_size', 0) / (1024 * 1024)
                
                # Count by categories
                tags_data = metadata.get('tags', {})
                for modality in tags_data.get('modality', []):
                    stats['by_modality'][modality] = stats['by_modality'].get(modality, 0) + 1
                
                for anatomy in tags_data.get('anatomy', []):
                    stats['by_anatomy'][anatomy] = stats['by_anatomy'].get(anatomy, 0) + 1
                
                all_tags.extend(tags_data.get('automatic', []))
                
            except Exception as e:
                self.logger.warning(f"Error reading stats from {metadata_file}: {e}")
        
        # Count most common tags
        from collections import Counter
        tag_counts = Counter(all_tags)
        stats['most_common_tags'] = dict(tag_counts.most_common(10))
        
        return stats


# Update the PDF processor to use image archiving
def update_pdf_processor_with_images():
    return '''# Updated src/document_processor/pdf_processor.py with image archiving

import pymupdf
from typing import List, Dict
import re
import logging
from .image_archiver import RadiologyImageArchiver

class PDFProcessor:
    def __init__(self):
        self.chunk_size = 1000
        self.overlap = 200
        self.logger = logging.getLogger(__name__)
        self.image_archiver = RadiologyImageArchiver()
    
    def extract_text_and_metadata(self, pdf_path: str) -> Dict:
        """Extract text, metadata, and archive images"""
        doc = pymupdf.open(pdf_path)
        content = {
            'text': '',
            'metadata': {
                'title': doc.metadata.get('title', ''),
                'author': doc.metadata.get('author', ''),
                'pages': doc.page_count,
                'source': pdf_path
            },
            'pages': [],
            'archived_images': []
        }
        
        # Extract text from all pages first
        for page_num in range(doc.page_count):
            page = doc[page_num]
            text = page.get_text()
            
            content['pages'].append({
                'page_num': page_num + 1,
                'text': text,
                'has_images': len(page.get_images()) > 0
            })
            content['text'] += text + '\\n'
        
        # Archive images with full document context
        try:
            archived_images = self.image_archiver.extract_and_archive_images(
                doc, content['metadata'], content['text']
            )
            content['archived_images'] = archived_images
            self.logger.info(f"📸 Archived {len(archived_images)} images from {pdf_path}")
        except Exception as e:
            self.logger.warning(f"Image archiving failed for {pdf_path}: {e}")
        
        doc.close()
        return content
        
    # ... rest of the methods remain the same ...
    '''