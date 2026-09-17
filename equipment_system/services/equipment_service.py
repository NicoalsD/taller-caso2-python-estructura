from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from equipment_system.data_structures.linked_list import LinkedList
from equipment_system.data_structures.queue import Queue
from equipment_system.data_structures.stack import Stack
from equipment_system.models.equipment import Equipment, EquipmentState, EquipmentType
from equipment_system.models.operation_result import OperationResult
from equipment_system.models.request import LoanRequest


class EquipmentLoanSystem:
    def __init__(self, capacity_k: int = 5, hours_limit: int = 8) -> None:
        self.capacity_k = capacity_k
        self.hours_limit = hours_limit
        self.inventory = LinkedList()
        self.carts: Dict[EquipmentType, Stack] = {
            equipment_type: Stack() for equipment_type in EquipmentType
        }
        self.wait_queues: Dict[EquipmentType, Queue] = {
            equipment_type: Queue() for equipment_type in EquipmentType
        }
        self.review_queue = Queue()
        self.store_queue = Queue()
        self.logs: List[Dict[str, Any]] = []
        self.directed_loans_total = 0
        self.directed_loans_count = 0
        self.total_wait_minutes = 0
        self.waiting_records: List[Dict[str, Any]] = []
        self.overdue_students: set[str] = set()
        self._last_error_rule: Optional[str] = None

    def _log(self, message: str, success: bool = True, rule_id: Optional[str] = None, **data: Any) -> None:
        entry = {
            "message": message,
            "success": success,
            "rule_id": rule_id,
            "timestamp": len(self.logs) + 1,
            "data": data,
        }
        self.logs.append(entry)

    def _ensure_equipment_type(self, equipment_type: EquipmentType | str) -> EquipmentType:
        if isinstance(equipment_type, EquipmentType):
            return equipment_type
        return EquipmentType.from_value(equipment_type)

    def _find_equipment(self, code: str) -> Optional[Equipment]:
        return self.inventory.find(lambda equipment: isinstance(equipment, Equipment) and equipment.code == code)

    def _find_wait_request(self, student_code: str, equipment_type: EquipmentType) -> Optional[LoanRequest]:
        for request in self.wait_queues[equipment_type]:
            if isinstance(request, LoanRequest) and request.student_code == student_code:
                return request
        return None

    def _student_has_active_type(self, student_code: str, equipment_type: EquipmentType) -> bool:
        for equipment in self.inventory:
            if isinstance(equipment, Equipment) and equipment.current_student == student_code and equipment.equipment_type == equipment_type:
                if equipment.state == EquipmentState.LOANED:
                    return True
        return False

    def _student_queued_for_type(self, student_code: str, equipment_type: EquipmentType) -> bool:
        return self._find_wait_request(student_code, equipment_type) is not None

    def _update_overdue_students(self, minute: int) -> None:
        self.overdue_students.clear()
        for equipment in self.inventory:
            if isinstance(equipment, Equipment) and equipment.state == EquipmentState.LOANED and equipment.current_student:
                if equipment.loan_start_minute is None:
                    continue
                if minute - equipment.loan_start_minute > self.hours_limit * 60:
                    self.overdue_students.add(equipment.current_student)

    def _lend_to_student(self, equipment_type: EquipmentType, student_code: str, minute: int, reason: str = "Loaned") -> OperationResult:
        if self.carts[equipment_type].is_empty():
            return OperationResult(False, f"No equipment available for {equipment_type.value}.", "R2")
        equipment = self.carts[equipment_type].pop()
        if not isinstance(equipment, Equipment):
            return OperationResult(False, "Invalid equipment object found on cart.", "R2")
        equipment.state = EquipmentState.LOANED
        equipment.current_student = student_code
        equipment.loan_start_minute = minute
        equipment.loans_count += 1
        self._log(f"{reason}: {equipment.code} to {student_code}", True)
        self._update_overdue_students(minute)
        return OperationResult(True, f"{equipment.code} loaned to {student_code}.", None, {"equipment": equipment.to_dict()})

    def _place_equipment_in_cart(self, equipment: Equipment) -> None:
        cart = self.carts[equipment.equipment_type]
        if cart.__len__() < self.capacity_k:
            equipment.state = EquipmentState.IN_CART
            cart.push(equipment)
        else:
            equipment.state = EquipmentState.IN_CART
            self.store_queue.enqueue(equipment)

    def load_inventory(self, data: Iterable[dict], capacity_k: Optional[int] = None) -> OperationResult:
        if capacity_k is not None:
            self.capacity_k = capacity_k
        self.inventory = LinkedList()
        for equipment_type in EquipmentType:
            self.carts[equipment_type] = Stack()
            self.wait_queues[equipment_type] = Queue()
        self.review_queue = Queue()
        self.store_queue = Queue()
        self.logs = []
        self.directed_loans_total = 0
        self.directed_loans_count = 0
        self.total_wait_minutes = 0
        self.waiting_records = []
        self.overdue_students = set()
        self._log("Inventory loaded", True)
        for item in data:
            equipment = Equipment.from_dict(item)
            equipment.state = EquipmentState.IN_CART
            self.inventory.append(equipment)
            self._place_equipment_in_cart(equipment)
            self._log(f"Loaded equipment {equipment.code}", True)
        return OperationResult(True, "Inventory loaded successfully.", None, {"count": len(self.inventory)})

    def request_equipment(self, student_code: str, equipment_type: EquipmentType | str, minute: int) -> OperationResult:
        equipment_type = self._ensure_equipment_type(equipment_type)
        if self._student_has_active_type(student_code, equipment_type):
            self._last_error_rule = "R1"
            return OperationResult(False, f"Student {student_code} already has a {equipment_type.value} equipment on loan.", "R1")
        if self._student_queued_for_type(student_code, equipment_type):
            self._last_error_rule = "R1"
            return OperationResult(False, f"Student {student_code} is already on the wait queue for {equipment_type.value}.", "R1")
        self._update_overdue_students(minute)
        if student_code in self.overdue_students:
            self._last_error_rule = "R6"
            return OperationResult(False, f"Student {student_code} is in arrears and cannot request equipment.", "R6")
        if not self.carts[equipment_type].is_empty():
            result = self._lend_to_student(equipment_type, student_code, minute, "Immediate request")
            if result.success:
                self._log(f"Request served immediately for {student_code}", True)
                return result
            return result
        request = LoanRequest(student_code, equipment_type, minute)
        self.wait_queues[equipment_type].enqueue(request)
        self._log(f"Queued request for {student_code} in {equipment_type.value}", True)
        return OperationResult(True, f"Request queued for {student_code}.", None, {"request": request.to_dict()})

    def lend(self, equipment_type: EquipmentType | str, student_code: Optional[str] = None, minute: Optional[int] = None) -> OperationResult:
        equipment_type = self._ensure_equipment_type(equipment_type)
        if self.carts[equipment_type].is_empty():
            return OperationResult(False, f"No equipment available in {equipment_type.value} cart.", "R2")
        if minute is None:
            minute = 0
        student = student_code or "UNASSIGNED"
        return self._lend_to_student(equipment_type, student, minute, "Manual loan")

    def lend_directed(self, code: str, student_code: Optional[str] = None, minute: Optional[int] = None) -> OperationResult:
        if minute is None:
            minute = 0
        equipment = self._find_equipment(code)
        if equipment is None:
            return OperationResult(False, f"Equipment {code} not found in inventory.", "R4")
        if equipment.state != EquipmentState.IN_CART:
            return OperationResult(False, f"Equipment {code} is not in a cart and cannot be directed.", "R4")
        cart = self.carts[equipment.equipment_type]
        auxiliary = Stack()
        movement_history: list[dict] = []
        movement_count = 0
        found = False
        while not cart.is_empty() and not found:
            current = cart.pop()
            movement_count += 1
            movement_history.append({"from": "main", "to": "aux", "code": current.code if isinstance(current, Equipment) else str(current)})
            if current.code == code:
                found = True
                current.state = EquipmentState.LOANED
                current.current_student = student_code or "DIRECTED"
                current.loan_start_minute = minute
                current.loans_count += 1
                self.directed_loans_count += 1
            else:
                auxiliary.push(current)
        if not found:
            while not auxiliary.is_empty():
                item = auxiliary.pop()
                cart.push(item)
                movement_count += 1
                movement_history.append({"from": "aux", "to": "main", "code": item.code})
            return OperationResult(False, f"Equipment {code} not found in the {equipment.equipment_type.value} cart.", "R4")
        while not auxiliary.is_empty():
            item = auxiliary.pop()
            cart.push(item)
            movement_count += 1
            movement_history.append({"from": "aux", "to": "main", "code": item.code})
        self.directed_loans_total += movement_count
        self._log(f"Directed loan for {code} took {movement_count} moves.", True)
        return OperationResult(True, f"Directed loan succeeded for {code}.", None, {
            "equipment_code": code,
            "movement_count": movement_count,
            "movement_history": movement_history,
            "equipment": equipment.to_dict(),
        })

    def return_equipment(self, code: str, minute: int) -> OperationResult:
        equipment = self._find_equipment(code)
        if equipment is None:
            return OperationResult(False, f"Equipment {code} does not exist.", "R5")
        if equipment.state != EquipmentState.LOANED:
            return OperationResult(False, f"Equipment {code} is not currently loaned.", "R5")
        if equipment.loan_start_minute is None:
            return OperationResult(False, f"Equipment {code} has no loan start time recorded.", "R5")
        if not equipment.current_student:
            return OperationResult(False, f"Equipment {code} has no assigned student.", "R5")
        duration_minutes = minute - equipment.loan_start_minute
        overdue = duration_minutes > self.hours_limit * 60
        if overdue:
            self.overdue_students.add(equipment.current_student)
        else:
            self.overdue_students.discard(equipment.current_student)
        equipment.state = EquipmentState.UNDER_REVIEW
        equipment.current_student = None
        equipment.loan_start_minute = None
        self.review_queue.enqueue(equipment)
        self._log(f"Returned {code} at minute {minute}; overdue={overdue}", True, "R6" if overdue else None)
        return OperationResult(True, f"Equipment {code} queued for review.", None, {
            "equipment": equipment.to_dict(),
            "duration_minutes": duration_minutes,
            "overdue": overdue,
        })

    def review_next(self, result: str) -> OperationResult:
        if self.review_queue.is_empty():
            return OperationResult(False, "There are no items in the review queue.", "R5")
        equipment = self.review_queue.dequeue()
        if not isinstance(equipment, Equipment):
            return OperationResult(False, "Invalid review item.", "R5")
        normalized = str(result).upper()
        if normalized == "APPROVE":
            if equipment.loans_count >= 5:
                equipment.state = EquipmentState.MAINTENANCE
                equipment.preventive_maintenance = True
                self._log(f"{equipment.code} moved into preventive maintenance.", True, "R8")
                return OperationResult(True, f"{equipment.code} sent to maintenance.", None, {"equipment": equipment.to_dict()})
            if self.carts[equipment.equipment_type].__len__() < self.capacity_k:
                equipment.state = EquipmentState.IN_CART
                self.carts[equipment.equipment_type].push(equipment)
                self._log(f"{equipment.code} approved and stored back in the cart.", True, "R5")
            else:
                equipment.state = EquipmentState.IN_CART
                self.store_queue.enqueue(equipment)
                self._log(f"{equipment.code} approved but sent to store queue due to full cart.", True, "R7")
            self._flush_store_queue(equipment.equipment_type)
            self.attend_waiting(equipment.equipment_type)
            return OperationResult(True, f"Equipment {equipment.code} reviewed successfully.", None, {"equipment": equipment.to_dict()})
        if normalized in {"DAMAGE", "DAMAGED"}:
            equipment.state = EquipmentState.MAINTENANCE
            equipment.damaged = True
            self._log(f"{equipment.code} marked as damaged and sent to maintenance.", True, "R5")
            return OperationResult(True, f"Equipment {equipment.code} reported as damaged.", None, {"equipment": equipment.to_dict()})
        return OperationResult(False, f"Unrecognized review decision: {result}.", "R5")

    def attend_waiting(self, equipment_type: EquipmentType | str) -> OperationResult:
        equipment_type = self._ensure_equipment_type(equipment_type)
        queue = self.wait_queues[equipment_type]
        if queue.is_empty() or self.carts[equipment_type].is_empty():
            return OperationResult(False, f"No waiting request or equipment available for {equipment_type.value}.", "R3")
        request = queue.dequeue()
        if not isinstance(request, LoanRequest):
            return OperationResult(False, "Queue item is invalid.", "R3")
        equipment = self.carts[equipment_type].pop()
        if not isinstance(equipment, Equipment):
            return OperationResult(False, "Cart item is invalid.", "R3")
        equipment.state = EquipmentState.LOANED
        equipment.current_student = request.student_code
        equipment.loan_start_minute = request.request_minute
        equipment.loans_count += 1
        wait_minutes = request.request_minute if request.request_minute >= 0 else 0
        self.waiting_records.append({
            "student_code": request.student_code,
            "equipment_type": equipment_type.value,
            "wait_minutes": wait_minutes,
        })
        self.total_wait_minutes += wait_minutes
        self._log(f"Attended waiting request for {request.student_code} in {equipment_type.value}.", True, "R3")
        return OperationResult(True, f"Waiting request served for {request.student_code}.", None, {
            "request": request.to_dict(),
            "equipment": equipment.to_dict(),
        })

    def search(self, code: str) -> OperationResult:
        equipment = self._find_equipment(code)
        if equipment is None:
            return OperationResult(False, f"Equipment {code} was not found.", "R8")
        position = None
        if equipment.state == EquipmentState.IN_CART:
            cart = self.carts[equipment.equipment_type]
            temp = Stack()
            index = 0
            while not cart.is_empty():
                item = cart.pop()
                index += 1
                if isinstance(item, Equipment) and item.code == code:
                    position = index
                temp.push(item)
            while not temp.is_empty():
                cart.push(temp.pop())
        return OperationResult(True, f"Equipment {code} located.", None, {
            "code": equipment.code,
            "type": equipment.equipment_type.value,
            "state": equipment.state.value,
            "position_from_top": position,
            "equipment": equipment.to_dict(),
        })

    def _flush_store_queue(self, equipment_type: EquipmentType) -> None:
        while not self.store_queue.is_empty() and self.carts[equipment_type].__len__() < self.capacity_k:
            item = self.store_queue.dequeue()
            if not isinstance(item, Equipment):
                continue
            item.state = EquipmentState.IN_CART
            self.carts[equipment_type].push(item)
            self._log(f"Stored queued equipment {item.code} back in the {equipment_type.value} cart.", True, "R7")

    def report(self) -> Dict[str, Any]:
        equipment_by_state: Dict[str, int] = {state.value: 0 for state in EquipmentState}
        equipment_by_type: Dict[str, int] = {equipment_type.value: 0 for equipment_type in EquipmentType}
        occupancy: Dict[str, int] = {}
        for equipment in self.inventory:
            if not isinstance(equipment, Equipment):
                continue
            equipment_by_state[equipment.state.value] += 1
            equipment_by_type[equipment.equipment_type.value] += 1
        for equipment_type in EquipmentType:
            occupancy[equipment_type.value] = self.carts[equipment_type].__len__()
        total_waits = len(self.waiting_records)
        average_wait = (self.total_wait_minutes / total_waits) if total_waits else 0
        immediate_requests = 0
        queued_requests = 0
        for log in self.logs:
            if "Request served immediately" in log["message"]:
                immediate_requests += 1
            if "Queued request" in log["message"]:
                queued_requests += 1
        most_borrowed = None
        max_loans = -1
        for equipment in self.inventory:
            if isinstance(equipment, Equipment):
                if equipment.loans_count > max_loans:
                    max_loans = equipment.loans_count
                    most_borrowed = equipment.code
        damaged_returns = sum(1 for equipment in self.inventory if isinstance(equipment, Equipment) and equipment.damaged)
        maintenance_count = sum(1 for equipment in self.inventory if isinstance(equipment, Equipment) and equipment.state == EquipmentState.MAINTENANCE)
        preventive_count = sum(1 for equipment in self.inventory if isinstance(equipment, Equipment) and equipment.preventive_maintenance)
        overdue_count = len(self.overdue_students)
        return {
            "equipment_by_state": equipment_by_state,
            "equipment_by_type": equipment_by_type,
            "cart_occupancy": occupancy,
            "immediate_requests": immediate_requests,
            "queued_requests": queued_requests,
            "average_wait_minutes": average_wait,
            "directed_loans_count": self.directed_loans_count,
            "total_directed_movements": self.directed_loans_total,
            "damaged_returns": damaged_returns,
            "equipment_in_maintenance": maintenance_count,
            "equipment_in_arrears": overdue_count,
            "most_borrowed_equipment": most_borrowed,
            "preventive_maintenance_count": preventive_count,
            "logs": self.logs,
        }

    def get_inventory_snapshot(self) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        for equipment in self.inventory:
            if isinstance(equipment, Equipment):
                items.append(equipment.to_dict())
        return items

    def get_waiting_snapshot(self) -> Dict[str, list[dict]]:
        snapshot: Dict[str, list[dict]] = {}
        for equipment_type in EquipmentType:
            queue_items = self.wait_queues[equipment_type].to_list()
            snapshot[equipment_type.value] = [item.to_dict() for item in queue_items if isinstance(item, LoanRequest)]
        return snapshot

    def get_cart_snapshot(self) -> Dict[str, list[str]]:
        snapshot: Dict[str, list[str]] = {}
        for equipment_type in EquipmentType:
            items: list[str] = []
            for equipment in self.carts[equipment_type]:
                if isinstance(equipment, Equipment):
                    items.append(equipment.code)
            snapshot[equipment_type.value] = items
        return snapshot

    def get_review_snapshot(self) -> list[dict]:
        items: list[dict] = []
        for equipment in self.review_queue:
            if isinstance(equipment, Equipment):
                items.append(equipment.to_dict())
        return items

    def get_store_snapshot(self) -> list[dict]:
        items: list[dict] = []
        for equipment in self.store_queue:
            if isinstance(equipment, Equipment):
                items.append(equipment.to_dict())
        return items

    def get_logs(self) -> list[dict]:
        return [dict(entry) for entry in self.logs]

    def get_most_recent_error(self) -> Optional[str]:
        return self._last_error_rule
