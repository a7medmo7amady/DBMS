class LRUKPolicy:
    def evict(self, frames, page_table, access_history, k, **kwargs):
        less_than_k = [p for p in frames if len(access_history[p]) < k]

        if less_than_k:
            victim = min(less_than_k, key=lambda p: access_history[p][-1])
        else:
            victim = min(frames, key=lambda p: access_history[p][0])

        frames.remove(victim)
        del page_table[victim]
        del access_history[victim]
        print("Evicted:", victim)

    def on_hit(self, page_id, frames, **kwargs):
        pass
