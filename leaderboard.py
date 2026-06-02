# leaderboard.py

import json
import heapq
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
LEADERBOARD_FILE = DATA_DIR / "leaderboard.json"


def ensure_leaderboard_file():
    """
    Create data/leaderboard.json if it does not exist.
    """
    DATA_DIR.mkdir(exist_ok=True)

    if not LEADERBOARD_FILE.exists():
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)


def load_leaderboard():
    """
    Load leaderboard data from JSON file.

    Returns:
        list of dictionaries
        Example:
        [
            {"name": "Jimin", "score": 1200, "turns": 35}
        ]
    """
    ensure_leaderboard_file()

    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            return []

        return data

    except json.JSONDecodeError:
        return []


def save_leaderboard(entries):
    """
    Save leaderboard entries to JSON file.
    """
    ensure_leaderboard_file()

    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=4, ensure_ascii=False)


def calculate_score(turn_count, hp=100, items_collected=0):
    """
    Calculate final score.

    Higher score is better.
    Fewer turns, higher HP, and more collected items produce a better score.
    """
    base_score = 1000
    turn_penalty = turn_count * 5
    hp_bonus = hp * 2
    item_bonus = items_collected * 50

    score = base_score - turn_penalty + hp_bonus + item_bonus

    return max(score, 0)


def build_max_heap(entries):
    """
    Build a max heap using Python's min heap.

    Python heapq is a min heap, so score is stored as negative.
    If scores are tied, fewer turns rank higher.
    """
    heap = []

    for entry in entries:
        name = str(entry.get("name", "Unknown"))
        score = int(entry.get("score", 0))
        turns = int(entry.get("turns", 999999))

        heapq.heappush(heap, (-score, turns, name))

    return heap


def get_top_scores_from_entries(entries, limit=10):
    """
    Return top scores from a given entry list.
    This is useful for testing without changing leaderboard.json.
    """
    heap = build_max_heap(entries)
    top_scores = []
    rank = 1

    while heap and len(top_scores) < limit:
        negative_score, turns, name = heapq.heappop(heap)

        top_scores.append({
            "rank": rank,
            "name": name,
            "score": -negative_score,
            "turns": turns
        })

        rank += 1

    return top_scores


def get_top_scores(limit=10):
    """
    Load saved leaderboard and return top scores.
    """
    entries = load_leaderboard()
    return get_top_scores_from_entries(entries, limit)


def add_score(name, score, turns):
    """
    Add a new score to leaderboard.json.
    """
    entries = load_leaderboard()

    new_entry = {
        "name": name,
        "score": int(score),
        "turns": int(turns)
    }

    entries.append(new_entry)
    save_leaderboard(entries)

    return get_top_scores()


def clear_leaderboard():
    """
    Reset leaderboard.
    Use only when needed.
    """
    save_leaderboard([])


def print_top_scores(top_scores):
    """
    Print leaderboard in terminal.
    """
    if not top_scores:
        print("Leaderboard is empty.")
        return

    print("Rank | Name       | Score | Turns")
    print("-" * 36)

    for entry in top_scores:
        print(
            f"{entry['rank']:>4} | "
            f"{entry['name']:<10} | "
            f"{entry['score']:>5} | "
            f"{entry['turns']:>5}"
        )


def test_leaderboard():
    """
    Test leaderboard logic without modifying leaderboard.json.
    """
    print("Leaderboard test started.")
    print("-" * 40)

    sample_entries = [
        {"name": "Jimin", "score": 1200, "turns": 35},
        {"name": "Alex", "score": 900, "turns": 50},
        {"name": "Mina", "score": 1500, "turns": 42},
        {"name": "Chris", "score": 1200, "turns": 30},
        {"name": "Dana", "score": 700, "turns": 60},
    ]

    print("Sample leaderboard using max heap:")
    top_scores = get_top_scores_from_entries(sample_entries, limit=10)
    print_top_scores(top_scores)

    print("-" * 40)

    score = calculate_score(turn_count=40, hp=80, items_collected=3)
    print(f"Sample calculated score: {score}")

    print("-" * 40)

    print("Current saved leaderboard:")
    saved_top_scores = get_top_scores(limit=10)
    print_top_scores(saved_top_scores)

    print("-" * 40)
    print("All leaderboard tests finished.")


if __name__ == "__main__":
    test_leaderboard()