import csv
import re
import sys

# Reconfigure stdout for UTF-8 to prevent console print errors on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def is_basic_title(title):
    # Strip hashtags first
    title_clean = re.sub(r'#\w+', '', title).strip()
    
    # If the clean title is extremely short (less than 25 characters)
    if len(title_clean) < 25:
        return True
        
    title_lower = title_clean.lower()
    
    # Generic patterns
    generic_patterns = [
        r"^vid_\d+", r"^img_\d+", r"^mov_\d+", r"^sequence \d+", 
        r"^untitled", r"^capture", r"^video$", r"^short$", r"^play$"
    ]
    for pattern in generic_patterns:
        if re.match(pattern, title_lower):
            return True
            
    # Generic indicators combined with moderate length
    generic_indicators = ["vid_", "img_", "mov_", "sequence", "untitled", "capture", "video", "short", "play", "gameplay"]
    if any(ind in title_lower for ind in generic_indicators) and len(title_clean) < 35:
        return True
        
    return False

def main():
    csv_file = 'videos_update.csv'
    rows = []
    
    print("Filtering SEO updates in CSV...")
    
    kept_updates = 0
    reset_updates = 0
    
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            curr_title = row.get('current_title', '').strip()
            curr_desc = row.get('current_description', '').strip()
            curr_tags = row.get('current_tags', '').strip()
            
            # Condition to keep update: NO current description AND a basic title
            has_no_desc = not curr_desc
            has_basic_title = is_basic_title(curr_title)
            
            if has_no_desc and has_basic_title:
                # Keep the generated values
                kept_updates += 1
                rows.append(row)
            else:
                # Reset new values to current values (so no update is made)
                row['new_title'] = row['current_title']
                row['new_description'] = row['current_description']
                row['tags'] = row['current_tags']
                reset_updates += 1
                rows.append(row)
                
    # Write back to CSV
    with open(csv_file, mode='w', encoding='utf-8', newline='') as f:
        fieldnames = ["video_id", "current_title", "current_description", "current_tags", "new_title", "new_description", "tags"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    print(f"Filtering complete!")
    print(f"Total videos: {len(rows)}")
    print(f"Kept SEO updates for: {kept_updates} videos (No description + basic title)")
    print(f"Reset (preserved original): {reset_updates} videos")

if __name__ == '__main__':
    main()
