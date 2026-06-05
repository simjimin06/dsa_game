# inventory.py

class Inventory:
    def __init__(self, initial_items=None):
        if initial_items is None:
            initial_items = {}

        self.items = dict(initial_items)

    def add(self, item_name, amount=1):
        if amount <= 0:
            return

        self.items[item_name] = self.items.get(item_name, 0) + amount

    def remove(self, item_name, amount=1):
        if amount <= 0:
            return False

        if self.items.get(item_name, 0) < amount:
            return False

        self.items[item_name] -= amount

        if self.items[item_name] <= 0:
            del self.items[item_name]

        return True

    def get(self, item_name, default=0):
        return self.items.get(item_name, default)

    def has(self, item_name, amount=1):
        return self.items.get(item_name, 0) >= amount

    def entries(self):
        return self.items.items()

    def is_empty(self):
        return len(self.items) == 0

    def to_text(self):
        if self.is_empty():
            return "empty"

        return ", ".join(
            f"{name} x{count}"
            for name, count in self.items.items()
        )