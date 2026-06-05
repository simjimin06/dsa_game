# leaderboard.py

import json
import heapq
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
LEADERBOARD_FILE = DATA_DIR / "leaderboard.json"


def ensure_leaderboard_file():
    DATA_DIR.mkdir(exist_ok=True)

    if not LEADERBOARD_FILE.exists():
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)


def load_leaderboard():
    ensure_leaderboard_file()

    try:
        with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            return data

        return []

    except json.JSONDecodeError:
        return []


def save_leaderboard(entries):
    ensure_leaderboard_file()

    with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=4, ensure_ascii=False)


def calculate_score(turn_count, hp=100, items_collected=0, enemies_defeated=0):
    base_score = 1000
    turn_penalty = turn_count * 5
    hp_bonus = hp * 2
    item_bonus = items_collected * 50
    enemy_bonus = enemies_defeated * 100

    score = base_score - turn_penalty + hp_bonus + item_bonus + enemy_bonus
    return max(score, 0)


def build_max_heap(entries):
    heap = []

    for entry in entries:
        name = str(entry.get("name", "Unknown"))
        score = int(entry.get("score", 0))
        turns = int(entry.get("turns", 999999))

        # heapq is a min heap, so we store negative score for max-heap behavior.
        heap.append((-score, turns, name))

    heapq.heapify(heap)
    return heap


def get_top_scores_from_entries(entries, limit=10):
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
    entries = load_leaderboard()
    return get_top_scores_from_entries(entries, limit)


def add_score(name, score, turns):
    entries = load_leaderboard()

    entries.append({
        "name": str(name),
        "score": int(score),
        "turns": int(turns)
    })

    save_leaderboard(entries)
    return get_top_scores(limit=10)


def clear_leaderboard():
    save_leaderboard([])


def print_top_scores(top_scores):
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
    print("Leaderboard test started.")
    print("-" * 40)

    sample_entries = [
        {"name": "Jimin", "score": 1200, "turns": 35},
        {"name": "Alex", "score": 900, "turns": 50},
        {"name": "Mina", "score": 1500, "turns": 42},
        {"name": "Chris", "score": 1200, "turns": 30},
        {"name": "Dana", "score": 700, "turns": 60},
    ]

    print("Sample leaderboard using heap:")
    top_scores = get_top_scores_from_entries(sample_entries)
    print_top_scores(top_scores)

    print("-" * 40)

    sample_score = calculate_score(
        turn_count=40,
        hp=80,
        items_collected=3,
        enemies_defeated=2
    )

    print(f"Sample calculated score: {sample_score}")

    print("-" * 40)

    print("Current saved leaderboard:")
    saved_scores = get_top_scores()
    print_top_scores(saved_scores)

    print("-" * 40)
    print("All leaderboard tests finished.")


if __name__ == "__main__":
    test_leaderboard()