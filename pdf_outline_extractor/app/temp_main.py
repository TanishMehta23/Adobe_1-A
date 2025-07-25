import os
import json
import fitz
import re
from collections import Counter

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
                        if text_lower.startswith('untitled'):
                            continue
                        if text_lower.startswith('document'):
                            continue

                        if len(text.split()) < 2 or len(text) < 5:
                            continue
                        if self._is_date_or_page_number(text):
                            continue
                        if text.replace(" ", "").isdigit():
                            continue

                        if font_size > common_font_size * 1.2 or (is_bold and font_size > common_font_size * 1.1):
                            title_candidates.append((text, font_size, is_bold, y_coord))

        if not title_candidates:
            return os.path.splitext(os.path.basename(self.input_path))[0]

        title_candidates.sort(key=lambda x: (-x[1], x[3]))

        best_candidate = title_candidates[0]
        
        final_title = best_candidate[0]
        current_font_size = best_candidate[1]
        current_y = best_candidate[3]
        
        for i in range(1, min(len(title_candidates), 5)):
            text, size, bold, y = title_candidates[i]
            
            if (abs(y - current_y) < current_font_size * 2 and 
                abs(size - current_font_size) < current_font_size * 0.2):
                final_title += " " + text
                current_y = y
            elif y > current_y + current_font_size * 3:
                break
        
        if final_title:
            final_title = re.sub(r'\s+', ' ', final_title.strip())
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

        if len(text.strip()) < 3:
            return False
            
        if len(text.strip()) <= 2 and not text.strip().isalnum():
            return False

        return True

    def _extract_potential_headings_from_page(self, page_num, page, common_font_size):
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

                        if text.lower() in page_seen_texts:
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
                            if text.lower() not in self.global_seen_headings:
                                potential_headings.append((text, font_size, is_bold, page_num, y_coord, x_coord))
                                page_seen_texts.add(text.lower())
                                self.global_seen_headings.add(text.lower())
        return potential_headings

    def _is_numbered_heading(self, text):
        match = re.match(r'^(\d+(\.\d+){0,2})\s+', text)
        if match:
            num_part = match.group(1)
            if len(text) > len(match.group(0)):
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
        outline = []
        if not sorted_headings:
            return []

        all_heading_font_sizes = sorted(list(set([h[1] for h in sorted_headings])), reverse=True)
        
        h_sizes = {}
        if len(all_heading_font_sizes) > 0:
            h_sizes["H1"] = all_heading_font_sizes[0]
        if len(all_heading_font_sizes) > 1:
            h_sizes["H2"] = all_heading_font_sizes[1]
        else:
            h_sizes["H2"] = h_sizes.get("H1", 0) * 0.9 if h_sizes.get("H1") else 0
        
        if len(all_heading_font_sizes) > 2:
            h_sizes["H3"] = all_heading_font_sizes[2]
        else:
            h_sizes["H3"] = h_sizes.get("H2", 0) * 0.9 if h_sizes.get("H2") else 0
        
        min_acceptable_font_size = 9
        h_sizes["H1"] = max(h_sizes.get("H1", 0), min_acceptable_font_size)
        h_sizes["H2"] = max(h_sizes.get("H2", 0), min_acceptable_font_size)
        h_sizes["H3"] = max(h_sizes.get("H3", 0), min_acceptable_font_size)

        for text, font_size, is_bold, page_num, y_coord, x_coord in sorted_headings:
            level = None

            match = re.match(r'^(\d+(\.\d+){0,2})\s+', text)
            if match:
                num_parts = match.group(1).split('.')
                if len(num_parts) == 1:
                    level = "H1"
                elif len(num_parts) == 2:
                    level = "H2"
                elif len(num_parts) == 3:
                    level = "H3"
                elif len(num_parts) > 3:
                    level = "H3"
            else:
                if font_size >= h_sizes.get("H1", 0) * 0.95: 
                    level = "H1"
                elif font_size >= h_sizes.get("H2", 0) * 0.95:
                    level = "H2"
                elif font_size >= h_sizes.get("H3", 0) * 0.95:
                    level = "H3"
                elif is_bold and font_size >= min_acceptable_font_size:
                    level = "H3"
                elif self._is_keyword_heading(text) and level is None:
                    text_lower = text.lower()
                    major_keywords = ["introduction", "overview", "summary", "conclusion", "references", 
                                    "appendix", "abstract", "executive summary", "table of contents"]
                    if any(keyword in text_lower for keyword in major_keywords):
                        level = "H1"
                    else:
                        level = "H2" 
            
            if level and font_size < min_acceptable_font_size:
                level = None

            if level:
                outline.append({
                    "level": level,
                    "text": text,
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

def main():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(current_dir, "input")
    output_dir = os.path.join(current_dir, "output")

    os.makedirs(output_dir, exist_ok=True)

    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist")
        return

    pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in '{input_dir}'")
        return

    print(f"Found {len(pdf_files)} PDF files to process...")

    for filename in pdf_files:
        try:
            print(f"Processing: {filename}")
            in_path = os.path.join(input_dir, filename)
            extractor = PDFOutlineExtractor(in_path)
            result = extractor.process_pdf()
            out_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))

            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Successfully created: {os.path.basename(out_path)}")

        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    print("Processing complete!")

if __name__ == "__main__":
    main()
