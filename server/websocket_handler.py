import asyncio
import json
import traceback
from asyncio import Lock
from collections import defaultdict
from threading import Thread
from typing import List, Dict, Set

from tornado.ioloop import IOLoop
from tornado.websocket import WebSocketHandler
from tornado_request_mapping import request_mapping

from common.logger_factory import LoggerFactory
from constant.message_type_constnat import MessageTypeConstant
from context.context_utils import ContextUtils
from entity.message.message_entity import MessageEntity
from entity.message.push_config_entity import PushConfigEntity
from entity.message.tcp_over_websocket_message import TcpOverWebsocketMessage
from exceptions.duplicated_name import DuplicatedName
from exceptions.invalid_password import InvalidPassword
from server.tcp_forward_client import TcpForwardClient


@request_mapping("/ws")
class MyWebSocketaHandler(WebSocketHandler):
    name_to_tcp_forward_client: Dict[str, TcpForwardClient] = {}
    handler_to_names: Dict['MyWebSocketaHandler', Set[str]] = defaultdict(set)
    lock = Lock()

    def _check_password(self, request_password: str) -> bool:
        password = ContextUtils.get_password()
        if not password and not request_password:
            return True
        return password == request_password

    def open(self, *args: str, **kwargs: str):
        password = self.get_argument('password', '')
        if not self._check_password(password):
            LoggerFactory.get_logger().error('invalid password')
            self.close(reason='invalid password')
            raise InvalidPassword()
        LoggerFactory.get_logger().info('new open websocket')

    def write_message(self, message, binary=False):
        try:
            return super(MyWebSocketaHandler, self).write_message(message, binary)
        except Exception:
            LoggerFactory.get_logger().error(traceback.format_exc())
            a = 3

    async def on_message(self, message):
        message_dict: MessageEntity = json.loads(message)
        if message_dict['type_'] == MessageTypeConstant.WEBSOCKET_OVER_TCP:
            data: TcpOverWebsocketMessage = message_dict['data']  # socket消息
            name = data['name']
            uid = data['uid']
            self.name_to_tcp_forward_client[name].send_to_socket(uid, bytes.fromhex(data['data']))

        elif message_dict['type_'] == MessageTypeConstant.PUSH_CONFIG:
            async with self.lock:
                LoggerFactory.get_logger().info(f'get push config: {message_dict}')
                data: List[PushConfigEntity] = message_dict['data']  # 配置
                this_name_to_tcp_forward_client = {}
                name_set = set()
                for d in data:
                    if d['name'] in self.name_to_tcp_forward_client:
                        raise DuplicatedName()
                    if d['name'] in name_set:
                        self.close(None, 'DuplicatedName')
                        raise DuplicatedName()
                    client = TcpForwardClient(self, d['name'], d['remote_port'], asyncio.get_event_loop())
                    this_name_to_tcp_forward_client[d['name']] = client
                    name_set.add(d['name'])
                task_list: List[Thread] = []
                for name, client in this_name_to_tcp_forward_client.items():
                    try:
                        client.bind_port()
                    except OSError:
                        for _, client in this_name_to_tcp_forward_client.items():
                            client.close()
                        raise
                    task_list.append(Thread(target=client.start_accept))
                self.name_to_tcp_forward_client.update(this_name_to_tcp_forward_client)
                for name, _ in this_name_to_tcp_forward_client.items():
                    self.handler_to_names[self].add(name)
                for t in task_list:
                    t.start()
    def on_close(self, code: int = None, reason: str = None) -> None:
        asyncio.ensure_future(self._on_close(code, reason))

    async def _on_close(self, code: int = None, reason: str = None) -> None:
        async with self.lock:
            LoggerFactory.get_logger().info('close')
            names = self.handler_to_names[self]
            for name in names:
                try:
                    client = self.name_to_tcp_forward_client.pop(name)
                    client.close()
                except KeyError:
                    pass

    def check_origin(self, origin: str) -> bool:
        return True