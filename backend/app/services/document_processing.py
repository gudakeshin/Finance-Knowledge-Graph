import asyncio
from pathlib import Path
from typing import Optional, Dict, Any
import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import easyocr
import logging

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Service for processing documents and extracting text
    """
    
    def __init__(self):
        self.reader = None
        try:
            self.reader = easyocr.Reader(['en'])
            logger.info("EasyOCR initialized successfully")
        except Exception as e:
            logger.warning(f"EasyOCR initialization failed: {e}. Falling back to pytesseract")
            self.reader = None
        
    def extract_text(self, file_path: str) -> str:
        """
        Extract text from document file
        """
        try:
            file_path = Path(file_path)
            
            if file_path.suffix.lower() == '.pdf':
                return self._extract_from_pdf(file_path)
            elif file_path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
                return self._extract_from_image(file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_path.suffix}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {str(e)}")
            raise
    
    def _extract_from_pdf(self, file_path: Path) -> str:
        """
        Extract text from PDF file
        """
        try:
            doc = fitz.open(str(file_path))
            text = ""
            
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text += page.get_text()
            
            doc.close()
            return text.strip()
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise
    
    def _extract_from_image(self, file_path: Path) -> str:
        """
        Extract text from image file using OCR
        """
        try:
            if self.reader:
                # Use EasyOCR for better accuracy
                results = self.reader.readtext(str(file_path))
                text = " ".join([result[1] for result in results])
                return text.strip()
            else:
                # Fallback to pytesseract
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                return text.strip()
                
        except Exception as e:
            logger.error(f"Error extracting text from image {file_path}: {str(e)}")
            # Final fallback to pytesseract
            try:
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                return text.strip()
            except Exception as fallback_error:
                logger.error(f"Fallback OCR also failed: {str(fallback_error)}")
                raise
    
    async def get_document_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get basic information about the document
        """
        try:
            file_path = Path(file_path)
            
            info = {
                "filename": file_path.name,
                "file_size": file_path.stat().st_size,
                "file_type": file_path.suffix.lower(),
                "exists": file_path.exists()
            }
            
            if file_path.suffix.lower() == '.pdf':
                doc = fitz.open(str(file_path))
                info["page_count"] = len(doc)
                info["title"] = doc.metadata.get("title", "")
                doc.close()
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting document info: {str(e)}")
            raise
    
    async def extract_structured_data(self, text: str) -> Dict[str, Any]:
        """
        Extract structured data from text
        """
        # This would contain more sophisticated parsing logic
        # For now, return basic structure
        return {
            "raw_text": text,
            "word_count": len(text.split()),
            "character_count": len(text),
            "lines": text.split('\n')
        } 