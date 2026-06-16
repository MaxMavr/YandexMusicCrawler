import json
from config import PoolConfig


class Pool:
    def save(self):
        with open(self.file, "w", encoding="utf-8") as f:
            json.dump(list(self.pool), f, ensure_ascii=False, indent=4)

    def __init__(self, config: PoolConfig):
        self.pool = set()
        self.save_frequency = config.save_frequency
        self.steps_since_last_save = 0
        self.file = config.file

        if not self.file.exists():
            self.save()
            return

        with open(self.file, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.pool.update(data)

    def __len__(self):
        return len(self.pool)

    def _check_save(self):
        self.steps_since_last_save += 1
        if self.steps_since_last_save >= self.save_frequency:
            self.save()
            self.steps_since_last_save = 0

    def next(self):
        self._check_save()
        return self.pool.pop()

    def update(self, extend_queue: list):
        self._check_save()
        return self.pool.update(extend_queue)

