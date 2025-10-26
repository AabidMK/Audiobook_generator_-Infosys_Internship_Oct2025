import os
import io
import re
from typing import Tuple, List, Optional, Dict, Any
import fitz
from docx import Document
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pandas as pd

class EnhancedTextExtractor:
    def __init__(self, tesseract_path: Optional[str] = None):
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        else:
            pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    
    def preprocess_image(self, image: Image.Image) -> Image.Image:
        """Enhanced image preprocessing for better OCR"""
        try:
            # Convert to grayscale
            image = image.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(2.5)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(image)
            image = enhancer.enhance(2.0)
            
            # Apply slight blur to reduce noise
            image = image.filter(ImageFilter.MedianFilter(3))
            
            return image
        except Exception:
            return image
    
    def extract_from_pdf(self, file_path: str, use_ocr: bool = True) -> Tuple[str, List[str], List[Dict]]:
        """Enhanced PDF extraction with better structure detection"""
        text_content = ""
        image_descriptions = []
        tables = []
        
        try:
            doc = fitz.open(file_path)
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract structured text with blocks
                blocks = page.get_text("dict")["blocks"]
                page_text = ""
                
                for block in blocks:
                    if "lines" in block:  # Text block
                        for line in block["lines"]:
                            for span in line["spans"]:
                                text = span["text"].strip()
                                if text:
                                    # Detect headings based on font size
                                    font_size = span["size"]
                                    if font_size > 12:  # Likely heading
                                        page_text += f"\n## {text}\n"
                                    else:
                                        page_text += text + " "
                        page_text += "\n"
                
                if page_text.strip():
                    text_content += f"\n--- Page {page_num + 1} ---\n{page_text}\n"
                
                # Extract text from images
                if use_ocr:
                    image_text = self._extract_text_from_pdf_images(page, page_num)
                    if image_text.strip():
                        text_content += f"\n### Image Content on Page {page_num + 1}\n{image_text}\n"
                
                # Extract tables
                page_tables = self._extract_tables_from_page(page, page_num)
                tables.extend(page_tables)
                
                # Extract images
                image_list = page.get_images()
                for img_index, img in enumerate(image_list):
                    img_description = self._process_pdf_image(doc, img, page_num, img_index)
                    image_descriptions.append(img_description)
            
            doc.close()
            
            # Add tables to text content
            if tables:
                text_content += "\n## Extracted Tables\n"
                for i, table in enumerate(tables):
                    text_content += f"\n### Table {i+1} (Page {table['page']})\n"
                    text_content += table['content'] + "\n"
            
        except Exception as e:
            raise Exception(f"Error processing PDF: {str(e)}")
        
        return text_content.strip(), image_descriptions, tables
    
    def _extract_tables_from_page(self, page, page_num: int) -> List[Dict]:
        """Extract tables from PDF page"""
        tables = []
        try:
            # Try PyMuPDF's table detection
            tabs = page.find_tables()
            if tabs.tables:
                for table_idx, table in enumerate(tabs.tables):
                    try:
                        df = table.to_pandas()
                        if not df.empty:
                            # Convert to markdown table
                            table_content = self._dataframe_to_markdown(df)
                            tables.append({
                                'page': page_num + 1,
                                'content': table_content,
                                'dataframe': df
                            })
                    except Exception as e:
                        continue
        except:
            pass
        
        return tables
    
    def _dataframe_to_markdown(self, df: pd.DataFrame) -> str:
        """Convert DataFrame to markdown table"""
        try:
            # Create markdown table
            headers = "| " + " | ".join(str(col) for col in df.columns) + " |"
            separator = "|" + "|".join(["---"] * len(df.columns)) + "|"
            rows = []
            
            for _, row in df.iterrows():
                row_str = "| " + " | ".join(str(cell) for cell in row) + " |"
                rows.append(row_str)
            
            return "\n".join([headers, separator] + rows)
        except:
            return df.to_string()
    
    def _extract_text_from_pdf_images(self, page, page_num: int) -> str:
        """Enhanced image text extraction"""
        try:
            image_text = ""
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    pix = fitz.Pixmap(page.parent, xref)
                    
                    if pix.n - pix.alpha < 4:
                        img_data = pix.tobytes("png")
                        pil_image = Image.open(io.BytesIO(img_data))
                        
                        # Try multiple OCR configurations
                        enhanced_image = self.preprocess_image(pil_image)
                        
                        # Try different PSM modes
                        ocr_results = []
                        for psm in [6, 8, 11, 13]:
                            try:
                                config = f'--oem 3 --psm {psm}'
                                text = pytesseract.image_to_string(enhanced_image, config=config)
                                if text.strip():
                                    ocr_results.append(text.strip())
                            except:
                                continue
                        
                        # Use the best result
                        best_text = max(ocr_results, key=len) if ocr_results else ""
                        cleaned_text = best_text.replace("\x0c", "").strip()
                        
                        if cleaned_text:
                            image_text += f"**Image {img_index + 1}:** {cleaned_text}\n\n"
                    
                    pix = None
                    
                except Exception as e:
                    continue
            
            return image_text
            
        except Exception as e:
            return f"[Image extraction error: {str(e)}]"
    
    def _process_pdf_image(self, doc, img, page_num: int, img_index: int) -> str:
        """Process PDF images"""
        try:
            return f"Image {img_index + 1} on page {page_num + 1}"
        except:
            return f"Image {img_index + 1} on page {page_num + 1}"
    
    def extract_from_docx(self, file_path: str) -> Tuple[str, List[str], List[Dict]]:
        """Enhanced DOCX extraction"""
        text_content = ""
        image_descriptions = []
        tables = []
        
        try:
            doc = Document(file_path)
            
            # Extract paragraphs with structure
            for para in doc.paragraphs:
                if para.text.strip():
                    # Detect headings
                    if para.style.name.startswith('Heading'):
                        level = para.style.name.replace('Heading', '').strip()
                        level_num = int(level) if level.isdigit() else 1
                        text_content += f"\n{'#' * level_num} {para.text}\n"
                    else:
                        text_content += para.text + "\n"
            
            # Extract tables
            for table_idx, table in enumerate(doc.tables):
                table_data = []
                for row in table.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    table_data.append(row_data)
                
                if table_data and any(any(cell for cell in row) for row in table_data):
                    # Convert to markdown
                    table_content = self._list_to_markdown_table(table_data)
                    tables.append({
                        'page': 1,
                        'content': table_content,
                        'dataframe': pd.DataFrame(table_data[1:], columns=table_data[0])
                    })
                    text_content += f"\n### Table {table_idx + 1}\n{table_content}\n"
            
            image_descriptions.append("DOCX document processed")
            
        except Exception as e:
            raise Exception(f"Error processing DOCX: {str(e)}")
        
        return text_content.strip(), image_descriptions, tables
    
    def _list_to_markdown_table(self, data: List[List[str]]) -> str:
        """Convert 2D list to markdown table"""
        if not data:
            return ""
        
        headers = "| " + " | ".join(str(cell) for cell in data[0]) + " |"
        separator = "|" + "|".join(["---"] * len(data[0])) + "|"
        rows = []
        
        for row in data[1:]:
            if row:
                row_str = "| " + " | ".join(str(cell) for cell in row) + " |"
                rows.append(row_str)
        
        return "\n".join([headers, separator] + rows)
    
    def extract_from_txt(self, file_path: str) -> Tuple[str, List[str], List[Dict]]:
        """Enhanced TXT extraction"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Add basic structure
            lines = content.split('\n')
            structured_content = ""
            for line in lines:
                if line.strip():
                    if len(line.strip()) < 50 and not line.endswith('.') and not line.endswith(','):
                        structured_content += f"\n## {line.strip()}\n"
                    else:
                        structured_content += line.strip() + "\n"
            
            return structured_content.strip(), [], []
        except Exception as e:
            raise Exception(f"Error processing TXT file: {str(e)}")
    
    def extract_from_image(self, file_path: str) -> Dict:
        """Enhanced image extraction"""
        try:
            image = Image.open(file_path)
            enhanced_image = self.preprocess_image(image)
            
            # Try multiple OCR configurations
            ocr_results = []
            for psm in [6, 8, 11, 13]:
                try:
                    config = f'--oem 3 --psm {psm}'
                    text = pytesseract.image_to_string(enhanced_image, config=config)
                    if text.strip():
                        ocr_results.append(text.strip())
                except:
                    continue
            
            best_text = max(ocr_results, key=len) if ocr_results else ""
            cleaned_text = best_text.replace("\x0c", "").strip()
            
            return {
                'success': True,
                'text_content': cleaned_text,
                'image_descriptions': ["Image processed with enhanced OCR"],
                'file_type': 'image',
                'char_count': len(cleaned_text),
                'word_count': len(cleaned_text.split()),
                'tables': []
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text_content': '',
                'image_descriptions': [],
                'file_type': 'image',
                'tables': []
            }
    
    def extract_text(self, file_path: str, use_ocr: bool = True) -> Dict:
        """Main extraction method"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        try:
            if file_ext == '.pdf':
                text_content, image_descriptions, tables = self.extract_from_pdf(file_path, use_ocr)
            elif file_ext in ['.docx', '.doc']:
                text_content, image_descriptions, tables = self.extract_from_docx(file_path)
            elif file_ext in ['.txt', '.text', '.md']:
                text_content, image_descriptions, tables = self.extract_from_txt(file_path)
            elif file_ext in ['.png', '.jpg', '.jpeg']:
                result = self.extract_from_image(file_path)
                return result
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")
            
            return {
                'success': True,
                'text_content': text_content,
                'image_descriptions': image_descriptions,
                'file_type': file_ext,
                'char_count': len(text_content),
                'word_count': len(text_content.split()),
                'tables': tables
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text_content': '',
                'image_descriptions': [],
                'file_type': file_ext,
                'tables': []
            }
    
    def save_as_markdown(self, extraction_result: Dict, output_path: str) -> bool:
        """Save extraction result as formatted markdown"""
        try:
            if not extraction_result['success']:
                return False
            
            content = extraction_result['text_content']
            file_type = extraction_result['file_type']
            
            md_content = f"""# Extracted Content from {file_type.upper()} File

**Extraction Summary:**
- **File Type:** {file_type}
- **Characters:** {extraction_result['char_count']:,}
- **Words:** {extraction_result['word_count']:,}
- **Images Found:** {len(extraction_result['image_descriptions'])}

## Content

{content}

"""
            
            # Add image descriptions
            if extraction_result['image_descriptions']:
                md_content += "\n## Image Descriptions\n"
                for i, desc in enumerate(extraction_result['image_descriptions']):
                    md_content += f"{i+1}. {desc}\n"
            
            # Add tables
            if 'tables' in extraction_result and extraction_result['tables']:
                md_content += "\n## Extracted Tables\n"
                for i, table in enumerate(extraction_result['tables']):
                    md_content += f"\n### Table {i+1}\n{table['content']}\n"
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_content)
            
            return True
            
        except Exception as e:
            print(f"Error saving markdown: {e}")
            return False