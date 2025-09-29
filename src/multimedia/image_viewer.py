#!/usr/bin/env python3
"""
Medical Image Viewer for Dictation Practice
Supports DICOM, standard image formats, and multi-slice viewing
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Union
import base64
from io import BytesIO

try:
    from PIL import Image, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL not available - image processing will be limited")

try:
    import pydicom
    import numpy as np
    PYDICOM_AVAILABLE = True
except ImportError:
    PYDICOM_AVAILABLE = False
    logging.warning("pydicom not available - DICOM support disabled")

class MedicalImageViewer:
    """Medical image viewer with DICOM and standard format support"""

    def __init__(self, image_dir: str = "data/dictation_images"):
        self.image_dir = Path(image_dir)
        self.image_dir.mkdir(parents=True, exist_ok=True)

        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.dcm']
        if PYDICOM_AVAILABLE:
            self.supported_formats.extend(['.dcm', '.dicom'])

        self.current_images = []
        self.current_index = 0

        logging.info(f"MedicalImageViewer initialized with support for: {', '.join(self.supported_formats)}")

    def load_images(self, image_paths: List[str]) -> bool:
        """Load a series of medical images"""
        self.current_images = []
        self.current_index = 0

        for path in image_paths:
            try:
                image_data = self._load_single_image(path)
                if image_data:
                    self.current_images.append(image_data)
            except Exception as e:
                logging.error(f"Failed to load image {path}: {e}")
                continue

        if not self.current_images:
            logging.warning("No valid images loaded")
            return False

        logging.info(f"Loaded {len(self.current_images)} images")
        return True

    def _load_single_image(self, image_path: str) -> Optional[Dict]:
        """Load a single image and return processed data"""
        path = Path(image_path)

        if not path.exists():
            # Try looking in the image directory
            path = self.image_dir / path.name
            if not path.exists():
                logging.warning(f"Image not found: {image_path}")
                return None

        file_ext = path.suffix.lower()

        if file_ext in ['.dcm', '.dicom'] and PYDICOM_AVAILABLE:
            return self._load_dicom_image(path)
        elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff'] and PIL_AVAILABLE:
            return self._load_standard_image(path)
        else:
            logging.warning(f"Unsupported image format: {file_ext}")
            return None

    def _load_dicom_image(self, path: Path) -> Optional[Dict]:
        """Load DICOM image"""
        try:
            dicom_data = pydicom.dcmread(str(path))

            # Extract pixel data
            if hasattr(dicom_data, 'pixel_array'):
                pixel_array = dicom_data.pixel_array

                # Handle different DICOM formats
                if len(pixel_array.shape) == 3:
                    # Multi-slice or RGB
                    if pixel_array.shape[2] == 3:
                        # RGB image
                        image = Image.fromarray(pixel_array)
                    else:
                        # Multi-slice - take middle slice
                        slice_index = pixel_array.shape[0] // 2
                        image = Image.fromarray(pixel_array[slice_index])
                else:
                    # Single slice grayscale
                    image = Image.fromarray(pixel_array)

                # Convert to RGB if grayscale
                if image.mode != 'RGB':
                    image = image.convert('RGB')

                # Get DICOM metadata
                metadata = {
                    'modality': getattr(dicom_data, 'Modality', 'Unknown'),
                    'study_description': getattr(dicom_data, 'StudyDescription', 'Unknown'),
                    'series_description': getattr(dicom_data, 'SeriesDescription', 'Unknown'),
                    'patient_id': getattr(dicom_data, 'PatientID', 'Unknown'),
                    'study_date': getattr(dicom_data, 'StudyDate', 'Unknown'),
                    'instance_number': getattr(dicom_data, 'InstanceNumber', 1),
                }

                return {
                    'image': image,
                    'path': str(path),
                    'type': 'dicom',
                    'metadata': metadata,
                    'original_shape': pixel_array.shape
                }

        except Exception as e:
            logging.error(f"Error loading DICOM {path}: {e}")
            return None

    def _load_standard_image(self, path: Path) -> Optional[Dict]:
        """Load standard image format"""
        try:
            image = Image.open(path)

            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')

            metadata = {
                'filename': path.name,
                'format': image.format,
                'size': image.size,
                'mode': image.mode
            }

            return {
                'image': image,
                'path': str(path),
                'type': 'standard',
                'metadata': metadata,
                'original_shape': image.size
            }

        except Exception as e:
            logging.error(f"Error loading image {path}: {e}")
            return None

    def get_current_image(self) -> Optional[Dict]:
        """Get the currently selected image"""
        if not self.current_images or self.current_index >= len(self.current_images):
            return None
        return self.current_images[self.current_index]

    def next_image(self) -> bool:
        """Move to next image"""
        if not self.current_images:
            return False

        if self.current_index < len(self.current_images) - 1:
            self.current_index += 1
            return True
        return False

    def previous_image(self) -> bool:
        """Move to previous image"""
        if not self.current_images:
            return False

        if self.current_index > 0:
            self.current_index -= 1
            return True
        return False

    def set_image_index(self, index: int) -> bool:
        """Set current image by index"""
        if not self.current_images or index < 0 or index >= len(self.current_images):
            return False

        self.current_index = index
        return True

    def get_image_count(self) -> int:
        """Get total number of loaded images"""
        return len(self.current_images)

    def get_image_info(self) -> Dict:
        """Get information about current image"""
        current = self.get_current_image()
        if not current:
            return {}

        return {
            'current_index': self.current_index + 1,
            'total_images': self.get_image_count(),
            'filename': Path(current['path']).name,
            'type': current['type'],
            'metadata': current['metadata']
        }

    def adjust_image(self, brightness: float = 1.0, contrast: float = 1.0) -> Optional[Image.Image]:
        """Adjust image brightness and contrast"""
        current = self.get_current_image()
        if not current or not PIL_AVAILABLE:
            return None

        image = current['image']

        # Adjust brightness
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(brightness)

        # Adjust contrast
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(contrast)

        return image

    def resize_image(self, width: int = None, height: int = None, maintain_aspect: bool = True) -> Optional[Image.Image]:
        """Resize image for display"""
        current = self.get_current_image()
        if not current or not PIL_AVAILABLE:
            return None

        image = current['image']

        if width is None and height is None:
            return image

        if maintain_aspect:
            image.thumbnail((width or image.width, height or image.height), Image.Resampling.LANCZOS)
            return image
        else:
            return image.resize((width or image.width, height or image.height), Image.Resampling.LANCZOS)

    def get_image_base64(self, max_width: int = 800, max_height: int = 600,
                        brightness: float = 1.0, contrast: float = 1.0) -> Optional[str]:
        """Get current image as base64 string for web display"""
        current = self.get_current_image()
        if not current or not PIL_AVAILABLE:
            return None

        try:
            # Get and process image
            image = current['image']

            # Adjust image if needed
            if brightness != 1.0 or contrast != 1.0:
                image = self.adjust_image(brightness, contrast)

            # Resize for web display
            image = self.resize_image(max_width, max_height, maintain_aspect=True)

            # Convert to base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG", quality=85)
            img_str = base64.b64encode(buffered.getvalue()).decode()

            return f"data:image/jpeg;base64,{img_str}"

        except Exception as e:
            logging.error(f"Error converting image to base64: {e}")
            return None

    def export_current_image(self, output_path: str, format: str = "JPEG") -> bool:
        """Export current image to file"""
        current = self.get_current_image()
        if not current or not PIL_AVAILABLE:
            return False

        try:
            image = current['image']
            image.save(output_path, format=format)
            logging.info(f"Image exported to {output_path}")
            return True
        except Exception as e:
            logging.error(f"Error exporting image: {e}")
            return False

    def create_sample_images(self):
        """Create sample images for testing dictation mode"""
        if not PIL_AVAILABLE:
            logging.warning("PIL not available - cannot create sample images")
            return

        try:
            # Create sample chest X-ray placeholder
            chest_img = Image.new('RGB', (512, 512), color='black')
            chest_path = self.image_dir / "sample_cxr_pneumonia.jpg"
            chest_img.save(chest_path)

            # Create sample CT head placeholder
            ct_img = Image.new('RGB', (512, 512), color='darkgray')
            ct_path = self.image_dir / "sample_ct_head_stroke.jpg"
            ct_img.save(ct_path)

            # Create sample CT abdomen placeholder
            abd_img = Image.new('RGB', (512, 512), color='gray')
            abd_path = self.image_dir / "sample_ct_appendicitis.jpg"
            abd_img.save(abd_path)

            logging.info("Created sample images for dictation practice")

        except Exception as e:
            logging.error(f"Error creating sample images: {e}")

if __name__ == "__main__":
    # Test the image viewer
    viewer = MedicalImageViewer()

    # Create sample images for testing
    viewer.create_sample_images()

    # Test loading sample images
    sample_images = [
        "sample_cxr_pneumonia.jpg",
        "sample_ct_head_stroke.jpg",
        "sample_ct_appendicitis.jpg"
    ]

    if viewer.load_images(sample_images):
        print(f"Loaded {viewer.get_image_count()} images")

        # Test navigation
        for i in range(viewer.get_image_count()):
            viewer.set_image_index(i)
            info = viewer.get_image_info()
            print(f"Image {i+1}: {info['filename']} ({info['type']})")
    else:
        print("Failed to load images")