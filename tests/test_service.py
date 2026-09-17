import unittest

from equipment_system.data_structures.linked_list import LinkedList
from equipment_system.data_structures.queue import Queue
from equipment_system.data_structures.stack import Stack


class TestCustomStructures(unittest.TestCase):
    def test_linked_list(self):
        linked = LinkedList()
        linked.append("first")
        linked.append("second")
        self.assertEqual(linked.to_list(), ["first", "second"])

    def test_stack(self):
        stack = Stack()
        stack.push(1)
        stack.push(2)
        self.assertEqual(stack.pop(), 2)
        self.assertEqual(stack.peek(), 1)

    def test_queue(self):
        queue = Queue()
        queue.enqueue("a")
        queue.enqueue("b")
        self.assertEqual(queue.dequeue(), "a")
        self.assertEqual(queue.dequeue(), "b")


if __name__ == "__main__":
    unittest.main()
