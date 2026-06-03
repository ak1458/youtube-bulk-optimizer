import csv
import re

def clean_and_optimize(current_title, current_description, current_tags):
    title = current_title.strip()
    
    # Remove existing hashtags from the title (we will move them to description)
    title_cleaned = re.sub(r'#\w+', '', title).strip()
    # Remove double spaces
    title_cleaned = re.sub(r'\s+', ' ', title_cleaned)
    
    # Default tags and description components
    base_tags = ["gaming", "pc gaming", "gameplay", "pc gameplay", "lets play"]
    
    # Detect the game from the title
    title_lower = title.lower()
    
    game_detected = "PC Gaming"
    detected_tags = []
    hashtag_list = ["#gaming", "#pcgaming", "#gameplay"]
    
    # Game-specific heuristics
    if "valorant" in title_lower:
        game_detected = "Valorant"
        detected_tags = ["valorant", "valorant gameplay", "valorant live", "valorant highlights", "valorant clutch", "tactical shooter", "riot games", "fps", "valorant pc"]
        hashtag_list = ["#gaming", "#valorant", "#fps", "#pcgaming", "#riotgames"]
        
        # Optimize title
        if title_cleaned.lower() in ["valorant", "valorant live"]:
            title_cleaned = "VALORANT: Insane Ranked Gameplay & Tactical Clutches!"
        elif "live" in title_lower:
            title_cleaned = f"VALORANT LIVE: {title_cleaned.replace('live', '').replace('Live', '').strip()} - Ranked Grind!"
        else:
            title_cleaned = f"VALORANT: {title_cleaned} (Epic Gameplay & Highlights)"
            
    elif "rdr2" in title_lower or "red dead" in title_lower:
        game_detected = "Red Dead Redemption 2"
        detected_tags = ["rdr2", "red dead redemption 2", "rdr2 gameplay", "rdr2 pc", "arthur morgan", "rockstar games", "open world games"]
        hashtag_list = ["#gaming", "#rdr2", "#reddeadredemption2", "#rockstargames", "#openworld"]
        
        title_cleaned = f"Red Dead Redemption 2: {title_cleaned} - Ultra Graphics Gameplay!"
        
    elif "control" in title_lower:
        game_detected = "Control"
        detected_tags = ["control", "control gameplay", "control remedy", "supernatural", "sci fi games", "remedy entertainment", "action adventure"]
        hashtag_list = ["#gaming", "#controlgame", "#remedy", "#supernatural", "#actiongames"]
        
        if title_cleaned.lower() == "control" or title_cleaned.lower() == "control story":
            title_cleaned = "Control: Mind-Bending Supernatural Action & Story Walkthrough!"
        else:
            title_cleaned = f"Control: {title_cleaned} - High Action Sci-Fi Gameplay!"
            
    elif "gta" in title_lower or "grand theft auto" in title_lower:
        game_detected = "Grand Theft Auto V"
        detected_tags = ["gta 5", "gta v", "grand theft auto 5", "gta 5 gameplay", "gta 5 pc", "gta online", "rockstar games"]
        hashtag_list = ["#gaming", "#gta5", "#gtav", "#grandtheftauto", "#rockstargames"]
        
        if "stream" in title_lower or "live" in title_lower:
            title_cleaned = f"GTA 5 LIVE: {title_cleaned.replace('stream', '').replace('Stream', '').strip()} - Los Santos Chaos!"
        else:
            title_cleaned = f"GTA 5: {title_cleaned} - Epic High-Speed Action!"
            
    elif "forza" in title_lower or "crew motorfest" in title_lower or "racing" in title_lower:
        game_detected = "Racing Games"
        detected_tags = ["forza horizon", "the crew motorfest", "racing games", "supercars", "forza vs crew", "car games", "drift"]
        hashtag_list = ["#gaming", "#racing", "#forzahorizon", "#thecrewmotorfest", "#supercars"]
        
        if "vs" in title_lower:
            title_cleaned = "Forza Horizon vs The Crew Motorfest: Ultimate Car Racing Showdown!"
        else:
            title_cleaned = f"Epic Racing Action: {title_cleaned} - Ultra Settings!"
            
    elif "spectre" in title_lower:
        game_detected = "Spectre"
        detected_tags = ["spectre", "spectre game", "spectre gameplay", "horror games", "indie horror", "pc horror"]
        hashtag_list = ["#gaming", "#spectregame", "#horrorgames", "#indiehorror"]
        
        title_cleaned = f"Spectre: {title_cleaned} - Scariest PC Horror Gameplay!"
        
    else:
        # Fallback/General PC Gaming title optimization
        if len(title_cleaned) < 15:
            title_cleaned = f"Epic {title_cleaned} PC Gameplay - Walkthrough & Highlights!"
        else:
            title_cleaned = f"{title_cleaned} - Max Settings PC Gameplay!"

    # Capitalize title beautifully (Title Case)
    title_cleaned = title_cleaned.title()
    # Correct some common capitalized acronyms
    title_cleaned = title_cleaned.replace("Gta", "GTA").replace("Rdr2", "RDR2").replace("Fps", "FPS").replace("Pc", "PC").replace("Live", "LIVE").replace("Vs", "vs")

    # Generate a rich, structured description
    description_lines = [
        f"Welcome back to the channel! Today we are playing {game_detected}.",
        "",
        "If you enjoyed the video, make sure to leave a Like, Comment, and Subscribe for more high-quality gaming streams, walkthroughs, and highlights!",
        "",
        "--- PC SPECIFICATIONS ---",
        "🖥️ CPU: Intel Core i7 / AMD Ryzen 7",
        "🎮 GPU: NVIDIA GeForce RTX Series",
        "💾 RAM: 16GB / 32GB DDR4",
        "",
        "--- SOCIAL LINKS ---",
        "💬 Join the Discord: [Insert Link]",
        "📸 Instagram: [Insert Link]",
        "🐦 Twitter: [Insert Link]",
        "",
        " ".join(hashtag_list)
    ]
    new_description = "\n".join(description_lines)

    # Combine tags and remove duplicates
    all_tags = list(dict.fromkeys(detected_tags + base_tags))
    new_tags = ", ".join(all_tags)

    return title_cleaned, new_description, new_tags

def main():
    input_csv = "videos_update.csv"
    output_rows = []

    print("Reading and generating optimized SEO metadata...")
    with open(input_csv, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        
        for row in reader:
            video_id = row.get("video_id")
            current_title = row.get("current_title", "")
            current_description = row.get("current_description", "")
            current_tags = row.get("current_tags", "")

            # Optimize
            opt_title, opt_desc, opt_tags = clean_and_optimize(current_title, current_description, current_tags)

            output_rows.append({
                "video_id": video_id,
                "current_title": current_title,
                "current_description": current_description,
                "current_tags": current_tags,
                "new_title": opt_title,
                "new_description": opt_desc,
                "tags": opt_tags
            })

    # Write back to videos_update.csv
    with open(input_csv, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ["video_id", "current_title", "current_description", "current_tags", "new_title", "new_description", "tags"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"Successfully optimized SEO metadata for all {len(output_rows)} videos inside '{input_csv}'.")

if __name__ == "__main__":
    main()
