import asyncio
import httpx
import random
import time

API_URL = "http://127.0.0.1:8000/api/v1/transaction"

async def simulate_normal_user(client, user_id):
    # Simulate a legitimate user making a transaction
    data = {
        "user_id": f"user_{user_id}",
        "amount": round(random.uniform(10.0, 500.0), 2),
        "ip_address": f"192.168.1.{user_id}",
        "geo_distance_km": random.uniform(0.1, 50.0),  # Close to home
        "time_of_day_hour": random.uniform(8.0, 22.0), # Daytime
        "device_trust_score": random.uniform(0.8, 1.0) # High trust
    }
    
    try:
        response = await client.post(API_URL, json=data)
        print(f"Normal User {user_id}: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

async def simulate_fraud_attack(client):
    # Simulate a credential stuffing / bot attack from a single IP
    attacker_ip = f"10.0.{random.randint(1,255)}.{random.randint(1,255)}"
    print(f"\n--- 🚨 INITIATING BOT ATTACK FROM {attacker_ip} ---\n")
    
    for i in range(15): # Try to hit the API rapidly
        data = {
            "user_id": f"victim_{random.randint(1000, 9999)}",
            "amount": round(random.uniform(500.0, 5000.0), 2),
            "ip_address": attacker_ip,
            "geo_distance_km": random.uniform(1000.0, 5000.0), # Far away (VPN)
            "time_of_day_hour": random.uniform(1.0, 4.0),      # Middle of night
            "device_trust_score": random.uniform(0.0, 0.3)     # Low trust
        }
        
        try:
            response = await client.post(API_URL, json=data)
            print(f"Attacker {attacker_ip} Attempt {i+1}: {response.status_code}")
            if response.status_code == 403:
                # WAF has kicked in and blocked the IP
                print(f"🔒 WAF successfully blocked attacker IP {attacker_ip}!")
        except Exception as e:
            pass
            
        await asyncio.sleep(0.1) # Super fast requests to trigger rate limiting / ML anomaly

async def main():
    async with httpx.AsyncClient() as client:
        print("Starting API Traffic Simulation...")
        
        while True:
            # 1. Simulate 5 normal users
            tasks = []
            for i in range(5):
                tasks.append(simulate_normal_user(client, random.randint(1, 100)))
            
            await asyncio.gather(*tasks)
            
            # 2. Randomly trigger a massive fraud attack (20% chance per cycle)
            if random.random() < 0.20:
                await simulate_fraud_attack(client)
                
            await asyncio.sleep(2.0)

if __name__ == "__main__":
    asyncio.run(main())
