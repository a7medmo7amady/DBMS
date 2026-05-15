import sys
import traceback
from bptree import BPTree


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
PASS = "\033[92m✓ PASS\033[0m"
FAIL = "\033[91m✗ FAIL\033[0m"
_tests_run = 0
_tests_passed = 0


def check(description: str, condition: bool) -> None:
    global _tests_run, _tests_passed
    _tests_run += 1
    if condition:
        _tests_passed += 1
        print(f"  {PASS}  {description}")
    else:
        print(f"  {FAIL}  {description}")


def section(title: str) -> None:
    print(f"\n{'─'*55}")
    print(f"  {title}")
    print(f"{'─'*55}")


# ─────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────

def test_basic_insert_search():
    section("1. Basic Insert & Point Search")
    t = BPTree(order=3)

    t.insert(10, "ten")
    t.insert(20, "twenty")
    t.insert(5, "five")
    t.insert(15, "fifteen")
    t.insert(30, "thirty")

    check("search(10) == 'ten'",        t.search(10) == "ten")
    check("search(5)  == 'five'",       t.search(5)  == "five")
    check("search(30) == 'thirty'",     t.search(30) == "thirty")
    check("search(99) == None",         t.search(99) is None)
    check("10 in tree",                 10 in t)
    check("99 not in tree",             99 not in t)
    check("len(tree) == 5",             len(t) == 5)


def test_split_and_grow():
    section("2. Node Splitting & Tree Growth")
    t = BPTree(order=2)   # max 3 keys → splits happen quickly

    keys = list(range(1, 16))   # 1..15
    for k in keys:
        t.insert(k, k * 10)

    t.visualize()

    all_found = all(t.search(k) == k * 10 for k in keys)
    check("All 15 inserted keys found after multiple splits", all_found)
    check("len(tree) == 15", len(t) == 15)


def test_range_scan():
    section("3. Range Scans (Core B+ Tree Feature)")
    t = BPTree(order=3)

    data = [(i, f"v{i}") for i in range(1, 21)]   # (1..20)
    for k, v in data:
        t.insert(k, v)

    # Full range
    r = t.range_scan(1, 20)
    check("range_scan(1,20) returns 20 items",      len(r) == 20)
    check("range_scan results are sorted",          r == sorted(r))

    # Sub-range
    r = t.range_scan(5, 10)
    check("range_scan(5,10) returns 6 items",       len(r) == 6)
    check("range_scan(5,10) keys correct",          [k for k, _ in r] == [5,6,7,8,9,10])

    # Single-element range
    r = t.range_scan(7, 7)
    check("range_scan(7,7) returns exactly [(7,'v7')]", r == [(7, "v7")])

    # Empty range
    r = t.range_scan(100, 200)
    check("range_scan outside domain returns []",   r == [])

    # Boundary-touching range
    r = t.range_scan(18, 25)
    check("range_scan(18,25) → keys 18,19,20",     [k for k, _ in r] == [18, 19, 20])


def test_duplicate_key_update():
    section("4. Duplicate Key → Value Update")
    t = BPTree(order=3)
    t.insert(42, "original")
    t.insert(42, "updated")

    check("search(42) == 'updated'",    t.search(42) == "updated")
    check("size stays 1 after update",  len(t) == 1)


def test_delete():
    section("5. Delete & Underflow Handling")
    t = BPTree(order=2)

    for k in [10, 20, 30, 40, 50, 60]:
        t.insert(k, k)

    check("delete(30) returns True",    t.delete(30))
    check("30 no longer found",         t.search(30) is None)
    check("delete(99) returns False",   not t.delete(99))
    check("len after delete == 5",      len(t) == 5)

    # Delete all
    for k in [10, 20, 40, 50, 60]:
        t.delete(k)
    check("tree empty after deleting all", len(t) == 0)
    check("range_scan on empty tree → []", t.range_scan(0, 100) == [])


def test_large_dataset():
    section("6. Large Dataset (1,000 keys)")
    import random
    random.seed(42)

    t = BPTree(order=4)
    keys = random.sample(range(1, 10_001), 1_000)
    for k in keys:
        t.insert(k, k * 2)

    sorted_keys = sorted(keys)
    check("len == 1000",                len(t) == 1_000)
    check("All 1000 keys searchable",   all(t.search(k) == k * 2 for k in keys))

    lo, hi = sorted_keys[100], sorted_keys[200]
    r = t.range_scan(lo, hi)
    expected = [(k, k * 2) for k in sorted_keys if lo <= k <= hi]
    check(f"range_scan({lo},{hi}) matches expected", r == expected)


def test_string_keys():
    section("7. String Keys")
    t = BPTree(order=3)
    words = ["banana", "apple", "cherry", "date", "elderberry", "fig"]
    for w in words:
        t.insert(w, w.upper())

    check("search('apple') works",       t.search("apple") == "APPLE")
    r = t.range_scan("apple", "date")
    check("range_scan('apple','date')",  [k for k, _ in r] == sorted(w for w in words if "apple" <= w <= "date"))


def test_leaf_linked_list():
    section("8. Leaf Linked-List Integrity")
    t = BPTree(order=2)
    for k in [5, 3, 8, 1, 4, 7, 9, 2, 6]:
        t.insert(k, k)

    # Walk the linked list manually
    node = t._find_leftmost_leaf()
    collected = []
    while node:
        collected.extend(node.keys)
        node = node.next_leaf

    check("Leaf chain is fully sorted", collected == sorted(collected))
    check("Leaf chain contains all 9 keys", collected == list(range(1, 10)))


# ─────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────

def main():
    print("\n" + "=" * 55)
    print("  B+ Tree Test Suite")
    print("=" * 55)

    tests = [
        test_basic_insert_search,
        test_split_and_grow,
        test_range_scan,
        test_duplicate_key_update,
        test_delete,
        test_large_dataset,
        test_string_keys,
        test_leaf_linked_list,
    ]

    for test in tests:
        try:
            test()
        except Exception:
            print(f"\n  \033[91mERROR in {test.__name__}:\033[0m")
            traceback.print_exc()

    print(f"\n{'='*55}")
    color = "\033[92m" if _tests_passed == _tests_run else "\033[91m"
    print(f"  {color}Results: {_tests_passed}/{_tests_run} tests passed\033[0m")
    print(f"{'='*55}\n")
    sys.exit(0 if _tests_passed == _tests_run else 1)


if __name__ == "__main__":
    main()