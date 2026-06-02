import numpy as np
import pickle
from sklearn.ensemble import IsolationForest

def train_and_save_model():
    print("Generating simulated API traffic dataset...")
    # Simulate features for an API request:
    # Feature 1: Request Rate (requests per minute)
    # Feature 2: Geographical Distance from last login (km)
    # Feature 3: Time of day (hour)
    # Feature 4: Device Trust Score (0.0 to 1.0)
    
    # 1. Generate "Normal" Traffic (95% of data)
    np.random.seed(42)
    normal_req_rate = np.random.normal(loc=5, scale=2, size=9500)      # 5 req/min
    normal_geo_dist = np.random.exponential(scale=50, size=9500)       # Short distance (staying in same city)
    normal_time = np.random.uniform(8, 22, size=9500)                  # Working hours
    normal_trust = np.random.normal(loc=0.9, scale=0.1, size=9500)     # High trust devices
    
    normal_data = np.column_stack([normal_req_rate, normal_geo_dist, normal_time, normal_trust])
    
    # 2. Generate "Malicious" Traffic / Credential Stuffing (5% of data)
    malicious_req_rate = np.random.normal(loc=150, scale=30, size=500) # 150 req/min (DDoS/Stuffing)
    malicious_geo_dist = np.random.exponential(scale=5000, size=500)   # High distance (VPN/Botnet)
    malicious_time = np.random.uniform(0, 5, size=500)                 # Late night attacks
    malicious_trust = np.random.normal(loc=0.2, scale=0.1, size=500)   # Unknown/Low trust devices
    
    malicious_data = np.column_stack([malicious_req_rate, malicious_geo_dist, malicious_time, malicious_trust])
    
    # Combine dataset
    X_train = np.vstack([normal_data, malicious_data])
    
    print("Training Isolation Forest Anomaly Detection Model...")
    # Contamination=0.05 means we expect ~5% of traffic to be fraudulent/anomalies
    model = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
    model.fit(X_train)
    
    # Save the model
    with open('fraud_model.pkl', 'wb') as f:
        pickle.dump(model, f)
        
    print("Model successfully trained and saved as 'fraud_model.pkl'!")

if __name__ == "__main__":
    train_and_save_model()
