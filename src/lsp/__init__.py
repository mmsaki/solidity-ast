import sys
import json
import threading
import logging
from dataclasses import dataclass
from typing import Optional, List, Union
from .ast import Root
from pathlib import Path

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)


@dataclass
class DocumentUri:
    pass


@dataclass
class ClientInfo:
    name: str
    version: Optional[str] = None


@dataclass
class WorkspaceFolder:
    uri: DocumentUri
    name: str


@dataclass
class TextDocumentClientCapabilities:
    completion: str


@dataclass
class ClientCapabilities:
    textDocument: Optional[TextDocumentClientCapabilities] = None
    workspace: Optional[dict] = None
    experimental: Optional[dict] = None


@dataclass
class InitializeParams:
    processId: Optional[int]
    capabilities: ClientCapabilities
    clientInfo: Optional[ClientInfo] = None
    initializationOptions: Optional[dict] = None
    workspaceFolders: Optional[Union[List[WorkspaceFolder], None]] = None


class JsonRpc:
    def __init__(self):
        self.stdin = sys.stdin
        self.stdout = sys.stdout

    def read_message(self):
        content_length = 0

        while True:
            line = self.stdin.readline()
            if not line:
                return None
            if line.startswith("Content-Length:"):
                content_length = int(line.split(":")[1].strip())
            if line.strip() == "":
                break

        if content_length == 0:
            return None

        content = self.stdin.read(content_length)
        return json.loads(content)

    def send_message(self, message: dict):
        body = json.dumps(message)
        response = f"Content-Length: {len(body)}\r\n\r\n{body}"
        self.stdout.write(response)
        self.stdout.flush()

    def handle_request(self, request: dict):
        method = request.get("method")
        id_ = request.get("id")
        params = request.get("params", {})

        if method == "initialize":
            logging.debug(f"Received initialize with params: {params}")
            result = {"jsonrpc": "2.0", "id": id_, "result": {"capabilities": {}}}
            self.send_message(result)
        else:
            logging.warning(f"Unknown method: {method}")
            error = {
                "jsonrpc": "2.0",
                "id": id_,
                "error": {"code": -32002, "message": f"Method '{method}' not found"},
            }
            self.send_message(error)


class LspServer:
    def __init__(self):
        self.rpc = JsonRpc()

    def start(self):
        while True:
            message = self.rpc.read_message()
            if message is None:
                break
            threading.Thread(target=self.rpc.handle_request, args=(message,)).start()


class Node:
    pass


def main():
    # LspServer().start()
    root = Root(file_path=Path("test/c.forge.ast.json"))

    node = root.find_node_at_position(
        "file:///Users/meek/Developer/lsp/C.sol", line=10, character=10
    )

    if node:
        print(f"Found {node.node_type} at depth {node.depth}")

        location = root.get_declaration_location(node)
        if location:
            file_uri, line, character = location
            print(f"Declaration at {file_uri}:{line}:{character}")


if __name__ == "__main__":
    main()
