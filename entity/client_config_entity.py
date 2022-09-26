from typing import List

from typing_extensions import TypedDict


class _ServerEntity(TypedDict):
    port: int
    host: str

    https: bool
    password: str


class _ClientEntity(TypedDict):
    name: str
    remote_port: int
    local_port: int
    local_ip: str


class ClientConfigEntity(TypedDict):
    server: _ServerEntity
    client: List[_ClientEntity]