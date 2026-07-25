from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import logging
from contextlib import asynccontextmanager
import json
from datetime import datetime

from app.api.routes import router
from app.api.websocket import ConnectionManager
from app.core.anomaly_detector import AnomalyDetector
from app.core.model_manager import ModelManager
from app.data.generator import DataGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global instances
anomaly_detector = None
model_manager = None
data_generator = None
manager = ConnectionManager()

# Background task flag
generator_running = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global anomaly_detector, model_manager, data_generator, generator_running
    
    # Startup
    logger.info("🚀 Starting up ThreatGuard...")
    
    try:
        # Initialize components
        model_manager = ModelManager()
        data_generator = DataGenerator()
        anomaly_detector = AnomalyDetector(model_manager)
        
        # Load or train initial model
        await model_manager.initialize()
        logger.info("✅ Models initialized successfully")
        
        # Start background data generation
        generator_running = True
        asyncio.create_task(generate_synthetic_data())
        logger.info("✅ Data generator started")
        
    except Exception as e:
        logger.error(f"❌ Startup error: {e}")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down...")
    generator_running = False

# Create FastAPI app
app = FastAPI(
    title="ThreatGuard AI - Anomaly Detection System",
    description="AI/ML based behavioral anomaly detection for cyber threats",
    version="3.0.1",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix="/api")

# ==================== WEBSOCKET ====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            data = await websocket.receive_text()
            
            # Process any incoming data if needed
            if data:
                try:
                    log_data = json.loads(data)
                    if anomaly_detector:
                        result = await anomaly_detector.process_real_time(data)
                        await manager.send_personal_message(json.dumps(result), websocket)
                except:
                    pass
                    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        logger.info(f"WebSocket disconnected. Active connections: {len(manager.active_connections)}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

# ==================== BACKGROUND TASKS ====================
async def generate_synthetic_data():
    """Background task to generate synthetic access logs"""
    global generator_running, anomaly_detector, data_generator
    
    batch_count = 0
    anomaly_count = 0
    total_logs = 0
    
    logger.info("🔄 Starting synthetic data generation...")
    
    while generator_running:
        try:
            # Generate a batch of logs (100 logs per batch)
            logs = data_generator.generate_batch(100, anomaly_rate=0.05)
            batch_count += 1
            total_logs += len(logs)
            
            # Process each log through the anomaly detector
            for log in logs:
                try:
                    result = await anomaly_detector.process_log(log)
                    if result.get('status') == 'anomaly':
                        anomaly_count += 1
                        # Broadcast alert to all connected WebSocket clients
                        await manager.broadcast_alert(result)
                except Exception as e:
                    logger.error(f"Error processing log: {e}")
            
            # Log progress every 10 batches
            if batch_count % 10 == 0:
                logger.info(f"📊 Generated {total_logs} logs, detected {anomaly_count} anomalies")
            
            # Wait 5 seconds before next batch
            await asyncio.sleep(5)
            
        except Exception as e:
            logger.error(f"❌ Data generation error: {e}")
            await asyncio.sleep(10)

# ==================== HEALTH CHECK (Additional) ====================
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "ThreatGuard AI - Anomaly Detection System",
        "version": "3.0.1",
        "status": "running",
        "docs": "/docs",
        "api": "/api"
    }

@app.get("/api/status")
async def system_status():
    """Get system status"""
    return {
        "status": "online",
        "timestamp": datetime.now().isoformat(),
        "models_loaded": model_manager.is_initialized if model_manager else False,
        "generator_running": generator_running,
        "websocket_connections": len(manager.active_connections)
    }

# ==================== RUN ====================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )