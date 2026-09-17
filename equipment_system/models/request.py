from __future__ import annotations

from dataclasses import dataclass

from equipment_system.models.equipment import EquipmentType


@dataclass
class LoanRequest:
    student_code: str
    equipment_type: EquipmentType
    request_minute: int

    def to_dict(self) -> dict:
        return {
            "student_code": self.student_code,
            "equipment_type": self.equipment_type.value,
            "request_minute": self.request_minute,
        }
