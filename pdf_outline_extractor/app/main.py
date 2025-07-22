import os
import json
import fitz  # PyMuPDF

def extract_headings_from_page(page):
    blocks = page.get_text("dict")["blocks"]
    headings = []
    for b in blocks:
        if b['type'] == 0:  # text
            for l in b['lines']:
                for span in l['spans']:
                    # Simple heading logic: large bold, or all-caps, or unique font
                    if (span['size'] >= 14 and span['flags'] & 2) or span['text'].isupper():
                        heading_text = span['text'].strip()
                        if len(heading_text) > 2 and heading_text.replace(' ', '').isalnum():
                            headings.append((heading_text, span['size']))
    return headings

def assign_levels(sorted_headings):
    levels = []
    # Heuristic: assign H1 to biggest, H2 to next, etc.
    if not sorted_headings:
        return []
    sizes = list(sorted(set(size for _, size in sorted_headings), reverse=True))
    for text, size, page_num in sorted_headings:
        if size == sizes[0]:
            level = "H1"
        elif len(sizes) > 1 and size == sizes[1]:
            level = "H2"
        else:
            level = "H3"
        levels.append({"level": level, "text": text, "page": page_num})
    return levels

def process_pdf(input_path):
    doc = fitz.open(input_path)
    headings = []
    for i, page in enumerate(doc, start=1):
        page_headings = extract_headings_from_page(page)
        headings += [(text, size, i) for (text, size) in page_headings]
    # Remove duplicates, sort by page/occurrence/order
    seen = set()
    filtered = []
    for t, s, p in headings:
        key = (t.lower(), p)
        if key not in seen:
            filtered.append((t, s, p))
            seen.add(key)
    outline = assign_levels(filtered)
    # Title = first H1 or first heading
    title = outline[0]["text"] if outline else os.path.basename(input_path)
    return {"title": title, "outline": outline}

def main():
    input_dir = "./input"
    output_dir = "./output"
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if input directory exists and has PDF files
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' does not exist")
        return
    
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith('.pdf')]
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
