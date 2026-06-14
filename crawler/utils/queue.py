import json
from collections import deque

from config import QueueConfig


class Queue:
    def save(self):
        with open(self.queue_file, "w", encoding="utf-8") as f:
            json.dump(list(self.queue), f, ensure_ascii=False, indent=4)

    def __init__(self, config: QueueConfig):
        self.queue = deque()
        self.save_frequency = config.save_frequency
        self.steps_since_last_save = 0
        self.queue_file = config.queue_file

        if not self.queue_file.exists():
            self.save()
            return

        with open(self.queue_file, "r", encoding="utf-8") as f:
            self.queue.extend(json.load(f))

    def __len__(self):
        return len(self.queue)

    def _check_save(self):
        self.steps_since_last_save += 1
        if self.steps_since_last_save >= self.save_frequency:
            self.save()
            self.steps_since_last_save = 0

    def popleft(self):
        self._check_save()
        return self.queue.popleft()

    def extend(self, extend_queue: list[int]):
        self._check_save()
        return self.queue.extend(extend_queue)

