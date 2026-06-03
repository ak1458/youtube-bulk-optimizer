import csv
from collections import Counter
import re

def clean_title(title):
    return re.sub(r'#\w+', '', title).strip()

def main():
    csv_file = 'videos_update.csv'
    games = []
    with open(csv_file, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            title = row.get('current_title', '').lower()
            
            # Detect game
            if "valorant" in title:
                games.append("Valorant")
            elif "rdr2" in title or "red dead" in title or "arthur morgan" in title:
                games.append("Red Dead Redemption 2")
            elif "control" in title:
                games.append("Control")
            elif "gta" in title or "grand theft auto" in title or "los santos" in title:
                games.append("Grand Theft Auto V")
            elif "forza" in title:
                games.append("Forza Horizon")
            elif "crew motorfest" in title or "crew 2" in title:
                games.append("The Crew Motorfest")
            elif "spectre" in title:
                games.append("Spectre")
            elif "resident evil" in title or "re9" in title:
                games.append("Resident Evil")
            elif "spider man" in title or "spiderman" in title:
                games.append("Spider-Man")
            elif "high on life" in title or "high on knife" in title:
                games.append("High on Life")
            elif "wukong" in title or "black myth" in title:
                games.append("Black Myth Wukong")
            elif "nioh" in title:
                games.append("Nioh")
            elif "reanimal" in title:
                games.append("Reanimal")
            elif "sleeping dogs" in title or "sleepingdog" in title:
                games.append("Sleeping Dogs")
            elif "cyberpunk" in title:
                games.append("Cyberpunk 2077")
            elif "god of war" in title:
                games.append("God of War")
            elif "unboxing" in title or "pc build" in title:
                games.append("Tech/Vlog")
            else:
                games.append("Unknown / General Gaming")
                
    counts = Counter(games)
    print("Game Distribution in CSV:")
    for game, count in counts.most_common():
        print(f"- {game}: {count}")

if __name__ == '__main__':
    main()
