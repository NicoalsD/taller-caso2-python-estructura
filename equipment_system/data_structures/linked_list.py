from __future__ import annotations

from typing import Callable, Iterable, Iterator, Optional

from .node import Node


class LinkedList:
    def __init__(self) -> None:
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self._size = 0

    def __len__(self) -> int:
        return self._size

    def is_empty(self) -> bool:
        return self.head is None

    def append(self, item: object) -> None:
        node = Node(item)
        if self.head is None:
            self.head = node
            self.tail = node
        else:
            self.tail.next_node = node
            self.tail = node
        self._size += 1

    def prepend(self, item: object) -> None:
        node = Node(item, self.head)
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1

    def remove(self, item: object) -> bool:
        if self.head is None:
            return False
        if self.head.data == item:
            self.head = self.head.next_node
            if self.head is None:
                self.tail = None
            self._size -= 1
            return True
        current = self.head
        while current.next_node is not None:
            if current.next_node.data == item:
                current.next_node = current.next_node.next_node
                if current.next_node is None:
                    self.tail = current
                self._size -= 1
                return True
            current = current.next_node
        return False

    def remove_by(self, predicate: Callable[[object], bool]) -> object | None:
        if self.head is None:
            return None
        if predicate(self.head.data):
            removed = self.head.data
            self.head = self.head.next_node
            if self.head is None:
                self.tail = None
            self._size -= 1
            return removed
        current = self.head
        while current.next_node is not None:
            if predicate(current.next_node.data):
                removed = current.next_node.data
                current.next_node = current.next_node.next_node
                if current.next_node is None:
                    self.tail = current
                self._size -= 1
                return removed
            current = current.next_node
        return None

    def find(self, predicate: Callable[[object], bool]) -> object | None:
        current = self.head
        while current is not None:
            if predicate(current.data):
                return current.data
            current = current.next_node
        return None

    def __iter__(self) -> Iterator[object]:
        current = self.head
        while current is not None:
            yield current.data
            current = current.next_node

    def __contains__(self, item: object) -> bool:
        return self.find(lambda each: each == item) is not None

    def to_list(self) -> list[object]:
        return list(self)
