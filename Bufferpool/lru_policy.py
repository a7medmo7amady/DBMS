class LRUPolicy:
    def evict(self, frames, page_table, access_history, **kwargs):
        victim = frames.pop(0)
        del page_table[victim]
        del access_history[victim]
        print("Evicted:", victim)

    def on_hit(self, page_id, frames, **kwargs):
        frames.remove(page_id)
        frames.append(page_id)
