from __future__ import annotations

from typing import Iterator, Optional

from .node import Node


class Queue:
    def __init__(self) -> None:
        self.front: Optional[Node] = None
        self.rear: Optional[Node] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self.front is None

    def enqueue(self, item: object) -> None:
        node = Node(item)
        if self.rear is None:
            self.front = node
            self.rear = node
        else:
            self.rear.next_node = node
            self.rear = node
        self._size += 1

    def dequeue(self) -> object:
        if self.front is None:
            raise IndexError("Queue is empty")
        item = self.front.data
        self.front = self.front.next_node
        if self.front is None:
            self.rear = None
        self._size -= 1
        return item

    def peek(self) -> object:
        if self.front is None:
            raise IndexError("Queue is empty")
        return self.front.data

    def to_list(self) -> list[object]:
        items: list[object] = []
        current = self.front
        while current is not None:
            items.append(current.data)
            current = current.next_node
        return items

    def __iter__(self) -> Iterator[object]:
        current = self.front
        while current is not None:
            yield current.data
            current = current.next_node

    def clear(self) -> None:
        self.front = None
        self.rear = None
        self._size = 0
