import threading
from typing import Optional

from scope_timer.node import TimerNode
from scope_timer.infer import TimeProperty


class TimerThreadLocal(threading.local):
    active_node: Optional[TimerNode]
    root_nodes: dict[str, TimerNode]
    time_property: Optional[TimeProperty]

    def __init__(self):
        self.active_node = None
        self.root_nodes = {}
        self.time_property = None

    def reset(self):
        self.active_node = None
        self.root_nodes.clear()
        self.time_property = None
