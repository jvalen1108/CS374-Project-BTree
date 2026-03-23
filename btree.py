class BTreeNode:
    def __init__(self, t, leaf=False):
        self.t = t
        self.keys = []
        self.children = []
        self.values = []
        self.leaf = leaf
        

class BTree:
    def __init__(self, t):
        self.root = BTreeNode(t, leaf=True)
        self.t = t

    def search(self, key, node=None):
        if node is None:
            node = self.root        #default to root if no node provided
        i=0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and node.keys[i] == key:
            return node.values[i]
        if node.leaf:
            return None 
        return self.search(key, node.children[i])

    def _split_child(self, parent, index):
        t = self.t
        child = parent.children[index]
        new_node = BTreeNode(t, leaf=child.leaf)

        median_index = t - 1

        # Save median key/value before trimming
        median_key = child.keys[median_index]
        median_value = child.values[median_index]

        # Right half goes to new node
        new_node.keys = child.keys[median_index + 1:]
        new_node.values = child.values[median_index + 1:]

        # If not a leaf, split children as well
        if not child.leaf:
            new_node.children = child.children[t:]
            child.children = child.children[:t]

        child.keys = child.keys[:median_index]
        child.values = child.values[:median_index]

        parent.keys.insert(index, median_key)
        parent.values.insert(index, median_value)

        parent.children.insert(index + 1, new_node)

    def _insert_non_full(self, node, key, value):
        i = len(node.keys) - 1

        if node.leaf:
            # Find insertion position
            while i >= 0 and key < node.keys[i]:
                i -= 1

            # If key already exists, append to its value list
            if i >= 0 and node.keys[i] == key:
                node.values[i].append(value)
            else:
                insert_pos = i + 1
                node.keys.insert(insert_pos, key)
                node.values.insert(insert_pos, [value])
        else:
            # Find child to recurse into
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1

            # Split child first if full
            if len(node.children[i].keys) == 2 * self.t - 1:
                self._split_child(node, i)

                # After split, decide whether to go left or right
                if key > node.keys[i]:
                    i += 1
                elif key == node.keys[i]:
                    node.values[i].append(value)
                    return

            self._insert_non_full(node.children[i], key, value)

    def insert(self, key, value):
        root = self.root

        # If root is full, tree grows in height
        if len(root.keys) == 2 * self.t - 1:
            new_root = BTreeNode(self.t, leaf=False)
            new_root.children.append(root)
            self.root = new_root

            # Split old root
            self._split_child(new_root, 0)

            # Decide which child should receive the new key
            if key > new_root.keys[0]:
                child_index = 1
            elif key == new_root.keys[0]:
                new_root.values[0].append(value)
                return
            else:
                child_index = 0

            self._insert_non_full(new_root.children[child_index], key, value)
        else:
            self._insert_non_full(root, key, value)

    def traverse(self, node=None):
        if node is None:
            node = self.root

        results = []

        for i in range(len(node.keys)):
            if not node.leaf:
                results.extend(self.traverse(node.children[i]))
            results.append((node.keys[i], node.values[i]))

        if not node.leaf:
            results.extend(self.traverse(node.children[len(node.keys)]))

        return results

    def range_query(self, low, high, node=None):
        if node is None:
            node = self.root

        results = []

        for i in range(len(node.keys)):
            if not node.leaf and node.keys[i] >= low:
                results.extend(self.range_query(low, high, node.children[i]))

            if low <= node.keys[i] <= high:
                results.append((node.keys[i], node.values[i]))

        if not node.leaf and (len(node.keys) == 0 or node.keys[-1] <= high):
            results.extend(self.range_query(low, high, node.children[len(node.keys)]))

        return results
    
    def _get_predecessor(self, node):
        current = node
        while not current.leaf:
            current = current.children[-1]
        return current.keys[-1], current.values[-1]


    def _get_successor(self, node):
        current = node
        while not current.leaf:
            current = current.children[0]
        return current.keys[0], current.values[0]
        
    def _borrow_from_prev(self, parent, index):
        child = parent.children[index]
        left_sibling = parent.children[index - 1]

        # Parent separator moves down into front of child
        child.keys.insert(0, parent.keys[index - 1])
        child.values.insert(0, parent.values[index - 1])

        # Left sibling's last key moves up to parent
        parent.keys[index - 1] = left_sibling.keys.pop()
        parent.values[index - 1] = left_sibling.values.pop()

        # Move last child pointer if not leaf
        if not left_sibling.leaf:
            child.children.insert(0, left_sibling.children.pop())


    def _borrow_from_next(self, parent, index):
        child = parent.children[index]
        right_sibling = parent.children[index + 1]

        # Parent separator moves down into end of child
        child.keys.append(parent.keys[index])
        child.values.append(parent.values[index])

        # Right sibling's first key moves up to parent
        parent.keys[index] = right_sibling.keys.pop(0)
        parent.values[index] = right_sibling.values.pop(0)

        # Move first child pointer if not leaf
        if not right_sibling.leaf:
            child.children.append(right_sibling.children.pop(0))


    def _merge(self, parent, index):
        left_child = parent.children[index]
        right_child = parent.children[index + 1]

        # Pull separator from parent down into left child
        left_child.keys.append(parent.keys[index])
        left_child.values.append(parent.values[index])

        # Append all keys/values from right child
        left_child.keys.extend(right_child.keys)
        left_child.values.extend(right_child.values)

        # Append children if internal node
        if not left_child.leaf:
            left_child.children.extend(right_child.children)

        # Remove separator key/value from parent
        parent.keys.pop(index)
        parent.values.pop(index)

        # Remove right child from parent
        parent.children.pop(index + 1)

        # If parent was root and is now empty, shrink tree height
        if parent == self.root and len(parent.keys) == 0:
            self.root = left_child

    def delete(self, key, node=None):
        if node is None:
            node = self.root

        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1

        # KEY FOUND IN THIS NODE
        if i < len(node.keys) and node.keys[i] == key:
            if node.leaf:
                node.keys.pop(i)
                node.values.pop(i)
            else:
                left_child = node.children[i]
                right_child = node.children[i + 1]

                if len(left_child.keys) >= self.t:
                    pred_key, pred_value = self._get_predecessor(left_child)
                    node.keys[i] = pred_key
                    node.values[i] = pred_value
                    self.delete(pred_key, left_child)

                elif len(right_child.keys) >= self.t:
                    succ_key, succ_value = self._get_successor(right_child)
                    node.keys[i] = succ_key
                    node.values[i] = succ_value
                    self.delete(succ_key, right_child)

                else:
                    self._merge(node, i)
                    self.delete(key, node.children[i])


        else:
            if node.leaf:
                print("Key not found")
                return

            # child index to recurse into is i
            if len(node.children[i].keys) == self.t - 1:
                # Try borrowing from left sibling
                if i > 0 and len(node.children[i - 1].keys) >= self.t:
                    self._borrow_from_prev(node, i)

                # Try borrowing from right sibling
                elif i < len(node.children) - 1 and len(node.children[i + 1].keys) >= self.t:
                    self._borrow_from_next(node, i)

                # Must merge with a sibling
                else:
                    if i > 0:
                        self._merge(node, i - 1)
                        i -= 1
                    else:
                        self._merge(node, i)

            self.delete(key, node.children[i])

       
