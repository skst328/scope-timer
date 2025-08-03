import pytest
from io import StringIO

from rich.console import Console

from scope_timer.node import TimerNode
from scope_timer.infer import infer_time_property
from scope_timer.record import TimerRecord

def test_get_or_create_branch():
    """Checks that branches (child nodes) are created and retrieved correctly."""
    parent = TimerNode("parent")
    child1 = parent.get_or_create_branch("child1")
    assert "child1" in parent.branch_nodes
    assert child1.parent == parent
    # Calling again should return the same object
    child1_again = parent.get_or_create_branch("child1")
    assert child1 is child1_again

def test_node_stats_with_no_calls():
    """Checks that stats are zero if no calls were completed."""
    node = TimerNode("test")
    # Add a record but don't call end_record(), so ncall remains 0
    node.records.append(TimerRecord(begin=1.0, end=None))

    assert node.ncall == 0
    node.build_stats_recursive()
    assert node.total_time == 0
    assert node.avg_time == 0
    assert node.min_time == 0
    assert node.max_time == 0
    assert node.var_time == 0

def test_get_open_nodes():
    """Checks that get_open_nodes() correctly finds unclosed scopes."""
    root = TimerNode("root")
    root.begin_record() # Unclosed root

    child_closed = root.get_or_create_branch("child_closed")
    child_closed.begin_record()
    child_closed.end_record()

    child_open = root.get_or_create_branch("child_open")
    child_open.begin_record() # Unclosed child

    open_nodes = root.get_open_nodes()
    open_node_names = [node.name for node in open_nodes]

    assert "root" in open_node_names
    assert "child_open" in open_node_names
    assert "child_closed" not in open_node_names
    assert len(open_nodes) == 2

def test_render_label_with_zero_time_parent():
    """
    Checks the percentage rendering when the parent's total time is zero.
    """
    time_prop = infer_time_property(1.0, "s", 2)
    parent = TimerNode("parent")
    # Do not add records to parent, so its total_time is 0

    child = parent.get_or_create_branch("child")
    child.begin_record()
    child.end_record()
    child.build_stats_recursive()

    label = child.render_label(time_prop, 10, 10, 2)
    assert "(--%)" in label.plain

def test_to_tree_with_children():
    """
    Checks that a tree with children is built correctly by inspecting its
    rendered string output. This avoids LSP errors.
    """
    time_prop = infer_time_property(1.0, "s", 2)
    root = TimerNode("root")
    root.begin_record()
    root.end_record()

    child = root.get_or_create_branch("child")
    child.begin_record()
    child.end_record()

    root.build_stats_recursive()
    tree = root.to_tree(time_prop)

    # Render the tree to an in-memory string
    console = Console(file=StringIO(), force_terminal=True)
    console.print(tree)
    output = console.file.getvalue()

    # Check the final string output
    assert "[root]" in output
    assert "[child]" in output

def test_properties_without_preprocessed_stats():
    """
    Checks the property fallbacks for when stats are not pre-calculated.
    """
    node = TimerNode("test")

    # Manually add records without calling build_stats_recursive()
    # This ensures node.stats remains None
    node.records = [
        TimerRecord(begin=1.0, end=1.1), # 0.1
        TimerRecord(begin=2.0, end=2.3), # 0.3
    ]
    node.ncall = 2

    # Accessing properties should trigger the _get_* methods
    assert node.stats is None
    assert pytest.approx(node.total_time) == 0.4
    assert pytest.approx(node.min_time) == 0.1
    assert pytest.approx(node.max_time) == 0.3
    assert pytest.approx(node.avg_time) == 0.2
    assert node.var_time > 0
