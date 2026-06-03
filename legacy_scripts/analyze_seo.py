import csv
import re

def is_generic_title(title):
    title_lower = title.lower().strip()
    
    # Common default/generic camera and recording software prefixes
    generic_patterns = [
        r"^vid_\d+", r"^img_\d+", r"^mov_\d+", r"^sequence \d+", 
        r"^untitled", r"^capture", r"^video$", r"^short$", r"^play$"
    ]
    
    for pattern in generic_patterns:
        if re.match(pattern, title_lower):
            return True
            
    # Also flag extremely short titles (less than 15 characters) as generic/unoptimized
    if len(title.strip()) < 15:
        return True
        
    return False

def main():
    csv_file = "videos_update.csv"
    
    total_videos = 0
    no_description = 0
    no_tags = 0
    no_hashtags = 0
    generic_titles = 0
    zero_seo_critical = []

    with open(csv_file, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            total_videos += 1
            title = row.get("current_title", "")
            description = row.get("current_description", "")
            tags = row.get("current_tags", "")

            # 1. Check if description is missing
            has_desc = bool(description.strip())
            if not has_desc:
                no_description += 1

            # 2. Check if tags are missing
            has_tags = bool(tags.strip())
            if not has_tags:
                no_tags += 1

            # 3. Check for hashtags (#) in title or description
            has_hash = "#" in title or "#" in description
            if not has_hash:
                no_hashtags += 1

            # 4. Check if title is generic or too short
            generic_title = is_generic_title(title)
            if generic_title:
                generic_titles += 1

            # 5. Critical "0 SEO" check (No description AND no tags AND no hashtags AND generic title)
            if not has_desc and not has_tags and not has_hash and generic_title:
                zero_seo_critical.append({
                    "id": row.get("video_id"),
                    "title": title
                })

    print("=" * 60)
    print("                 YOUTUBE VIDEO SEO ANALYSIS                    ")
    print("=" * 60)
    print(f"Total Videos Analyzed : {total_videos}")
    print("-" * 60)
    print(f"[-] No Description     : {no_description} videos ({(no_description/total_videos)*100:.1f}%)")
    print(f"[-] No Tags            : {no_tags} videos ({(no_tags/total_videos)*100:.1f}%)")
    print(f"[-] No Hashtags (#)    : {no_hashtags} videos ({(no_hashtags/total_videos)*100:.1f}%)")
    print(f"[!] Generic/Short Title : {generic_titles} videos ({(generic_titles/total_videos)*100:.1f}%)")
    print("-" * 60)
    
    critical_count = len(zero_seo_critical)
    print(f"[CRITICAL] '0 SEO' VIDEOS : {critical_count} videos ({(critical_count/total_videos)*100:.1f}%)")
    print("   (These have generic titles, NO description, NO tags, and NO hashtags!)")
    print("=" * 60)

    if critical_count > 0:
        print("\nHere are some of your critical '0 SEO' videos that need immediate optimization:")
        # Show up to 15 critical videos
        for idx, video in enumerate(zero_seo_critical[:15]):
            print(f" {idx + 1}. [ID: {video['id']}] \"{video['title']}\"")
        if critical_count > 15:
            print(f" ... and {critical_count - 15} more videos.")
            
        print("\nTip: You can find these IDs in your 'videos_update.csv' and update their 'new_title', 'new_description', and 'tags' columns!")
    else:
        print("\n[SUCCESS] Great news! None of your videos have absolute '0 SEO' (completely unoptimized across all criteria).")
    print("=" * 60)

if __name__ == "__main__":
    main()
