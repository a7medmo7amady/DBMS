from typing import Any, List, Optional, Tuple


class Node:

    def __init__(self, is_leaf: bool = False):
        self.keys: List[Any] = []
        self.children: List["Node"] = []
        self.values: List[Any] = []
        self.next_leaf: Optional["Node"] = None
        self.is_leaf = is_leaf

    def __repr__(self):
        return f"{'Leaf' if self.is_leaf else 'Internal'}({self.keys})"


class BPTree:
    """
    B+ Tree with full range scan support.

    Properties:
    - All data records live only in leaf nodes.
    - Leaf nodes are linked in sorted order via next_leaf.
    - Internal nodes store separator keys to guide searches.
    - Order `t` means each node holds between t-1 and 2t-1 keys (except root).
    """

    def __init__(self, order: int = 3):
        if order < 2:
            raise ValueError("Order must be >= 2")
        self.order = order
        self.max_keys = 2 * order - 1
        self.min_keys = order - 1
        self.root: Node = Node(is_leaf=True)
        self._size = 0

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def insert(self, key: Any, value: Any) -> None:
        """Insert a key-value pair. Duplicate keys update the existing value."""
        if len(self.root.keys) == self.max_keys:
            new_root = Node(is_leaf=False)
            new_root.children.append(self.root)
            self._split_child(new_root, 0)
            self.root = new_root

        self._insert_non_full(self.root, key, value)
        self._size += 1

    def search(self, key: Any) -> Optional[Any]:
        """Point lookup. Returns the value for key, or None if not found."""
        leaf = self._find_leaf(self.root, key)
        if key in leaf.keys:
            return leaf.values[leaf.keys.index(key)]
        return None

    def range_scan(self, low: Any, high: Any) -> List[Tuple[Any, Any]]:
        """
        Return all (key, value) pairs where low <= key <= high,
        in sorted order, by walking the leaf-node linked list.
        O(log N + K) where K is the number of results.
        """
        results = []
        leaf = self._find_leaf(self.root, low)
        while leaf is not None:
            for i, k in enumerate(leaf.keys):
                if k > high:
                    return results
                if k >= low:
                    results.append((k, leaf.values[i]))
            leaf = leaf.next_leaf
        return results

    def delete(self, key: Any) -> bool:
        """Delete a key. Returns True if deleted, False if not found."""
        if not self._delete(self.root, key):
            return False
        self._size -= 1
        if not self.root.is_leaf and len(self.root.keys) == 0:
            self.root = self.root.children[0]
        return True

    def __len__(self) -> int:
        return self._size

    def __contains__(self, key: Any) -> bool:
        return self.search(key) is not None

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    def _find_leaf(self, node: Node, key: Any) -> Node:
        """Walk down from node to the leaf that should contain key."""
        if node.is_leaf:
            return node
        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1
        return self._find_leaf(node.children[i], key)

    def _insert_non_full(self, node: Node, key: Any, value: Any) -> None:
        """Insert into a node that is guaranteed to have room."""
        if node.is_leaf:
            # Find the right position and insert in sorted order
            i = 0
            while i < len(node.keys) and node.keys[i] < key:
                i += 1
            if i < len(node.keys) and node.keys[i] == key:
                # Key already exists — update value instead
                node.values[i] = value
                self._size -= 1  # counteract the +1 in insert()
            else:
                node.keys.insert(i, key)
                node.values.insert(i, value)
        else:
            # Find which child to go into
            i = len(node.keys) - 1
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == self.max_keys:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def _split_child(self, parent: Node, child_index: int) -> None:
        """
        Split a full child node in two.
        - Leaf split:     middle key is COPIED UP (stays in the new right leaf)
        - Internal split: middle key is PUSHED UP (removed from the child)
        """
        t = self.order
        child = parent.children[child_index]
        new_node = Node(is_leaf=child.is_leaf)
        mid = t - 1

        if child.is_leaf:
            # Right half (including mid) goes into the new node
            new_node.keys   = child.keys[mid:]
            new_node.values = child.values[mid:]
            child.keys      = child.keys[:mid]
            child.values    = child.values[:mid]

            # Wire up the leaf linked list
            new_node.next_leaf = child.next_leaf
            child.next_leaf    = new_node

            separator = new_node.keys[0]   # smallest key of the new leaf
        else:
            # Mid key goes up to parent; not kept in either child
            separator        = child.keys[mid]
            new_node.keys    = child.keys[mid + 1:]
            new_node.children = child.children[mid + 1:]
            child.keys       = child.keys[:mid]
            child.children   = child.children[:mid + 1]

        parent.keys.insert(child_index, separator)
        parent.children.insert(child_index + 1, new_node)

    def _delete(self, node: Node, key: Any) -> bool:
        if node.is_leaf:
            if key not in node.keys:
                return False
            idx = node.keys.index(key)
            node.keys.pop(idx)
            node.values.pop(idx)
            return True

        i = 0
        while i < len(node.keys) and key >= node.keys[i]:
            i += 1

        child = node.children[i]
        deleted = self._delete(child, key)
        if not deleted:
            return False

        if len(child.keys) < self.min_keys:
            self._fix_underflow(node, i)

        self._update_separators(node, key)
        return True

    def _fix_underflow(self, parent: Node, child_idx: int) -> None:
        
        child = parent.children[child_idx]

        # Try borrowing from left sibling
        if child_idx > 0:
            left = parent.children[child_idx - 1]
            if len(left.keys) > self.min_keys:
                self._borrow_from_left(parent, child_idx)
                return

        if child_idx < len(parent.children) - 1:
            right = parent.children[child_idx + 1]
            if len(right.keys) > self.min_keys:
                self._borrow_from_right(parent, child_idx)
                return

        if child_idx > 0:
            self._merge(parent, child_idx - 1)
        else:
            self._merge(parent, child_idx)

    def _borrow_from_left(self, parent: Node, idx: int) -> None:
        child = parent.children[idx]
        left  = parent.children[idx - 1]
        if child.is_leaf:
            child.keys.insert(0, left.keys.pop())
            child.values.insert(0, left.values.pop())
            parent.keys[idx - 1] = child.keys[0]
        else:
            child.keys.insert(0, parent.keys[idx - 1])
            child.children.insert(0, left.children.pop())
            parent.keys[idx - 1] = left.keys.pop()

    def _borrow_from_right(self, parent: Node, idx: int) -> None:
        child = parent.children[idx]
        right = parent.children[idx + 1]
        if child.is_leaf:
            child.keys.append(right.keys.pop(0))
            child.values.append(right.values.pop(0))
            parent.keys[idx] = right.keys[0]
        else:
            child.keys.append(parent.keys[idx])
            child.children.append(right.children.pop(0))
            parent.keys[idx] = right.keys.pop(0)

    def _merge(self, parent: Node, left_idx: int) -> None:
        left  = parent.children[left_idx]
        right = parent.children[left_idx + 1]
        if left.is_leaf:
            left.keys      += right.keys
            left.values    += right.values
            left.next_leaf  = right.next_leaf
        else:
            left.keys      += [parent.keys[left_idx]] + right.keys
            left.children  += right.children
        parent.keys.pop(left_idx)
        parent.children.pop(left_idx + 1)

    def _update_separators(self, node: Node, deleted_key: Any) -> None:
        """If a separator equals the deleted key, replace it with the new minimum."""
        for i, k in enumerate(node.keys):
            if k == deleted_key:
                leaf = self._find_leaf(node.children[i + 1], deleted_key)
                if leaf.keys:
                    node.keys[i] = leaf.keys[0]

    # -------------------------------------------------------------------------
    # Visualisation
    # -------------------------------------------------------------------------

    def visualize(self) -> None:
        print("\n" + "=" * 60)
        print(f"B+ Tree  (order={self.order}, size={self._size})")
        print("=" * 60)
        if not self.root.keys and self.root.is_leaf:
            print("  (empty tree)")
            return

        queue = [(self.root, 0)]
        current_level = 0
        line = []
        while queue:
            node, level = queue.pop(0)
            if level != current_level:
                print(f"  Level {current_level}: " + "  |  ".join(line))
                line = []
                current_level = level
            line.append(str(node.keys))
            for child in node.children:
                queue.append((child, level + 1))
        print(f"  Level {current_level}: " + "  |  ".join(line))

        print("\n  Leaf chain (linked list):")
        leaf = self._find_leftmost_leaf()
        chain = []
        while leaf:
            chain.append(str(list(zip(leaf.keys, leaf.values))))
            leaf = leaf.next_leaf
        print("  " + " → ".join(chain))
        print("=" * 60 + "\n")

    def _find_leftmost_leaf(self) -> Node:
        node = self.root
        while not node.is_leaf:
            node = node.children[0]
        return node