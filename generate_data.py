import asyncio
import sys
sys.path.append('backend')

from app.data.generator import DataGenerator
from app.core.anomaly_detector import AnomalyDetector
from app.core.model_manager import ModelManager

async def generate():
    print("🚀 Generating data...")
    
    # Initialize
    model_manager = ModelManager()
    await model_manager.initialize()
    
    detector = AnomalyDetector(model_manager)
    generator = DataGenerator()
    
    # Generate 200 logs with anomalies
    logs = generator.generate_batch(200, anomaly_rate=0.15)
    
    print(f"📊 Generated {len(logs)} logs")
    
    # Process each log
    count = 0
    for log in logs:
        result = await detector.process_log(log)
        if result.get('status') == 'anomaly':
            count += 1
            print(f"⚠️ Alert {count}: {result.get('threat_type')} - Score: {result.get('risk_score')}")
    
    print(f"✅ Done! Processed {len(logs)} logs, detected {count} anomalies")
    return count

asyncio.run(generate())