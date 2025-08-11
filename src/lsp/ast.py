import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class Severity(Enum):
    WARNING = "warning"
    ERROR = "error"


class ErrorType(Enum):
    WARNING = "Warning"
    ERROR = "Error"


@dataclass
class SourceLocation:
    file: str
    start: int
    end: int


@dataclass
class AstNodeIndex:
    """Spatial index entry for AST nodes"""

    node_id: int
    file_id: int
    start_byte: int
    end_byte: int
    node_type: str
    node_data: dict
    depth: int  # nesting depth for finding innermost node


@dataclass
class PositionIndex:
    """Spatial index for fast position-to-node lookups"""

    file_nodes: Dict[int, List[AstNodeIndex]] = field(default_factory=dict)
    node_by_id: Dict[int, AstNodeIndex] = field(default_factory=dict)
    file_id_to_path: Dict[int, str] = field(default_factory=dict)

    def add_node(self, node_index: AstNodeIndex):
        """Add a node to the spatial index"""
        file_id = node_index.file_id
        if file_id not in self.file_nodes:
            self.file_nodes[file_id] = []

        self.file_nodes[file_id].append(node_index)
        self.node_by_id[node_index.node_id] = node_index

    def finalize_index(self):
        """Sort nodes by start position for binary search"""
        for file_id in self.file_nodes:
            self.file_nodes[file_id].sort(key=lambda x: (x.start_byte, -x.depth))

    def find_nodes_at_position(
        self, file_id: int, byte_offset: int
    ) -> List[AstNodeIndex]:
        """Find all nodes containing the given byte offset"""
        if file_id not in self.file_nodes:
            return []

        nodes = self.file_nodes[file_id]
        containing_nodes = []

        for node in nodes:
            if node.start_byte <= byte_offset < node.end_byte:
                containing_nodes.append(node)

        # Sort by depth (deepest first) for innermost node
        containing_nodes.sort(key=lambda x: -x.depth)
        return containing_nodes

    def find_innermost_node(
        self, file_id: int, byte_offset: int
    ) -> Optional[AstNodeIndex]:
        """Find the innermost (deepest) node containing the position"""
        nodes = self.find_nodes_at_position(file_id, byte_offset)
        return nodes[0] if nodes else None


@dataclass
class Errors:
    source_location: SourceLocation
    error_type: ErrorType
    error_code: int
    severity: Severity
    message: str


class NodeType(Enum):
    source_unit = "SourceUnit"
    contract = "ContractDefinition"
    interface = "InterfaceDefinition"
    variable = "VariableDeclaration"


@dataclass
class Ast:
    id: int
    nodes: list
    node_type: NodeType
    src: str


@dataclass
class SourceFile:
    id: int
    ast: dict

    def preorder(self, node):
        if node is None:
            return
        self.preorder(node.left)
        self.preorder(node.right)
        self.process(node)

    def inorder(self, node):
        if node is None:
            return
        self.inorder(node.left)
        self.process(node)
        self.inorder(node.right)

    def postorder(self, node):
        if node is None:
            return
        self.postorder(node.left)
        self.postorder(node.right)
        self.process(node)

    def process(self, node):
        pass


@dataclass
class File:
    source_file: SourceFile
    verison: str
    build_id: str
    profile: str


@dataclass
class BuildInfo:
    id: str
    source_id_to_path: Dict[str, str]
    language: str


