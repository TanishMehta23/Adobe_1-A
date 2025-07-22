import os
import json
import fitz

def extract_title(page):
    text_dict = page.get_text("dict")
    title_candidates = []
    
    for block in text_dict["blocks"]:
        if block["type"] == 0:  # text block
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if text and len(text) > 5:
                        # Clean up the text
                        if text.lower().endswith('.doc'):
                            text = text.rsplit('-', 1)[0].strip()
                        if text.lower().startswith('microsoft word'):
                            text = text.replace('Microsoft Word - ', '').strip()
                        
                        # Add to candidates with priority based on size
                        title_candidates.append((text, span["size"]))
    
    if title_candidates:
        # Sort by size (descending)
        title_candidates.sort(key=lambda x: -x[1])
        return title_candidates[0][0]
    
    return None

def is_topic_heading(text):
    # Check if text starts with a number followed by dot and space (e.g., "1. ", "2.1 ")
    if text and text[0].isdigit() and '. ' in text:
        return True
    
    # List of known topic names
    topic_keywords = [
        "introduction",
        "overview",
        "references",
        "acknowledgements",
        "table of contents",
        "revision history",
        "business outcomes",
        "content",
        "trademarks",
        "documents"
    ]
    
    # Check if text contains any topic keywords
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in topic_keywords)

def extract_headings_from_page(page):
    blocks = page.get_text("dict")["blocks"]
    headings = []
    for b in blocks:
        if b["type"] == 0:
            for l in b["lines"]:
                for span in l["spans"]:
                    text = span["text"].strip()
                    # Only include proper topic headings
                    is_heading = (
                        len(text) > 3 and  # Reasonable length
                        not text.replace('.', '').isdigit() and  # Not just a number
                        (
                            (text[0].isdigit() and '.' in text) or  # Numbered sections
                            is_topic_heading(text)  # Known topic names
                        )
                    )
                    
                    if is_heading:
                        headings.append((text, span["size"]))
    return headings

def assign_levels(sorted_headings):
    levels = []
    if not sorted_headings:
        return []
    
    for text, size, page_num in sorted_headings:
        # Skip unwanted entries
        if text.strip().isdigit() or len(text.strip()) < 3:
            continue
        
        # Determine level based on text format
        if text[0].isdigit():
            parts = text.split(' ', 1)
            if len(parts) > 1:
                section_num = parts[0].rstrip('.')
                # If it has a subsection (like 2.1)
                if '.' in section_num:
                    level = "H2"
                else:
                    level = "H1"
            else:
                continue  # Skip if it's just a number
        else:
            # For non-numbered headings, check content
            if text.lower() in ["table of contents", "acknowledgements", "references"]:
                level = "H1"
            else:
                level = "H2"
        
        levels.append({
            "level": level,
            "text": text,
            "page": page_num
        })
    
    return levels

def process_pdf(input_path):
    doc = fitz.open(input_path)
    title = extract_title(doc[0]) or os.path.splitext(os.path.basename(input_path))[0]
    
    headings = []
    for i, page in enumerate(doc, start=1):
        page_headings = extract_headings_from_page(page)
        headings += [(text, size, i) for (text, size) in page_headings]
    
    seen = set()
    filtered = []
    for t, s, p in headings:
        key = (t.lower(), p)
        if key not in seen:
            filtered.append((t, s, p))
            seen.add(key)
    
    outline = assign_levels(filtered)
    doc.close()
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
            result = process_pdf(in_path)
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
