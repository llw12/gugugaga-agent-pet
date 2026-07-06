from app.main import get_fixed_command_intent


def test_node_version_intent_maps_to_fixed_command():
    assert get_fixed_command_intent("node版本") == "check_node"


def test_npm_version_intent_maps_to_fixed_command():
    assert get_fixed_command_intent("npm版本") == "check_npm"


def test_direct_command_tool_text_does_not_map_to_command():
    assert get_fixed_command_intent("command.check_node") is None
