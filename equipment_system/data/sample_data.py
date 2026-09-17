from __future__ import annotations

from equipment_system.data_structures.linked_list import LinkedList
from equipment_system.data_structures.queue import Queue
from equipment_system.data_structures.stack import Stack
from equipment_system.models.equipment import Equipment, EquipmentState, EquipmentType


def build_sample_inventory() -> list[dict]:
    return [
        {"code": "PORT-01", "type": "PORTABLE", "state": "IN_CART", "loans_count": 1},
        {"code": "PORT-02", "type": "PORTABLE", "state": "IN_CART", "loans_count": 0},
        {"code": "PORT-03", "type": "PORTABLE", "state": "IN_CART", "loans_count": 2},
        {"code": "KIT-01", "type": "KIT", "state": "IN_CART", "loans_count": 0},
        {"code": "KIT-02", "type": "KIT", "state": "IN_CART", "loans_count": 1},
        {"code": "MULT-01", "type": "MULTIMETER", "state": "IN_CART", "loans_count": 3},
        {"code": "MULT-02", "type": "MULTIMETER", "state": "IN_CART", "loans_count": 0},
    ]