if __name__ == "__main__":
    tree = BTree(t=2)

    test_data = [
        (25.0, {"name": "Player A"}),
        (18.3, {"name": "Player B"}),
        (30.1, {"name": "Player C"}),
        (12.5, {"name": "Player D"}),
        (18.3, {"name": "Player E"}),
        (27.4, {"name": "Player F"}),
        (8.0,  {"name": "Player G"}),
        (22.0, {"name": "Player H"}),
    ]

    for ppg, info in test_data:
        tree.insert(ppg, info)
        print(f"Inserted {info['name']} at PPG {ppg}")

    print("\n--- Search Tests ---")
    result = tree.search(18.3)
    print(f"Search 18.3: {result}")
    result = tree.search(30.1)
    print(f"Search 30.1: {result}")
    result = tree.search(99.9)
    print(f"Search 99.9: {result}")

    # This needs to be indented here, inside the if block
    print("\n--- Traverse Test ---")
    for ppg, players in tree.traverse():
        print(f"  PPG {ppg}: {[p['name'] for p in players]}")
    
    print("\n--- Range Query: 20-30 PPG ---")
    for ppg, players in tree.range_query(20.0, 30.0):
        print(f"  PPG {ppg}: {[p['name'] for p in players]}")
        
    print("\n--- Delete Tests ---")

    # Delete a key that's in a leaf
    tree.delete(8.0)
    print(f"After deleting 8.0, search 8.0: {tree.search(8.0)}")

    # Delete a key that's in an internal node
    tree.delete(25.0)
    print(f"After deleting 25.0, search 25.0: {tree.search(25.0)}")

    # Try deleting a key that doesn't exist
    tree.delete(99.9)

    # Verify tree is still intact
    print("\n--- Traverse After Deletes ---")
    for ppg, players in tree.traverse():
        print(f"  PPG {ppg}: {[p['name'] for p in players]}")