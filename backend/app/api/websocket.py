from fastapi import WebSocket
from typing import List
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected: {len(self.active_connections)} connections")
    
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected: {len(self.active_connections)} connections")
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                self.disconnect(connection)
    
    async def broadcast_alert(self, alert: dict):
        """Broadcast alert to all connected clients"""
        await self.broadcast(json.dumps({
            'type': 'alert',
            'data': alert
        }))
    
    async def broadcast_stats(self, stats: dict):
        """Broadcast stats update to all connected clients"""
        await self.broadcast(json.dumps({
            'type': 'stats',
            'data': stats
        }))