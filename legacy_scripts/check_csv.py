import csv

def main():
    csv_file = 'videos_update.csv'
    total = 0
    empty_desc = 0
    empty_new_desc = 0
    same_desc = 0
    basic_title = 0
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            curr_desc = row.get('current_description', '').strip()
            new_desc = row.get('new_description', '').strip()
            curr_title = row.get('current_title', '').strip()
            new_title = row.get('new_title', '').strip()
            
            if not curr_desc:
                empty_desc += 1
            if not new_desc:
                empty_new_desc += 1
            if curr_desc == new_desc:
                same_desc += 1
                
            # Basic title criteria: less than 15 chars, or starts with vid_, img_, etc.
            title_lower = curr_title.lower()
            if len(curr_title) < 20 or any(p in title_lower for p in ["vid_", "img_", "mov_", "sequence", "untitled", "capture", "short", "play"]):
                basic_title += 1
                
    print(f"Total rows in CSV: {total}")
    print(f"Empty current_description: {empty_desc}")
    print(f"Empty new_description: {empty_new_desc}")
    print(f"Same current and new description: {same_desc}")
    print(f"Basic title: {basic_title}")

if __name__ == '__main__':
    main()
