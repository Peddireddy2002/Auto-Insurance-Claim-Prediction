import os
import io
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from pdf2image import convert_from_path, convert_from_bytes
import numpy as np
import cv2
from config.settings import settings

# Configure logging
logger = logging.getLogger(__name__)


class PDFProcessor:
    """Advanced PDF processing and OCR extraction utility."""
    
    def __init__(self):
        """Initialize PDF processor with configuration."""
        self.tesseract_cmd = settings.tesseract_cmd
        self.poppler_path = settings.poppler_path
        
        # Configure Tesseract
        if self.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd
        
        # OCR configuration
        self.ocr_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz .,:-/$'
    
    def extract_text_from_pdf(self, file_path: str) -> Dict[str, Any]:
        """
        Extract text from PDF using multiple methods for best results.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            result = {
                "text": "",
                "pages": [],
                "method_used": "",
                "confidence": 0.0,
                "metadata": {}
            }
            
            # Method 1: Try extracting text directly (for text-based PDFs)
            text_extraction_result = self._extract_text_directly(file_path)
            
            if text_extraction_result["text"].strip():
                result.update(text_extraction_result)
                result["method_used"] = "direct_text_extraction"
                result["confidence"] = 0.95
                logger.info(f"Direct text extraction successful for {file_path}")
                return result
            
            # Method 2: OCR extraction (for scanned PDFs or images)
            ocr_result = self._extract_text_with_ocr(file_path)
            result.update(ocr_result)
            result["method_used"] = "ocr_extraction"
            logger.info(f"OCR extraction completed for {file_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            return {
                "text": "",
                "pages": [],
                "method_used": "error",
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    def _extract_text_directly(self, file_path: str) -> Dict[str, Any]:
        """Extract text directly from PDF using PyMuPDF."""
        try:
            doc = fitz.open(file_path)
            pages = []
            full_text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text()
                
                pages.append({
                    "page_number": page_num + 1,
                    "text": text,
                    "word_count": len(text.split())
                })
                
                full_text += text + "\n"
            
            doc.close()
            
            return {
                "text": full_text.strip(),
                "pages": pages,
                "metadata": {
                    "total_pages": len(pages),
                    "total_words": len(full_text.split())
                }
            }
            
        except Exception as e:
            logger.error(f"Direct text extraction failed: {str(e)}")
            return {"text": "", "pages": [], "metadata": {"error": str(e)}}
    
    def _extract_text_with_ocr(self, file_path: str) -> Dict[str, Any]:
        """Extract text using OCR after converting PDF to images."""
        try:
            # Convert PDF to images
            images = convert_from_path(
                file_path,
                dpi=300,
                poppler_path=self.poppler_path if self.poppler_path else None
            )
            
            pages = []
            full_text = ""
            total_confidence = 0.0
            
            for i, image in enumerate(images):
                # Preprocess image for better OCR
                processed_image = self._preprocess_image(image)
                
                # Extract text with confidence scores
                ocr_data = pytesseract.image_to_data(
                    processed_image,
                    config=self.ocr_config,
                    output_type=pytesseract.Output.DICT
                )
                
                # Calculate page-level confidence
                confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
                page_confidence = np.mean(confidences) if confidences else 0.0
                
                # Extract text
                page_text = pytesseract.image_to_string(
                    processed_image,
                    config=self.ocr_config
                )
                
                pages.append({
                    "page_number": i + 1,
                    "text": page_text,
                    "confidence": page_confidence,
                    "word_count": len(page_text.split())
                })
                
                full_text += page_text + "\n"
                total_confidence += page_confidence
            
            average_confidence = total_confidence / len(pages) if pages else 0.0
            
            return {
                "text": full_text.strip(),
                "pages": pages,
                "confidence": average_confidence / 100.0,  # Normalize to 0-1
                "metadata": {
                    "total_pages": len(pages),
                    "total_words": len(full_text.split()),
                    "average_confidence": average_confidence
                }
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {str(e)}")
            return {
                "text": "",
                "pages": [],
                "confidence": 0.0,
                "metadata": {"error": str(e)}
            }
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """
        Preprocess image for better OCR results.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image
        """
        try:
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Convert to grayscale
            gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
            
            # Apply denoising
            denoised = cv2.fastNlMeansDenoising(gray)
            
            # Apply adaptive thresholding
            thresh = cv2.adaptiveThreshold(
                denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
            )
            
            # Morphological operations to clean up
            kernel = np.ones((1, 1), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
            
            # Convert back to PIL Image
            return Image.fromarray(cleaned)
            
        except Exception as e:
            logger.warning(f"Image preprocessing failed, using original: {str(e)}")
            return image
    
    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """
        Extract text from image files using OCR.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary containing extracted text and metadata
        """
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            processed_image = self._preprocess_image(image)
            
            # Extract text with confidence
            ocr_data = pytesseract.image_to_data(
                processed_image,
                config=self.ocr_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Calculate confidence
            confidences = [int(conf) for conf in ocr_data['conf'] if int(conf) > 0]
            average_confidence = np.mean(confidences) if confidences else 0.0
            
            # Extract text
            text = pytesseract.image_to_string(processed_image, config=self.ocr_config)
            
            return {
                "text": text.strip(),
                "confidence": average_confidence / 100.0,  # Normalize to 0-1
                "method_used": "image_ocr",
                "metadata": {
                    "word_count": len(text.split()),
                    "average_confidence": average_confidence,
                    "image_size": image.size
                }
            }
            
        except Exception as e:
            logger.error(f"Image OCR failed for {image_path}: {str(e)}")
            return {
                "text": "",
                "confidence": 0.0,
                "method_used": "error",
                "metadata": {"error": str(e)}
            }
    
    def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data patterns from text.
        
        Args:
            text: Extracted text from document
            
        Returns:
            Dictionary containing structured data
        """
        import re
        
        structured_data = {
            "dates": [],
            "amounts": [],
            "phone_numbers": [],
            "emails": [],
            "license_plates": [],
            "policy_numbers": [],
            "claim_numbers": []
        }
        
        try:
            # Extract dates (various formats)
            date_patterns = [
                r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
                r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',
                r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}\b'
            ]
            
            for pattern in date_patterns:
                structured_data["dates"].extend(re.findall(pattern, text, re.IGNORECASE))
            
            # Extract monetary amounts
            amount_patterns = [
                r'\$[\d,]+\.?\d*',
                r'USD [\d,]+\.?\d*',
                r'\b\d+\.\d{2}\b'
            ]
            
            for pattern in amount_patterns:
                structured_data["amounts"].extend(re.findall(pattern, text))
            
            # Extract phone numbers
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            structured_data["phone_numbers"] = re.findall(phone_pattern, text)
            
            # Extract email addresses
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            structured_data["emails"] = re.findall(email_pattern, text)
            
            # Extract license plates (basic pattern)
            license_pattern = r'\b[A-Z]{1,3}[0-9]{1,4}[A-Z]?\b'
            structured_data["license_plates"] = re.findall(license_pattern, text)
            
            # Extract policy numbers
            policy_pattern = r'\b(?:POL|POLICY)[:\s]*([A-Z0-9-]+)\b'
            structured_data["policy_numbers"] = re.findall(policy_pattern, text, re.IGNORECASE)
            
            # Extract claim numbers
            claim_pattern = r'\b(?:CLM|CLAIM)[:\s]*([A-Z0-9-]+)\b'
            structured_data["claim_numbers"] = re.findall(claim_pattern, text, re.IGNORECASE)
            
            # Remove duplicates
            for key in structured_data:
                structured_data[key] = list(set(structured_data[key]))
            
            return structured_data
            
        except Exception as e:
            logger.error(f"Structured data extraction failed: {str(e)}")
            return structured_data
    
    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate file format and properties.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Validation results
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                return {"valid": False, "error": "File does not exist"}
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > settings.max_file_size:
                return {
                    "valid": False,
                    "error": f"File size ({file_size} bytes) exceeds maximum allowed ({settings.max_file_size} bytes)"
                }
            
            # Check file extension
            file_extension = file_path.suffix.lower().lstrip('.')
            if file_extension not in settings.allowed_extensions:
                return {
                    "valid": False,
                    "error": f"File extension '{file_extension}' not allowed. Allowed: {settings.allowed_extensions}"
                }
            
            # Additional PDF validation
            if file_extension == 'pdf':
                try:
                    doc = fitz.open(str(file_path))
                    page_count = len(doc)
                    doc.close()
                    
                    if page_count == 0:
                        return {"valid": False, "error": "PDF has no pages"}
                    
                    if page_count > 50:  # Reasonable limit
                        return {"valid": False, "error": "PDF has too many pages (max 50)"}
                        
                except Exception as e:
                    return {"valid": False, "error": f"Invalid PDF file: {str(e)}"}
            
            return {
                "valid": True,
                "file_size": file_size,
                "file_type": file_extension,
                "metadata": {
                    "name": file_path.name,
                    "size_mb": round(file_size / (1024 * 1024), 2)
                }
            }
            
        except Exception as e:
            return {"valid": False, "error": f"File validation error: {str(e)}"}


# Global instance
pdf_processor = PDFProcessor()