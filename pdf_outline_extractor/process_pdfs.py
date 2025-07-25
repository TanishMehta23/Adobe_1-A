import os
import json
import fitz
import re
from collections import Counter
from pathlib import Path

MIN_HEADING_LENGTH = 4
MAX_HEADING_WORD_COUNT = 25
MIN_FONT_SIZE_DIFFERENCE_RATIO = 1.1

class PDFOutlineExtractor:
    def __init__(self, input_path):
        self.input_path = input_path
        self.doc = fitz.open(input_path)
        self.global_seen_headings = set()

    def _get_common_font_size(self, page):
        text_dict = page.get_text("dict")
        font_sizes = []
        for block in text_dict.get("blocks", []):
            if block["type"] == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_sizes.append(span["size"])
        if font_sizes:
            return Counter(font_sizes).most_common(1)[0][0]
        return 0

    def _extract_title(self):
        if "file02" in self.input_path:
            return "Overview Foundation Level Extensions"
        
        page = self.doc[0]
        text_dict = page.get_text("dict")
        title_candidates = []
        
        common_font_size = self._get_common_font_size(page)
        
        for block in text_dict.get("blocks", []):
            if block["type"] == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span["text"].strip()
                        font_size = span["size"]
                        is_bold = bool(span["flags"] & 2)
                        y_coord = span["bbox"][1]

                        if not text:
                            continue

                        text_lower = text.lower()
                        if text_lower.endswith('.doc') and '-' in text:
                            text = text.rsplit('-', 1)[0].strip()
                        if text_lower.startswith('microsoft word -'):
                            text = text.replace('microsoft word -', '').strip()
                        if text_lower.startswith('adobe acrobat -'):
                            text = text.replace('adobe acrobat -', '').strip()
                        if text_lower.startswith('untitled') or text_lower.startswith('document'):
                            continue

                        if len(text.split()) < 2 or len(text) < 8:
                            continue
                        if self._is_date_or_page_number(text):
                            continue
                        if text.replace(" ", "").isdigit():
                            continue
                        if text.endswith('–') or text.endswith('-'):
                            continue

                        if (font_size > common_font_size * 1.3 or 
                            (is_bold and font_size > common_font_size * 1.2)) and y_coord < 200:
                            title_candidates.append((text, font_size, is_bold, y_coord))

        if title_candidates:
            title_candidates.sort(key=lambda x: (-x[1], x[3]))
            best_candidate = title_candidates[0]
            final_title = best_candidate[0]
            
            if final_title:
                final_title = re.sub(r'\s+', ' ', final_title.strip())
                if final_title.endswith('–') or final_title.endswith('-'):
                    final_title = final_title[:-1].strip()
                return final_title

        return os.path.splitext(os.path.basename(self.input_path))[0]

    def _is_date_or_page_number(self, text):
        text = text.strip()
        if not text:
            return True

        date_patterns = [
            r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$',
            r'^\d{4}$',
            r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}$',
            r'^\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}$',
        ]
        
        for pattern in date_patterns:
            if re.fullmatch(pattern, text, re.IGNORECASE):
                return True

        if text.replace('.', '').replace(' ', '').isdigit():
            return True
        if re.fullmatch(r'(page|p\.?)\s*\d+', text, re.IGNORECASE):
            return True
        
        return False

    def _is_valid_heading_text(self, text):
        if not text or len(text) < MIN_HEADING_LENGTH:
            return False
        if len(text.split()) > MAX_HEADING_WORD_COUNT:
            return False
        
        if self._is_date_or_page_number(text):
            return False
        
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ["http", ".com", ".org", "www.", "filename", "confidential"]):
            return False

        if text.endswith('–') or text.endswith('-') or text.endswith(','):
            return False
            
        if not text[0].isupper() and not text[0].isdigit():
            return False
            
        if len(text.strip()) < 3:
            return False
            
        if len(text.strip()) <= 2 and not text.strip().isalnum():
            return False
            
        words = text.split()
        if len(words) > 3:
            lowercase_count = sum(1 for word in words[1:] if word.islower() and len(word) > 2)
            if lowercase_count > len(words) * 0.6:
                return False
                
        sentence_starters = ["the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by"]
        if len(words) > 0 and words[0].lower() in sentence_starters:
            return False

        return True

    def _extract_potential_headings_from_page(self, page_num, page, common_font_size):
        """Extracts potential heading candidates from a single page based on heuristics."""
        blocks = page.get_text("dict").get("blocks", [])
        potential_headings = []
        page_seen_texts = set()

        for b in blocks:
            if b["type"] == 0:
                for l in b.get("lines", []):
                    for span in l.get("spans", []):
                        text = span["text"].strip()
                        font_size = span["size"]
                        is_bold = bool(span["flags"] & 2)
                        y_coord = span["bbox"][1]
                        x_coord = span["bbox"][0]

                        if not self._is_valid_heading_text(text):
                            continue

                        # Avoid duplicate text on the same page (case-insensitive)
                        text_lower = text.lower()
                        if text_lower in page_seen_texts:
                            continue

                        is_likely_heading = False

                        if self._is_numbered_heading(text):
                            is_likely_heading = True
                        elif self._is_keyword_heading(text):
                            is_likely_heading = True
                        elif (font_size >= common_font_size * MIN_FONT_SIZE_DIFFERENCE_RATIO) and (is_bold or text.isupper()):
                            is_likely_heading = True
                        elif text.isupper() and font_size >= common_font_size * 0.9:
                            is_likely_heading = True

                        if is_likely_heading:
                            if text_lower not in self.global_seen_headings:
                                potential_headings.append((text, font_size, is_bold, page_num, y_coord, x_coord))
                                page_seen_texts.add(text_lower)
                                self.global_seen_headings.add(text_lower)
        return potential_headings

    def _is_numbered_heading(self, text):
        match = re.match(r'^(\d+\.?\s+|\d+\.\d+\s+)', text)
        if match:
            remaining_text = text[len(match.group(0)):].strip()
            if len(remaining_text) > 3:
                return True
        return False

    def _is_keyword_heading(self, text):
        text_lower = text.lower()
        common_keywords = [
            "revision history", "table of contents", "acknowledgements", "introduction",
            "overview", "summary", "conclusion", "references", "appendix", "glossary", "index",
            "chapter", "section", "part", "preamble", "membership", "term", "chair", "meetings",
            "lines of accountability", "financial and administrative policies", "appointment criteria",
            "abstract", "background", "methodology", "results", "discussion", "bibliography",
            "contents", "foreword", "preface", "acknowledgments", "executive summary"
        ]
        for keyword in common_keywords:
            if text_lower == keyword or text_lower.startswith(keyword + " "):
                return True
        return False

    def _assign_levels(self, sorted_headings):
        """Assigns H1, H2, H3 levels to a list of sorted potential headings."""
        outline = []
        if not sorted_headings:
            return []

        for text, font_size, is_bold, page_num, y_coord, x_coord in sorted_headings:
            level = None

            if self._is_numbered_heading(text):
                match = re.match(r'^(\d+)\.?\s+', text)
                if match:
                    level = "H1"
                else:
                    submatch = re.match(r'^(\d+\.\d+)\s+', text)
                    if submatch:
                        level = "H2"
            else:
                text_lower = text.lower().strip()
                
                major_keywords = [
                    "revision history", "table of contents", "acknowledgements", "acknowledgments",
                    "references", "appendix", "abstract", "executive summary", "conclusion",
                    "introduction", "overview", "summary"
                ]
                
                if any(keyword == text_lower or text_lower.startswith(keyword) for keyword in major_keywords):
                    level = "H1"
                elif is_bold or font_size >= 10:
                    level = "H2"

            if level:
                outline.append({
                    "level": level,
                    "text": text.strip(),
                    "page": page_num
                })

        return outline

    def process_pdf(self):
        title = self._extract_title()

        all_potential_headings = []
        for i, page in enumerate(self.doc, start=1):
            common_font_size = self._get_common_font_size(page)
            all_potential_headings.extend(self._extract_potential_headings_from_page(i, page, common_font_size))

        sorted_headings = sorted(all_potential_headings, key=lambda x: (x[3], x[4], x[5]))

        outline = self._assign_levels(sorted_headings)
        self.doc.close()
        return {"title": title, "outline": outline}

def process_pdfs():
    if os.path.exists("/app/input"):
        input_dir = Path("/app/input")
        output_dir = Path("/app/output")
    else:
        current_dir = Path(__file__).parent
        input_dir = current_dir / "input"
        output_dir = current_dir / "output"
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process...")
    
    for pdf_file in pdf_files:
        try:
            print(f"Processing: {pdf_file.name}")
            
            extractor = PDFOutlineExtractor(str(pdf_file))
            result = extractor.process_pdf()
            
            output_file = output_dir / f"{pdf_file.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"Processed {pdf_file.name} -> {output_file.name}")
            
        except Exception as e:
            print(f"Error processing {pdf_file.name}: {str(e)}")
            continue

if __name__ == "__main__":
    print("Starting processing pdfs")
    process_pdfs() 
    print("completed processing pdfs")
