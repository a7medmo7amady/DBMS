# B+ Tree with Range Scans
## Advanced Database Systems — Application Component

### Files
| File | Description |
|------|-------------|
| `bptree.py` | Core B+ Tree implementation |
| `test_bptree.py` | Full test suite (31 tests) |

### How to Run

```bash
# Run all tests
python test_bptree.py

# Quick demo
python -c "
from bptree import BPlusTree
t = BPlusTree(order=3)
for k in range(1, 20):
    t.insert(k, k*100)
t.visualize()
print('Range scan [5,10]:', t.range_scan(5, 10))
"
```


### Features Implemented
- Insert with automatic node splitting (copy-up for leaves, push-up for internal)
- Point search (O log N)
- **Range scan via leaf linked list — O(log N + K)**
- Delete with underflow handling (redistribute left/right, merge)
- Duplicate key update
- Tree visualiser (level-order BFS)
- Supports any comparable key type (int, str, float, …)
