import csv
import re
import os

def is_basic_title(title):
    title_clean = re.sub(r'#\w+', '', title).strip()
    if len(title_clean) < 25:
        return True
        
    title_lower = title_clean.lower()
    generic_patterns = [
        r"^vid_\d+", r"^img_\d+", r"^mov_\d+", r"^sequence \d+", 
        r"^untitled", r"^capture", r"^video$", r"^short$", r"^play$"
    ]
    for pattern in generic_patterns:
        if re.match(pattern, title_lower):
            return True
            
    generic_indicators = ["vid_", "img_", "mov_", "sequence", "untitled", "capture", "video", "short", "play", "gameplay"]
    if any(ind in title_lower for ind in generic_indicators) and len(title_clean) < 35:
        return True
        
    return False

def filter_csv_metadata(csv_file='videos_update.csv'):
    if not os.path.exists(csv_file):
        return 0, 0
        
    rows = []
    kept_updates = 0
    reset_updates = 0
    
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            curr_title = row.get('current_title', '').strip()
            curr_desc = row.get('current_description', '').strip()
            
            # Keep updates only for: no description AND basic title
            has_no_desc = not curr_desc
            has_basic_title = is_basic_title(curr_title)
            
            if has_no_desc and has_basic_title:
                kept_updates += 1
            else:
                row['new_title'] = row['current_title']
                row['new_description'] = row['current_description']
                row['tags'] = row['current_tags']
                reset_updates += 1
            rows.append(row)
            
    # Save back
    with open(csv_file, mode='w', encoding='utf-8', newline='') as f:
        fieldnames = ["video_id", "current_title", "current_description", "current_tags", "new_title", "new_description", "tags"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        
    return kept_updates, reset_updates