@dataclass
class Root:
    sources: Dict[str, List[File]] = field(default_factory=dict)
    errors: List[Errors] = field(default_factory=list)
    build_infos: List[BuildInfo] = field(default_factory=list)
    file_path: Path = Path("")
    position_index: PositionIndex = field(default_factory=PositionIndex)

    def __post_init__(self):
        self._initialize(self.file_path)
        self._build_position_index()

    def search_id(self, id: int):
        for _, files in self.sources.items():
            for file in files:
                s = file.source_file
                if s.id == id:
                    print("Success", s.id)
                else:
                    print("Not found", s.id)
                    continue

    def _initialize(self, file_path):
        data = read_file(file_path)
        _sources = data.get("sources")
        _errors = data.get("errors")
        _build_infos = data.get("build_infos")
        if _sources:
            for filename, files in _sources.items():
                source = []
                for file in files:
                    id, ast, s, f = None, None, None, None
                    version = file.get("version")
                    build_id = file.get("build_id")
                    profile = file.get("profile")
                    s = file.get("source_file")
                    if s:
                        id = s.get("id")
                        ast = s.get("ast")
                        if isinstance(id, int) and ast:
                            s = SourceFile(id, ast)
                        if s and version and build_id and profile:
                            f = File(s, version, build_id, profile)
                        source.append(f)
                self.sources[filename] = source

        if _errors:
            for error in _errors:
                _sourceLocation = error.get("sourceLocation")
                _type = error.get("type")
                _errorCode = error.get("errorCode")
                _message = error.get("message")
                _severity = error.get("severity")

                sourceLocation = None
                error_type = None
                error_code = None
                severity = None
                message = None

                if _sourceLocation:
                    _file = _sourceLocation.get("file")
                    _start = _sourceLocation.get("start")
                    _end = _sourceLocation.get("end")
                    if _file is not None and _start is not None and _end is not None:
                        sourceLocation = SourceLocation(_file, _start, _end)

                if _type is not None:
                    if _type.lower() == "warning":
                        error_type = ErrorType.WARNING
                    elif _type.lower() == "error":
                        error_type = ErrorType.ERROR

                if _errorCode is not None:
                    error_code = _errorCode

                if _severity is not None:
                    if _severity.lower() == "warning":
                        severity = Severity.WARNING
                    elif _severity.lower() == "error":
                        severity = Severity.ERROR

                if _message is not None:
                    message = _message

                if (
                    sourceLocation
                    and error_type
                    and error_code
                    and severity
                    and message
                ):
                    self.errors.append(
                        Errors(
                            sourceLocation, error_type, error_code, severity, message
                        )
                    )
        if _build_infos:
            for info in _build_infos:
                _id = info.get("id")
                _source_map = info.get("source_id_to_path")
                _language = info.get("language")

                if _id and _source_map and _language:
                    self.build_infos.append(
                        BuildInfo(
                            id=_id,
                            source_id_to_path=dict(_source_map),
                            language=_language,
                        )
                    )

    def _build_position_index(self):
        """Build spatial index for all AST nodes"""
        # Build file_id to path mapping from build_infos
        for build_info in self.build_infos:
            for file_id_str, file_path in build_info.source_id_to_path.items():
                try:
                    file_id = int(file_id_str)
                    self.position_index.file_id_to_path[file_id] = file_path
                except ValueError:
                    continue

        # Index all AST nodes
        for file_path, files in self.sources.items():
            for file in files:
                if file and file.source_file:
                    self._index_ast_nodes(file.source_file.ast, file.source_file.id, 0)

        self.position_index.finalize_index()

    def _index_ast_nodes(self, node: dict, file_id: int, depth: int):
        """Recursively index AST nodes"""
        if not isinstance(node, dict):
            return

        # Index current node if it has src and id
        if "src" in node and "id" in node:
            src_info = parse_src(node["src"])
            if src_info:
                start, length, node_file_id = src_info
                node_index = AstNodeIndex(
                    node_id=node["id"],
                    file_id=node_file_id,
                    start_byte=start,
                    end_byte=start + length,
                    node_type=node.get("nodeType", "Unknown"),
                    node_data=node,
                    depth=depth,
                )
                self.position_index.add_node(node_index)

        # Recursively index child nodes
        for key, value in node.items():
            if key in [
                "nodes",
                "body",
                "statements",
                "members",
                "parameters",
                "declarations",
                "symbolAliases",
                "arguments",
                "assignments",
                "baseContracts",
                "modifiers",
            ]:
                if isinstance(value, list):
                    for child in value:
                        self._index_ast_nodes(child, file_id, depth + 1)
            elif key in [
                "expression",
                "leftExpression",
                "leftHandSide",
                "rightExpression",
                "rightHandSide",
                "value",
                "typeName",
                "baseExpression",
                "parameters",
                "baseName",
                "parameterTypes",
                "returnParameterTypes",
            ]:
                if isinstance(value, dict):
                    self._index_ast_nodes(value, file_id, depth + 1)
            elif isinstance(value, dict) and "nodeType" in value:
                self._index_ast_nodes(value, file_id, depth + 1)

    def find_node_at_position(
        self, file_uri: str, line: int, character: int
    ) -> Optional[AstNodeIndex]:
        """Find the innermost AST node at the given LSP position"""
        # Convert URI to file path and find matching file_id
        file_id = None
        for fid, path in self.position_index.file_id_to_path.items():
            if file_uri.endswith(path) or path.endswith(
                file_uri.replace("file://", "")
            ):
                file_id = fid
                break

        if file_id is None:
            return None

        # Read file content to convert position to byte offset
        try:
            file_path = self.position_index.file_id_to_path[file_id]
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            byte_offset = lsp_position_to_byte_offset(content, line, character)
            return self.position_index.find_innermost_node(file_id, byte_offset)
        except (FileNotFoundError, KeyError):
            return None

    def get_declaration_location(
        self, node: AstNodeIndex
    ) -> Optional[Tuple[str, int, int]]:
        """Get the declaration location for a node (file_uri, line, character)"""
        # Look for referencedDeclaration first
        referenced_id = node.node_data.get("referencedDeclaration")
        if referenced_id and referenced_id in self.position_index.node_by_id:
            target_node = self.position_index.node_by_id[referenced_id]
            return self._node_to_location(target_node)

        # Fallback: parse typeIdentifier for struct/enum references
        type_desc = node.node_data.get("typeDescriptions", {})
        type_id = type_desc.get("typeIdentifier", "")

        # Extract node ID from typeIdentifier patterns like "t_struct$_Name_$123_"
        import re

        match = re.search(r"\$(\d+)", type_id)
        if match:
            target_id = int(match.group(1))
            if target_id in self.position_index.node_by_id:
                target_node = self.position_index.node_by_id[target_id]
                return self._node_to_location(target_node)

        return None

    def _node_to_location(self, node: AstNodeIndex) -> Optional[Tuple[str, int, int]]:
        """Convert AST node to LSP location (file_uri, line, character)"""
        if node.file_id not in self.position_index.file_id_to_path:
            return None

        file_path = self.position_index.file_id_to_path[node.file_id]

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            line, character = byte_offset_to_lsp_position(content, node.start_byte)
            file_uri = f"file://{file_path}"
            return (file_uri, line, character)
        except FileNotFoundError:
            return None


