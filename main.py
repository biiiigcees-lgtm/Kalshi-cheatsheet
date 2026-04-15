import os
import logging
import pickle
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import MinMaxScaler
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("btc-ai")

app = FastAPI()

# Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
MODEL_PATH = "model.pkl"
SCALER_PATH = "scaler.pkl"

class PredictionRequest(BaseModel):
    hours: int = 24

class PredictionResponse(BaseModel):
    current_price: float
    predicted_price: float
    change_percent: float
    confidence: float

def fetch_btc_data(days=30):
    """Fetch BTC historical data from CoinGecko API"""
    try:
        logger.info(f"Fetching {days} days of BTC data from CoinGecko...")
        url = f"{COINGECKO_API_URL}/coins/bitcoin/market_chart"
        params = {
            "vs_currency": "usd",
            "days": days,
            "interval": "hourly" if days <= 30 else "daily"
        }
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        prices = data["prices"]
        
        # Convert to DataFrame
        df = pd.DataFrame(prices, columns=["timestamp", "price"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)
        
        logger.info(f"Successfully fetched {len(df)} data points")
        return df
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch BTC data: {str(e)}")

def prepare_features(df):
    """Prepare features for ML model"""
    df = df.copy()
    
    # Technical indicators
    df["returns"] = df["price"].pct_change()
    df["ma_7"] = df["price"].rolling(window=7).mean()
    df["ma_24"] = df["price"].rolling(window=24).mean()
    df["ma_48"] = df["price"].rolling(window=48).mean()
    df["std_24"] = df["price"].rolling(window=24).std()
    df["rsi"] = calculate_rsi(df["price"], window=14)
    
    # Lag features
    df["price_lag_1"] = df["price"].shift(1)
    df["price_lag_2"] = df["price"].shift(2)
    df["price_lag_3"] = df["price"].shift(3)
    
    # Drop NaN values
    df.dropna(inplace=True)
    
    return df

def calculate_rsi(prices, window=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def train_model(df):
    """Train ML model on BTC data"""
    try:
        logger.info("Training ML model...")
        
        # Prepare features
        df_features = prepare_features(df)
        
        # Define features and target
        feature_cols = ["returns", "ma_7", "ma_24", "ma_48", "std_24", "rsi", 
                       "price_lag_1", "price_lag_2", "price_lag_3"]
        X = df_features[feature_cols].values
        y = df_features["price"].values
        
        # Scale features
        scaler = MinMaxScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Train model
        model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_scaled, y)
        
        # Save model and scaler
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model, f)
        with open(SCALER_PATH, "wb") as f:
            pickle.dump(scaler, f)
        
        logger.info("Model training completed and saved")
        return model, scaler, feature_cols
    
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise

def load_model():
    """Load trained model and scaler"""
    try:
        if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
            with open(MODEL_PATH, "rb") as f:
                model = pickle.load(f)
            with open(SCALER_PATH, "rb") as f:
                scaler = pickle.load(f)
            logger.info("Loaded existing model")
            return model, scaler
        return None, None
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None, None

def predict_price(model, scaler, df, feature_cols, hours=24):
    """Predict future BTC price"""
    try:
        # Get latest data point
        df_features = prepare_features(df)
        latest = df_features[feature_cols].iloc[-1].values.reshape(1, -1)
        
        # Scale
        latest_scaled = scaler.transform(latest)
        
        # Predict
        predicted = model.predict(latest_scaled)[0]
        current = df["price"].iloc[-1]
        
        change_percent = ((predicted - current) / current) * 100
        confidence = model.score(scaler.transform(df_features[feature_cols].values), 
                                df_features["price"].values)
        
        return {
            "current_price": current,
            "predicted_price": predicted,
            "change_percent": change_percent,
            "confidence": abs(confidence)
        }
    
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise

@app.on_event("startup")
async def startup_event():
    """Initialize model on startup"""
    model, scaler = load_model()
    
    if model is None:
        logger.info("No model.pkl found — auto-training now...")
        try:
            df = fetch_btc_data(days=30)
            train_model(df)
        except Exception as e:
            logger.error(f"Auto-train failed: {e}")
    else:
        logger.info("Model loaded successfully")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Predict BTC price"""
    try:
        # Load model
        model, scaler = load_model()
        if model is None:
            raise HTTPException(status_code=503, detail="Model not available")
        
        # Fetch latest data
        df = fetch_btc_data(days=30)
        
        # Feature columns (must match training)
        feature_cols = ["returns", "ma_7", "ma_24", "ma_48", "std_24", "rsi", 
                       "price_lag_1", "price_lag_2", "price_lag_3"]
        
        # Predict
        prediction = predict_price(model, scaler, df, feature_cols, request.hours)
        
        return PredictionResponse(**prediction)
    
    except Exception as e:
        logger.error(f"Prediction endpoint error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/retrain")
async def retrain():
    """Retrain the model with fresh data"""
    try:
        logger.info("Manual retrain requested...")
        df = fetch_btc_data(days=30)
        model, scaler, _ = train_model(df)
        return {"status": "success", "message": "Model retrained successfully"}
    except Exception as e:
        logger.error(f"Retrain failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "BTC AI Prediction API",
        "endpoints": {
            "/health": "Health check",
            "/predict": "Predict BTC price (POST)",
            "/retrain": "Retrain model (POST)"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
