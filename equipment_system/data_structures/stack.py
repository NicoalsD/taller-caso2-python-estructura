from __future__ import annotations

from typing import Iterator, Optional

from .node import Node


class Stack:
    def __init__(self) -> None:
        self.top: Optional[Node] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self.top is None

    def push(self, item: object) -> None:
        self.top = Node(item, self.top)
        self._size += 1

    def pop(self) -> object:
        if self.top is None:
            raise IndexError("Stack is empty")
        item = self.top.data
        self.top = self.top.next_node
        self._size -= 1
        return item

    def peek(self) -> object:
        if self.top is None:
            raise IndexError("Stack is empty")
        return self.top.data

    def to_list(self) -> list[object]:
        items: list[object] = []
        current = self.top
        while current is not None:
            items.append(current.data)
            current = current.next_node
        return items

    def __iter__(self) -> Iterator[object]:
        current = self.top
        while current is not None:
            yield current.data
            current = current.next_node

    def clear(self) -> None:
        self.top = None
        self._size = 0