def parse_src(src: str) -> Optional[Tuple[int, int, int]]:
    """Parse Solidity AST src format 'start:length:file_id'"""
    try:
        parts = src.split(":")
        if len(parts) != 3:
            return None
        start = int(parts[0])
        length = int(parts[1])
        file_id = int(parts[2])
        return (start, length, file_id)
    except (ValueError, IndexError):
        return None


def lsp_position_to_byte_offset(content: str, line: int, character_utf16: int) -> int:
    """Convert LSP position (line, UTF-16 character) to byte offset"""
    lines = content.split("\n")

    if line >= len(lines):
        return len(content.encode("utf-8"))

    # Get byte offset to start of target line
    line_start_bytes = 0
    for i in range(line):
        if i < len(lines):
            line_start_bytes += len(lines[i].encode("utf-8")) + 1  # +1 for \n

    # Convert UTF-16 character offset to byte offset within the line
    target_line = lines[line]
    utf16_count = 0
    byte_offset_in_line = 0

    for char in target_line:
        if utf16_count >= character_utf16:
            break
        utf16_count += len(char.encode("utf-16le")) // 2  # UTF-16 code units
        byte_offset_in_line += len(char.encode("utf-8"))

    return line_start_bytes + byte_offset_in_line


def byte_offset_to_lsp_position(content: str, byte_offset: int) -> Tuple[int, int]:
    """Convert byte offset to LSP position (line, UTF-16 character)"""
    content_bytes = content.encode("utf-8")

    if byte_offset >= len(content_bytes):
        lines = content.split("\n")
        last_line = lines[-1] if lines else ""
        return (len(lines) - 1, len(last_line.encode("utf-16le")) // 2)

    # Find line containing the byte offset
    lines = content.split("\n")
    current_byte = 0

    for line_num, line in enumerate(lines):
        line_bytes = len(line.encode("utf-8"))

        if current_byte + line_bytes >= byte_offset:
            # Found the line, now find character position
            byte_in_line = byte_offset - current_byte
            line_prefix = line.encode("utf-8")[:byte_in_line].decode(
                "utf-8", errors="ignore"
            )
            utf16_char = len(line_prefix.encode("utf-16le")) // 2
            return (line_num, utf16_char)

        current_byte += line_bytes + 1  # +1 for \n

    # Fallback
    return (len(lines) - 1, 0)


def read_file(filename):
    with open(filename, "r") as f:
        data = json.load(f)
    return data
