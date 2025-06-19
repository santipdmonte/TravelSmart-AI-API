import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, Optional
from markitdown import MarkItDown
from openai import OpenAI

class DocumentAnalyzer:
    def __init__(self, openai_api_key: Optional[str] = None, openai_model: str = "gpt-4o-mini"):
        """
        Initialize the Document Analyzer
        
        Args:
            openai_api_key: OpenAI API key for image analysis (optional)
            openai_model: OpenAI model to use for image descriptions
        """
        self.openai_client = None
        self.openai_model = openai_model
        
        # Initialize OpenAI client if API key is provided
        if openai_api_key:
            self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Initialize MarkItDown with or without LLM support
        if self.openai_client:
            self.md = MarkItDown(llm_client=self.openai_client, llm_model=self.openai_model)
        else:
            self.md = MarkItDown(enable_plugins=False)
    
    def detect_file_type(self, file_path: str) -> Dict[str, Any]:
        """
        Detect file type and return relevant information
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary containing file type information
        """
        file_path = Path(file_path)
        
        # Get file extension
        extension = file_path.suffix.lower()
        
        # Get MIME type
        mime_type, _ = mimetypes.guess_type(str(file_path))
        
        # File size
        file_size = file_path.stat().st_size if file_path.exists() else 0
        
        # Categorize file type
        file_category = self._categorize_file(extension, mime_type)
        
        return {
            "filename": file_path.name,
            "extension": extension,
            "mime_type": mime_type,
            "file_size": file_size,
            "file_category": file_category,
            "supports_markitdown": self._supports_markitdown(extension, mime_type)
        }
    
    def _categorize_file(self, extension: str, mime_type: str) -> str:
        """Categorize file based on extension and MIME type"""
        
        # Office documents
        office_extensions = {'.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls'}
        if extension in office_extensions:
            return "office_document"
        
        # PDF
        if extension == '.pdf' or (mime_type and 'pdf' in mime_type):
            return "pdf"
        
        # Images
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        if extension in image_extensions or (mime_type and mime_type.startswith('image/')):
            return "image"
        
        # Text/Data formats
        text_extensions = {'.txt', '.csv', '.json', '.xml', '.html', '.htm', '.md', '.yml', '.yaml'}
        if extension in text_extensions or (mime_type and mime_type.startswith('text/')):
            return "text_data"
        
        # Archive
        archive_extensions = {'.zip', '.rar', '.7z', '.tar', '.gz'}
        if extension in archive_extensions:
            return "archive"
        
        return "unknown"
    
    def _supports_markitdown(self, extension: str, mime_type: str) -> bool:
        """Check if file type is supported by MarkItDown"""
        supported_extensions = {
            '.pdf', '.docx', '.doc', '.pptx', '.ppt', '.xlsx', '.xls',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp',
            '.html', '.htm', '.txt', '.csv', '.json', 
            '.xml', '.zip', '.md'
        }
        return extension in supported_extensions
    
    def analyze_document(self, file_path: str) -> Dict[str, Any]:
        """
        Analyze a document and extract text content using appropriate method
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Dictionary containing analysis results
        """
        try:
            # Detect file type
            file_info = self.detect_file_type(file_path)
            
            result = {
                "file_info": file_info,
                "success": False,
                "text_content": "",
                "extraction_method": "",
                "error": None
            }
            
            if not Path(file_path).exists():
                result["error"] = "File does not exist"
                return result
            
            # Check file size limit (20MB)
            max_size = 20 * 1024 * 1024  # 20MB in bytes
            if file_info["file_size"] > max_size:
                result["error"] = f"File size ({file_info['file_size']} bytes) exceeds 20MB limit"
                return result
            
            if not file_info["supports_markitdown"]:
                result["error"] = f"File type '{file_info['file_category']}' not supported by MarkItDown"
                return result
            
            # Use appropriate MarkItDown method based on file category
            extraction_method = self._get_extraction_method(file_info)
            result["extraction_method"] = extraction_method
            
            # Extract text using MarkItDown
            markitdown_result = self.md.convert(file_path)
            result["text_content"] = markitdown_result.text_content
            result["success"] = True
            
            # Add specific notes based on file type
            result["notes"] = self._get_extraction_notes(file_info)
            
            return result
            
        except Exception as e:
            return {
                "file_info": file_info if 'file_info' in locals() else {},
                "success": False,
                "text_content": "",
                "extraction_method": "",
                "error": str(e),
                "notes": []
            }
    
    def _get_extraction_method(self, file_info: Dict[str, Any]) -> str:
        """Get the extraction method used based on file type"""
        category = file_info["file_category"]
        
        method_map = {
            "office_document": "Office document parsing (mammoth, pandas, pptx)",
            "pdf": "PDF text extraction (pdfminer)",
            "image": "OCR + LLM description" if self.openai_client else "EXIF metadata only",
            "text_data": "Direct text parsing",
            "archive": "Recursive content extraction"
        }
        
        return method_map.get(category, "Standard MarkItDown conversion")
    
    def _get_extraction_notes(self, file_info: Dict[str, Any]) -> list:
        """Get specific notes about the extraction process"""
        notes = []
        category = file_info["file_category"]
        
        if category == "pdf":
            notes.append("PDF formatting may be lost during extraction")
            notes.append("Image-based PDFs require OCR preprocessing")
        
        elif category == "image" and not self.openai_client:
            notes.append("No LLM client configured - only EXIF metadata extracted")
            notes.append("For image descriptions, provide OpenAI API key")
        
        elif category == "office_document":
            notes.append("Formatting and styling preserved as Markdown")
            notes.append("Complex layouts may need manual review")
        
        elif category == "text_data":
            notes.append("Direct text parsing - formatting preserved")
        
        elif category == "archive":
            notes.append("Extracts content from all files within the archive")
            notes.append("Large archives may take longer to process")
        
        return notes

# Example usage and testing
def main():
    # Example usage
    analyzer = DocumentAnalyzer()
    
    # Test file (you would replace this with actual file path)
    test_file = "document_analyzer/pdf_example.pdf"
    
    if os.path.exists(test_file):
        result = analyzer.analyze_document(test_file)
        
        print("=== Document Analysis Results ===")
        print(f"File: {result['file_info']['filename']}")
        print(f"Type: {result['file_info']['file_category']}")
        print(f"Extension: {result['file_info']['extension']}")
        print(f"MIME Type: {result['file_info']['mime_type']}")
        print(f"Size: {result['file_info']['file_size']} bytes")
        print(f"Extraction Method: {result['extraction_method']}")
        print(f"Success: {result['success']}")
        
        if result['notes']:
            print("\nNotes:")
            for note in result['notes']:
                print(f"- {note}")
        
        if result['success']:
            print(f"\nExtracted Text (first 500 chars):")
            print(result['text_content'][:500] + "..." if len(result['text_content']) > 500 else result['text_content'])
        else:
            print(f"\nError: {result['error']}")
    else:
        print(f"Test file {test_file} not found")

if __name__ == "__main__":
    main()