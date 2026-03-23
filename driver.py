from btree import BTree
import csv

def load_and_aggregate(filepath):
    """
    Read per-game data and aggregate into player-season averages.
    Returns a list of dicts, each representing one player's season.
    """
    player_seasons = {}

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["gameType"] != "Regular Season":
                continue

            # Determine NBA season
            date_str = row["gameDateTimeEst"]
            year = int(date_str[:4])
            month = int(date_str[5:7])

            if month < 8:
                season_year = year - 1
            else:
                season_year = year

            # Only include 2004 season or after
            if season_year < 2004:
                continue

            season = f"{season_year}-{str(season_year + 1)[-2:]}"

            pid = row["personId"]
            key = (pid, season)

            if key not in player_seasons:
                player_seasons[key] = {
                    "name": f"{row['firstName']} {row['lastName']}",
                    "team": f"{row['playerteamCity']} {row['playerteamName']}",
                    "season": season,
                    "total_points": 0,
                    "total_assists": 0,
                    "total_rebounds": 0,
                    "games_played": 0,
                }

            stats = player_seasons[key]
            stats["total_points"] += float(row["points"])
            stats["total_assists"] += float(row["assists"])
            stats["total_rebounds"] += float(row["reboundsTotal"])
            stats["games_played"] += 1

    results = []
    for key, stats in player_seasons.items():
        gp = stats["games_played"]
        if gp > 0:
            stats["ppg"] = round(stats["total_points"] / gp, 1)
            stats["apg"] = round(stats["total_assists"] / gp, 1)
            stats["rpg"] = round(stats["total_rebounds"] / gp, 1)
        if gp >= 40:  # Only include players with 40+ games
            results.append(stats)
        
    

    return results


if __name__ == "__main__":
    # 1 — Load and insert
    file_path = r"C:\Users\josev\Downloads\archive\PlayerStatistics.csv"    
    records = load_and_aggregate(file_path)

    tree = BTree(t=5)

    inserted_count = 0
    for record in records:
        tree.insert(record["ppg"], record)
        inserted_count += 1

    print("=== B-Tree Demo ===")
    print(f"Inserted {inserted_count} records into the B-Tree.\n")

    print("\n" + "=" * 50)

    # 2 — Search demo
    print("=== Search Demo ===")
    existing_ppg = 25.7   # placeholder
    result = tree.search(existing_ppg)
    print(f"Search for PPG {existing_ppg}:")
    if result:
            for player in result:
                print(f"  {player['name']} | {player['season']} | {player['team']} | PPG: {existing_ppg} | APG: {player['apg']} | RPG: {player['rpg']}")
    else:
            print("  Not found")

    missing_ppg = 99.9
    missing_result = tree.search(missing_ppg)
    print(f"\nSearch for PPG {missing_ppg}:")
    if missing_result:
        for player in missing_result:
            print(f"  {player['name']} | {player['season']} | {player['team']} | PPG: {missing_ppg}")
    else:
        print("  Not found")

    print("\n" + "=" * 50)

    #3 — Range query demo
    print("=== Range Query Demo (28.0 to 30.0 PPG) ===")
    elite_scorers = tree.range_query(28.0, 30.0)

    for ppg, players in elite_scorers:
        for player in players:
            print(f"{player['name']} | {player['season']} | {player['team']} | PPG: {ppg}")
       
    print("\n" + "=" * 50)
    
    #4 — Traverse demo
    print("=== Traverse Demo ===")
    all_results = tree.traverse()

    flat_results = []
    for ppg, players in all_results:
        for player in players:
            flat_results.append((ppg, player))
            
    print("First 5 (lowest PPG):")
    for ppg, player in flat_results[:5]:
        print(f"  {player['name']} | {player['season']} | {player['team']} | PPG: {ppg}")

    print("\nLast 5 (highest PPG):")
    for ppg, player in flat_results[-5:]:
        print(f"  {player['name']} | {player['season']} | {player['team']} | PPG: {ppg}")

    print(f"\nTotal records in traversal: {len(flat_results)}\n")
    
    print("\n" + "=" * 50)

    #5 — Delete demo
    print("=== Delete Demo ===")
    delete_ppg = 25.7  

    before_delete = tree.search(delete_ppg)
    print(f"Before deleting PPG {delete_ppg}:")
    if before_delete:
        for player in before_delete:
            print(f"  {player['name']} | {player['season']} | {player['team']} | PPG: {delete_ppg}")
    else:
        print("  Not found")

    tree.delete(delete_ppg)

    after_delete = tree.search(delete_ppg)
    print(f"\nAfter deleting PPG {delete_ppg}:")
    if after_delete:
        for player in after_delete:
            print(f"  {player['name']} | {player['season']} | {player['team']} | PPG: {delete_ppg}")
    else:
        print("  Not found")

    after_delete_results = tree.traverse()
    new_total_records = sum(len(players) for _, players in after_delete_results)
    print(f"\nTotal records after deletion: {new_total_records}")