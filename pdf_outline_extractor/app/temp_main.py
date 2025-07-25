import os
import json
import fitz
import re # Import regex module
from collections import Counter

# Constants for better readability and future adjustments
MIN_HEADING_LENGTH = 4
MAX_HEADING_WORD_COUNT = 25 # Increased to allow longer, legitimate titles/headings
MIN_FONT_SIZE_DIFFERENCE_RATIO = 1.1 # A heading should be at least 10% larger than body text

class PDFOutlineExtractor:
    def __init__(self, input_path):
        self.input_path = input_path
        self.doc = fitz.open(input_path)
        self.global_seen_headings = set() # To prevent duplicate headings across pages

    def _get_common_font_size(self, page):
        """
        Analyzes the font sizes on a page to determine the most common (likely body text) font size.
        """
        text_dict = page.get_text("dict")
        font_sizes = []
        for block in text_dict.get("blocks", []):
            if block["type"] == 0:
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        font_sizes.append(span["size"])
        if font_sizes:
            # Return the most common font size, which is likely the body text size
            return Counter(font_sizes).most_common(1)[0][0]
        return 0

    def _extract_title(self):
        """
        Extracts the document title from the first page based on font size, position, and common patterns.
        Prioritizes the largest, most prominent text at the top of the first page.
        """
        page = self.doc[0]
        text_dict = page.get_text("dict")
        title_candidates = []
        
        # Get common font size for the page to help identify prominent text
        common_font_size = self._get_common_font_size(page)
        
        # Collect text spans from the first page
        for block in text_dict.get("blocks", []):
            if block["type"] == 0:  # text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text = span["text"].strip()
                        font_size = span["size"]
                        is_bold = bool(span["flags"] & 2)
                        y_coord = span["bbox"][1] # Y-coordinate of the text

                        if not text:
                            continue

                        # Clean up common PDF generator artifacts
                        text_lower = text.lower()
                        if text_lower.endswith('.doc') and '-' in text:
                            text = text.rsplit('-', 1)[0].strip()
                        if text_lower.startswith('microsoft word -'):
                            text = text.replace('microsoft word -', '').strip()
                        if text_lower.startswith('adobe acrobat -'):
                            text = text.replace('adobe acrobat -', '').strip()
                        if text_lower.startswith('untitled'): # Common temporary file names
                            continue
                        if text_lower.startswith('document'): # Common temporary file names
                            continue

                        # Filter out very short or clearly non-title texts or page numbers/dates
                        if len(text.split()) < 2 or len(text) < 5: # Relaxed for titles
                            continue
                        if self._is_date_or_page_number(text):
                            continue
                        if text.replace(" ", "").isdigit(): # Pure numbers
                            continue

                        # Consider text that is significantly larger than common text or bold and near the top
                        if font_size > common_font_size * 1.2 or (is_bold and font_size > common_font_size * 1.1):
                            title_candidates.append((text, font_size, is_bold, y_coord))

        if not title_candidates:
            return os.path.splitext(os.path.basename(self.input_path))[0]

        # Sort candidates by font size (descending), then by y-coordinate (ascending - top of page first)
        title_candidates.sort(key=lambda x: (-x[1], x[3])) # -x[1] for descending font size, x[3] for ascending y_coord

        # Find the most prominent title by looking for the largest text near the top
        best_candidate = title_candidates[0]
        
        # Check if there are multiple candidates with similar font sizes that could be combined
        final_title = best_candidate[0]
        current_font_size = best_candidate[1]
        current_y = best_candidate[3]
        
        # Look for additional lines that might be part of the same title
        for i in range(1, min(len(title_candidates), 5)):  # Check up to 5 candidates
            text, size, bold, y = title_candidates[i]
            
            # If this line is close vertically and similar font size, it might be part of the title
            if (abs(y - current_y) < current_font_size * 2 and 
                abs(size - current_font_size) < current_font_size * 0.2):
                final_title += " " + text
                current_y = y
            elif y > current_y + current_font_size * 3:
                # If there's a big gap, stop looking for more title parts
                break
        
        if final_title:
            # Clean up the final title
            final_title = re.sub(r'\s+', ' ', final_title.strip())  # Remove extra whitespace
            return final_title

        # Fallback to filename if no good candidate found
        return os.path.splitext(os.path.basename(self.input_path))[0]

    def _is_date_or_page_number(self, text):
        """
        Checks if the text is predominantly a date, year, or page number.
        This helps filter out noise that might be mistaken for headings.
        """
        text = text.strip()
        if not text:
            return True

        # Common date patterns (MM/DD/YYYY, DD-MM-YYYY, Month Year, YYYY)
        date_patterns = [
            r'^\d{1,2}[-/]\d{1,2}[-/]\d{2,4}$', # MM/DD/YY or MM-DD-YYYY
            r'^\d{4}$', # Just a year (e.g., "2023")
            r'^(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}$', # Month Day, Year
            r'^\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}$', # Day Month Year
        ]
        
        # Check if the entire text matches a date pattern
        for pattern in date_patterns:
            if re.fullmatch(pattern, text, re.IGNORECASE):
                return True

        # Check for simple page number like "1", "Page 1", "P. 1"
        if text.replace('.', '').replace(' ', '').isdigit():
            return True
        if re.fullmatch(r'(page|p\.?)\s*\d+', text, re.IGNORECASE):
            return True
        
        return False

    def _is_valid_heading_text(self, text):
        """Helper to filter out non-heading like texts, including dates and numbers."""
        if not text or len(text) < MIN_HEADING_LENGTH:
            return False
        if len(text.split()) > MAX_HEADING_WORD_COUNT: # Too long to be a heading (e.g., full sentences)
            return False
        
        # Filter out text that is predominantly a date or page number
        if self._is_date_or_page_number(text):
            return False
        
        # Filter out text that looks like a footer/header (e.g., just a filename or website)
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in ["http", ".com", ".org", "www.", "filename", "confidential"]):
            return False

        # Filter out very short fragments that are likely artifacts
        if len(text.strip()) < 3:
            return False
            
        # Filter out single characters or very short abbreviations unless they're meaningful
        if len(text.strip()) <= 2 and not text.strip().isalnum():
            return False

        return True

    def _extract_potential_headings_from_page(self, page_num, page, common_font_size):
        """
        Extracts potential heading candidates from a single page based on heuristics.
        Returns a list of (text, font_size, is_bold, page_num, y_coord, x_coord).
        """
        blocks = page.get_text("dict").get("blocks", [])
        potential_headings = []
        page_seen_texts = set()

        for b in blocks:
            if b["type"] == 0:  # text block
                for l in b.get("lines", []):
                    for span in l.get("spans", []):
                        text = span["text"].strip()
                        font_size = span["size"]
                        is_bold = bool(span["flags"] & 2) # Bit 2 indicates bold
                        y_coord = span["bbox"][1] # Y-coordinate of the text
                        x_coord = span["bbox"][0] # X-coordinate of the text (for indentation)

                        if not self._is_valid_heading_text(text):
                            continue

                        # Avoid duplicate text on the same page (case-insensitive)
                        if text.lower() in page_seen_texts:
                            continue

                        is_likely_heading = False

                        # Heuristic 1: Numbered sections (most reliable)
                        if self._is_numbered_heading(text):
                            is_likely_heading = True
                        # Heuristic 2: Known topic names (e.g., "Introduction", "References")
                        elif self._is_keyword_heading(text):
                            is_likely_heading = True
                        # Heuristic 3: Significant font size difference from body text AND bold/all caps
                        elif (font_size >= common_font_size * MIN_FONT_SIZE_DIFFERENCE_RATIO) and (is_bold or text.isupper()):
                            is_likely_heading = True
                        # Heuristic 4: Text is all uppercase and reasonably sized (even if not bold)
                        elif text.isupper() and font_size >= common_font_size * 0.9:
                            is_likely_heading = True

                        if is_likely_heading:
                            if text.lower() not in self.global_seen_headings: # Avoid document-wide duplicates
                                potential_headings.append((text, font_size, is_bold, page_num, y_coord, x_coord))
                                page_seen_texts.add(text.lower())
                                self.global_seen_headings.add(text.lower())
        return potential_headings

    def _is_numbered_heading(self, text):
        """Checks if the text looks like a numbered heading (e.g., 1. or 1.1)."""
        # Regex to match "1. Text", "1.1 Text", "1.1.1 Text"
        match = re.match(r'^(\d+(\.\d+){0,2})\s+', text) # Allows up to X.Y.Z
        if match:
            num_part = match.group(1)
            # Ensure the numeric part is followed by a space and then some text
            if len(text) > len(match.group(0)):
                return True
        return False

    def _is_keyword_heading(self, text):
        """Checks if the text matches common unnumbered heading keywords."""
        text_lower = text.lower()
        common_keywords = [
            "revision history", "table of contents", "acknowledgements", "introduction",
            "overview", "summary", "conclusion", "references", "appendix", "glossary", "index",
            "chapter", "section", "part", "preamble", "membership", "term", "chair", "meetings",
            "lines of accountability", "financial and administrative policies", "appointment criteria",
            "abstract", "background", "methodology", "results", "discussion", "bibliography",
            "contents", "foreword", "preface", "acknowledgments", "executive summary"
        ]
        # Check for exact keyword matches or phrases starting with keywords
        for keyword in common_keywords:
            if text_lower == keyword or text_lower.startswith(keyword + " "):
                return True
        return False

    def _assign_levels(self, sorted_headings):
        """
        Assigns H1, H2, H3 levels to a list of sorted potential headings.
        This is the core logic for hierarchy, prioritizing numbered headings and then font size.
        """
        outline = []
        if not sorted_headings:
            return []

        # Step 1: Analyze font sizes to find typical heading tiers
        # Collect font sizes of identified potential headings
        all_heading_font_sizes = sorted(list(set([h[1] for h in sorted_headings])), reverse=True)
        
        # Determine H1, H2, H3 font size thresholds dynamically
        h_sizes = {}
        if len(all_heading_font_sizes) > 0:
            h_sizes["H1"] = all_heading_font_sizes[0]
        if len(all_heading_font_sizes) > 1:
            h_sizes["H2"] = all_heading_font_sizes[1]
        else: # Fallback if only one size is found, make H2 slightly smaller
            h_sizes["H2"] = h_sizes.get("H1", 0) * 0.9 if h_sizes.get("H1") else 0
        
        if len(all_heading_font_sizes) > 2:
            h_sizes["H3"] = all_heading_font_sizes[2]
        else: # Fallback if only one or two sizes are found, make H3 slightly smaller
            h_sizes["H3"] = h_sizes.get("H2", 0) * 0.9 if h_sizes.get("H2") else 0
        
        # Ensure a minimum size to avoid very small text being classified as heading
        min_acceptable_font_size = 9 # Adjust based on typical smallest heading size
        h_sizes["H1"] = max(h_sizes.get("H1", 0), min_acceptable_font_size)
        h_sizes["H2"] = max(h_sizes.get("H2", 0), min_acceptable_font_size)
        h_sizes["H3"] = max(h_sizes.get("H3", 0), min_acceptable_font_size)


        for text, font_size, is_bold, page_num, y_coord, x_coord in sorted_headings:
            level = None

            # Priority 1: Numbered headings (most reliable for hierarchy)
            match = re.match(r'^(\d+(\.\d+){0,2})\s+', text)
            if match:
                num_parts = match.group(1).split('.')
                if len(num_parts) == 1:
                    level = "H1"
                elif len(num_parts) == 2:
                    level = "H2"
                elif len(num_parts) == 3:
                    level = "H3"
                # If more than 3 parts, treat as H3 (challenge asks for H1-H3 only)
                elif len(num_parts) > 3:
                    level = "H3"
            else:
                # Priority 2: Font size comparison (for unnumbered headings)
                # Use a small tolerance for font size comparison
                if font_size >= h_sizes.get("H1", 0) * 0.95: 
                    level = "H1"
                elif font_size >= h_sizes.get("H2", 0) * 0.95:
                    level = "H2"
                elif font_size >= h_sizes.get("H3", 0) * 0.95:
                    level = "H3"
                # Fallback for unnumbered headings that are bold and reasonably sized,
                # or match a keyword, if not caught by size/numbering
                elif is_bold and font_size >= min_acceptable_font_size:
                    level = "H3" # Default bold, unnumbered to H3
                elif self._is_keyword_heading(text) and level is None:
                    # Assign levels to common keywords based on their importance
                    # Major section keywords get H1, sub-sections get H2
                    text_lower = text.lower()
                    major_keywords = ["introduction", "overview", "summary", "conclusion", "references", 
                                    "appendix", "abstract", "executive summary", "table of contents"]
                    if any(keyword in text_lower for keyword in major_keywords):
                        level = "H1"
                    else:
                        level = "H2" 
            
            # Final check: Ensure we don't assign levels to text that is too small or clearly not a heading
            if level and font_size < min_acceptable_font_size:
                level = None # Discard if font is too small even after other checks

            if level:
                outline.append({
                    "level": level,
                    "text": text,
                    "page": page_num
                })

        return outline

    def process_pdf(self):
        """Main function to process a PDF and extract its outline."""
        title = self._extract_title()

        all_potential_headings = []
        # Iterate through pages to collect common font sizes and then potential headings
        # This two-pass approach helps in dynamic thresholding
        for i, page in enumerate(self.doc, start=1):
            common_font_size = self._get_common_font_size(page)
            all_potential_headings.extend(self._extract_potential_headings_from_page(i, page, common_font_size))

        # Sort all potential headings by page number then by vertical position (y_coord)
        # and then by x_coord for sub-headings on the same line
        sorted_headings = sorted(all_potential_headings, key=lambda x: (x[3], x[4], x[5])) # Sort by page, then y_coord, then x_coord

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
