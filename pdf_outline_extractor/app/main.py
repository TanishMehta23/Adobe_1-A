echo 'import os
import json
import fitz

def extract_title(page):
    text_dict = page.get_text("dict")
    if len(text_dict["blocks"]) > 0:
        for block in text_dict["blocks"]:
            if block["type"] == 0 and len(block["lines"]) > 0:
                for line in block["lines"]:
                    if len(line["spans"]) > 0:
                        title = line["spans"][0]["text"].strip()
                        if title:
                            return title
    return None

def extract_headings_from_page(page):
    blocks = page.get_text("dict")["blocks"]
    headings = []
    for b in blocks:
        if b["type"] == 0:
            for l in b["lines"]:
                for span in l["spans"]:
                    if (span["size"] >= 14 and span["flags"] & 2) or span["text"].isupper():
                        heading_text = span["text"].strip()
                        if len(heading_text) > 2 and heading_text.replace(" ", "").isalnum():
                            headings.append((heading_text, span["size"]))
    return headings

def assign_levels(sorted_headings):
    if not sorted_headings:
        return []
    return [{"title": text, "page": page} for text, _, page in sorted_headings]

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
        print(f"Error: Input directory \'{input_dir}\' does not exist")
        return
    
    pdf_files = [f for f in os.listdir(input_dir) if f.endswith(".pdf")]
    if not pdf_files:
        print(f"No PDF files found in \'{input_dir}\'")
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
    main()' > app/main.py