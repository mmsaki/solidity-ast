import pytest
from pathlib import Path
from lsp.ast import Root


class Src:
    def __init__(self, src: str):
        (a, b, c) = src.split(":")
        self.byteoffset = a
        self.length = b
        self.context = c


@pytest.fixture
def f():
    """
    forge build C.sol --json --ast --no-cache > ~/Developer/lsp/test/c.forge.ast.json
    """
    filename = "test/c.forge.ast.json"
    filepath = Path(filename)
    return Root(file_path=filepath)


def test_byte_offset():
    src = "9212:3:6"
    s = Src(src)
    assert s.byteoffset == "9212"
    assert s.length == "3"
    assert s.context == "6"


def test_position_index(f):
    """Test the spatial indexing system"""
    # Test that the position index was built
    assert f.position_index is not None
    assert len(f.position_index.file_id_to_path) > 0
    assert len(f.position_index.node_by_id) > 0

    # Test finding a node at a position
    # This would need actual file content and positions from your test data
    print(f"Indexed {len(f.position_index.node_by_id)} nodes")
    print(f"File mappings: {f.position_index.file_id_to_path}")


def test_lsp_position_conversion():
    """Test LSP position to byte offset conversion"""
    from lsp.ast import lsp_position_to_byte_offset, byte_offset_to_lsp_position

    content = "Hello\nWorld\n🌍"

    # Test basic conversion
    byte_offset = lsp_position_to_byte_offset(content, 1, 0)  # Start of "World"
    assert byte_offset == 6

    # Test reverse conversion
    line, char = byte_offset_to_lsp_position(content, 6)
    assert line == 1
    assert char == 0

    # Test with emoji (multi-byte character)
    byte_offset = lsp_position_to_byte_offset(content, 2, 0)  # Start of emoji line
    line, char = byte_offset_to_lsp_position(content, byte_offset)
    assert line == 2
