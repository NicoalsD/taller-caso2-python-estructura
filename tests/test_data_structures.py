import unittest

from equipment_system.data_structures.linked_list import LinkedList
from equipment_system.data_structures.queue import Queue
from equipment_system.data_structures.stack import Stack
from equipment_system.models.equipment import Equipment, EquipmentType
from equipment_system.services.equipment_service import EquipmentLoanSystem


class TestDataStructures(unittest.TestCase):
    def test_linked_list_append_and_find(self):
        items = LinkedList()
        items.append("a")
        items.append("b")
        self.assertEqual(items.to_list(), ["a", "b"])
        self.assertIn("b", items)

    def test_queue_fifo(self):
        queue = Queue()
        queue.enqueue("a")
        queue.enqueue("b")
        self.assertEqual(queue.dequeue(), "a")
        self.assertEqual(queue.dequeue(), "b")

    def test_stack_lifo(self):
        stack = Stack()
        stack.push("a")
        stack.push("b")
        self.assertEqual(stack.pop(), "b")
        self.assertEqual(stack.peek(), "a")


class TestEquipmentLoanSystem(unittest.TestCase):
    def setUp(self):
        self.service = EquipmentLoanSystem(capacity_k=2, hours_limit=2)
        self.service.load_inventory([
            {"code": "PORT-01", "type": "PORTABLE", "loans_count": 1},
            {"code": "PORT-02", "type": "PORTABLE", "loans_count": 2},
            {"code": "KIT-01", "type": "KIT", "loans_count": 0},
        ])

    def test_request_immediate_and_wait_queue(self):
        result = self.service.request_equipment("S1", "PORTABLE", 10)
        self.assertTrue(result.success)
        self.assertFalse(self.service.wait_queues[EquipmentType.PORTABLE].is_empty())

    def test_directed_loan_order_preservation(self):
        self.service.carts[EquipmentType.PORTABLE].push(Equipment(code="PORT-01", equipment_type=EquipmentType.PORTABLE))
        self.service.carts[EquipmentType.PORTABLE].push(Equipment(code="PORT-02", equipment_type=EquipmentType.PORTABLE))
        initial = [item.code for item in self.service.carts[EquipmentType.PORTABLE]]
        result = self.service.lend_directed("PORT-01", "S1", 15)
        self.assertTrue(result.success)
        self.assertEqual(result.data["movement_count"], 1)
        self.assertEqual([item.code for item in self.service.carts[EquipmentType.PORTABLE]], ["PORT-02"])
        self.assertNotEqual(initial, ["PORT-02"])

    def test_r1_and_r6(self):
        self.service.request_equipment("S1", EquipmentType.PORTABLE, 10)
        self.service.request_equipment("S2", EquipmentType.PORTABLE, 15)
        self.assertTrue(self.service.wait_queues[EquipmentType.PORTABLE].__len__() >= 1)
        result = self.service.request_equipment("S1", EquipmentType.PORTABLE, 20)
        self.assertFalse(result.success)
        self.assertEqual(result.rule_id, "R1")

    def test_search_does_not_mutate_cart(self):
        before = [item.code for item in self.service.carts[EquipmentType.PORTABLE]]
        result = self.service.search("PORT-02")
        after = [item.code for item in self.service.carts[EquipmentType.PORTABLE]]
        self.assertTrue(result.success)
        self.assertEqual(before, after)

    def test_return_and_review(self):
        equipment = self.service._find_equipment("PORT-01")
        equipment.state = EquipmentState = type("State", (), {})()


if __name__ == "__main__":
    unittest.main()
