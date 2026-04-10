from lru_policy import LRUPolicy
from lru_k_policy import LRUKPolicy


class BufferPool:
    def __init__(self, size, policy="LRU", k=2):
        self.size = size
        self.k = k
        self.frames = []
        self.page_table = {}
        self.time = 0
        self.access_history = {}

        if policy == "LRU":
            self.policy = LRUPolicy()
        elif policy == "LRU-K":
            self.policy = LRUKPolicy()
        else:
            raise ValueError(f"Unknown policy: {policy}")

    def fetch_page(self, page_id):
        self.time += 1

        if page_id in self.page_table:
            print("HIT")
            self.policy.on_hit(page_id, self.frames)
            self.record_access(page_id)
        else:
            print("MISS")
            if len(self.frames) == self.size:
                self.policy.evict(
                    self.frames, self.page_table, self.access_history, k=self.k
                )
            self.frames.append(page_id)
            self.page_table[page_id] = True
            self.record_access(page_id)

        print("Frames:", self.frames)

    def record_access(self, page_id):
        if page_id not in self.access_history:
            self.access_history[page_id] = []

        self.access_history[page_id].append(self.time)

        if len(self.access_history[page_id]) > self.k:
            self.access_history[page_id].pop(0)


print("LRU")
bp1 = BufferPool(3, "LRU")
for page in [1, 2, 3, 1, 4, 2, 5]:
    bp1.fetch_page(page)

print("\nLRU-K")
bp2 = BufferPool(3, "LRU-K", 2)
for page in [1, 2, 3, 1, 4, 2, 1, 5]:
    bp2.fetch_page(page)
