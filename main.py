# main.py

from game import Game


def main():
    try:
        name = input("Enter player name: ").strip()
    except EOFError:
        name = ""

    if not name:
        name = "Player"

    game = Game(player_name=name)
    game.run()


if __name__ == "__main__":
    main()