from __future__ import annotations

import asyncio
import serial_asyncio
import array

from abc import ABC, abstractmethod
from typing import List

class AresFrame(object):
    def __init__(self) -> None:
        self.cmd = 0
        self.size = 0
        self.idx = 0
        self.sidx = 0
        self.type = 0
        self.data = 0

    @classmethod
    def make_byte_stream(cls, data_list):
        data_array = array.array('B',data_list)
        #data_array = array.array('B',[0x01,0x2, 0x16,0x00, 0x00, 0x01, 0x01, 0x02, 0x03, 0x04])
        octets = bytes(data_array)

        return octets

    def update_from_byte_stream(self, data):
        self.cmd = data[0]
        self.size = data[1]
        self.idx = data[2:4]
        self.sidx = data[4]
        self.type = data[5]
        self.data = data[6:10]

class SerialProtocol(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self.queue = asyncio.Queue()
        self.lock = asyncio.Lock()

    def connection_made(self, transport):
        self.transport = transport
        print('Connection made')

    def data_received(self, data):
        print(f'Data received: {data}')

    async def send_data(self, data):
        async with self.lock:
            await self.queue.put(data)

    async def process_queue(self):
        while True:
            if not self.queue.empty():
                async with self.lock:
                    data = await self.queue.get()
                if self.transport:
                    self.transport.write(data)
                    print(f'Sent data: {data}')
                else:
                    print("Connection not established")
            await asyncio.sleep(0.1)

    def connection_lost(self, exc):
        print('Connection lost')
        asyncio.get_event_loop().stop()

async def external_event(proto):
    send_data = [0x01,0x2, 0x16,0x00, 0x00, 0x01, 0x01, 0x02, 0x03, 0x04]
    octets = AresFrame.make_byte_stream(send_data)
    await proto.send_data(octets)

async def main(loop, port):
    serial_coro = serial_asyncio.create_serial_connection(loop, SerialProtocol, port, baudrate=115200)
    proto, _ = await serial_coro
    await asyncio.gather(proto.process_queue(), external_event(proto))

if __name__ == '__main__':
    port = 'COM3'  # 시리얼 포트 설정

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main(loop, port))
    finally:
        loop.close()