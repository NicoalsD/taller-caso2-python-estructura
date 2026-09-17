from dataclasses import dataclass


@dataclass
class Node:
    data: object
    next_node: "Node | None" = None
