import csv
import re

def is_generic_title(title):
    title_lower = title.lower().strip()
    generic_patterns = [
        r"^vid_\d+", r"^img_\d+", r"^mov_\d+", r"^sequence \d+", 
        r"^untitled", r"^capture", r"^video$", r"^short$", r"^play$"
    ]
    for pattern in generic_patterns:
        if re.match(pattern, title_lower):
            return True
    if len(title.strip()) < 15:
        return True
    return False

def main():
    csv_file = 'videos_update.csv'
    count = 0
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            curr_desc = row.get('current_description', '').strip()
            curr_title = row.get('current_title', '').strip()
            if not curr_desc:
                is_gen = is_generic_title(curr_title)
                print(f"{idx+1}. ID: {row['video_id']} | Title: \"{curr_title}\" | IsGeneric: {is_gen}")
                count += 1
                if count >= 30:
                    print("... and more")
                    break

if __name__ == '__main__':
    main()
