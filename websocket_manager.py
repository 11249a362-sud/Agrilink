from fastapi import WebSocket
from collections import defaultdict

class ConnectionManager:
    def __init__(self):
        self.active_connections = defaultdict(list)

    async def connect(self, auction_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[auction_id].append(websocket)

    def disconnect(self, auction_id: int, websocket: WebSocket):
        if websocket in self.active_connections[auction_id]:
            self.active_connections[auction_id].remove(websocket)

    async def broadcast(self, auction_id: int, message: dict):
        for connection in self.active_connections[auction_id]:
            await connection.send_json(message)

manager = ConnectionManager()