from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pickle
import numpy as np
import time
import json
import asyncio
from typing import List

app = FastAPI(
    title="AI-Driven Cloud Security Gateway",
    description="WAF and Fraud Detection Engine using Isolation Forest",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- ML MODEL LOADING ---
print("Loading AI Anomaly Detection Model...")
try:
    with open('fraud_model.pkl', 'rb') as f:
        model = pickle.load(f)
except FileNotFoundError:
    print("Error: fraud_model.pkl not found. Please run train_model.py first.")
    exit(1)

# --- MOCK REDIS FOR STATE MANAGEMENT ---
# In production, use aioredis to connect to a real Redis cluster
class MockRedis:
    def __init__(self):
        self.ip_requests = {} # IP -> [timestamps]
        self.blocked_ips = set()
        
redis_store = MockRedis()

# --- WEBSOCKETS (LIVE DASHBOARD) ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()

# --- MODELS ---
class TransactionRequest(BaseModel):
    user_id: str
    amount: float
    ip_address: str
    geo_distance_km: float
    time_of_day_hour: float
    device_trust_score: float

# --- CLOUD SECURITY WAF & INFERENCE ENDPOINT ---
@app.post("/api/v1/transaction")
async def process_transaction(req: TransactionRequest):
    current_time = time.time()
    
    # 1. WAF Check: Is IP already blocked?
    if req.ip_address in redis_store.blocked_ips:
        await manager.broadcast({
            "status": "BLOCKED_WAF",
            "ip": req.ip_address,
            "reason": "IP previously blacklisted by AI",
            "timestamp": current_time
        })
        raise HTTPException(status_code=403, detail="WAF: IP is permanently banned.")

    # 2. Redis State: Calculate Request Rate (Rolling Window)
    if req.ip_address not in redis_store.ip_requests:
        redis_store.ip_requests[req.ip_address] = []
    
    # Remove timestamps older than 60 seconds
    redis_store.ip_requests[req.ip_address] = [
        t for t in redis_store.ip_requests[req.ip_address] if current_time - t < 60
    ]
    
    redis_store.ip_requests[req.ip_address].append(current_time)
    current_req_rate = len(redis_store.ip_requests[req.ip_address])

    # 3. AI Inference (Anomaly Detection)
    # Features: [req_rate, geo_distance, time_of_day, device_trust]
    features = np.array([[
        current_req_rate,
        req.geo_distance_km,
        req.time_of_day_hour,
        req.device_trust_score
    ]])
    
    # Isolation Forest returns 1 for normal, -1 for anomaly
    prediction = model.predict(features)[0]
    
    # Calculate an "AI Risk Score" based on the decision function (lower is more anomalous)
    anomaly_score = model.decision_function(features)[0]
    risk_percentage = round((0.5 - anomaly_score) * 100, 2)
    risk_percentage = max(0.0, min(100.0, risk_percentage)) # Clamp between 0 and 100

    # 4. Security Action
    is_fraud = prediction == -1
    
    if is_fraud:
        # Auto-ban the IP in Redis
        redis_store.blocked_ips.add(req.ip_address)
        action = "BLOCKED_BY_AI"
        
        # --- NEW: DevOps Slack / Email Alert Integration ---
        # If the risk score is extremely high (>90%), simulate sending an urgent Webhook alert
        if risk_percentage > 90.0:
            trigger_devops_alert(req.ip_address, risk_percentage, current_req_rate)
    else:
        action = "APPROVED"

    # 5. Broadcast to Live Security Dashboard
    event = {
        "user_id": req.user_id,
        "amount": req.amount,
        "ip": req.ip_address,
        "action": action,
        "risk_score": risk_percentage,
        "req_rate": current_req_rate,
        "timestamp": current_time
    }
    
    # Fire and forget the broadcast so it doesn't block the API response
    asyncio.create_task(manager.broadcast(event))
    
    if is_fraud:
        raise HTTPException(status_code=403, detail=f"Transaction blocked by AI. Risk Score: {risk_percentage}%")
        
    return {"status": "success", "transaction_id": f"txn_{int(current_time)}", "risk_score": f"{risk_percentage}%"}

# --- UTILITY: DevOps Alerting ---
def trigger_devops_alert(ip_address: str, risk_score: float, req_rate: int):
    """
    Simulates triggering an external webhook (like Slack or PagerDuty) 
    to alert the DevOps team of a high-risk attack.
    """
    import httpx
    
    slack_webhook_url = "https://hooks.slack.com/services/MOCK/WEBHOOK/URL"
    message = f"🚨 *CRITICAL SECURITY ALERT* 🚨\n" \
              f"AI Anomaly Detected!\n" \
              f"IP Address: `{ip_address}`\n" \
              f"Risk Score: *{risk_score}%*\n" \
              f"Request Rate: {req_rate} req/min\n" \
              f"Action Taken: IP permanently blacklisted at WAF layer."
              
    print("\n" + "="*50)
    print(f"[SLACK WEBHOOK FIRED TO DEVOPS TEAM]")
    print(message)
    print("="*50 + "\n")
    
    # In a real environment, you would run:
    # asyncio.create_task(httpx.AsyncClient().post(slack_webhook_url, json={"text": message}))

@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
