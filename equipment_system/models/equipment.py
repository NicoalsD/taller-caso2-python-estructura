from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class EquipmentType(str, Enum):
    PORTABLE = "PORTABLE"
    KIT = "KIT"
    MULTIMETER = "MULTIMETER"

    @classmethod
    def values(cls) -> list[str]:
        return [member.value for member in cls]

    @classmethod
    def from_value(cls, value: str | "EquipmentType") -> "EquipmentType":
        if isinstance(value, cls):
            return value
        for member in cls:
            if member.value == str(value).upper():
                return member
        raise ValueError(f"Unsupported equipment type: {value}")

    @property
    def display_name(self) -> str:
        return {
            self.PORTABLE: "Portable",
            self.KIT: "Kit",
            self.MULTIMETER: "Multimeter",
        }[self]


class EquipmentState(str, Enum):
    IN_CART = "IN_CART"
    LOANED = "LOANED"
    UNDER_REVIEW = "UNDER_REVIEW"
    MAINTENANCE = "MAINTENANCE"


@dataclass
class Equipment:
    code: str
    equipment_type: EquipmentType
    state: EquipmentState = EquipmentState.IN_CART
    loans_count: int = 0
    current_student: Optional[str] = None
    loan_start_minute: Optional[int] = None
    preventive_maintenance: bool = False
    damaged: bool = False
    iteration_note: str = ""

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "Equipment":
        equipment_type = EquipmentType.from_value(payload.get("type") or payload.get("equipment_type"))
        state_value = payload.get("state")
        state = EquipmentState(state_value) if state_value else EquipmentState.IN_CART
        return cls(
            code=str(payload["code"]),
            equipment_type=equipment_type,
            state=state,
            loans_count=int(payload.get("loans_count", 0)),
            current_student=payload.get("current_student"),
            loan_start_minute=payload.get("loan_start_minute"),
            preventive_maintenance=bool(payload.get("preventive_maintenance", False)),
            damaged=bool(payload.get("damaged", False)),
            iteration_note=str(payload.get("iteration_note") or ""),
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "type": self.equipment_type.value,
            "state": self.state.value,
            "loans_count": self.loans_count,
            "current_student": self.current_student,
            "loan_start_minute": self.loan_start_minute,
            "preventive_maintenance": self.preventive_maintenance,
            "damaged": self.damaged,
            "iteration_note": self.iteration_note,
        }
