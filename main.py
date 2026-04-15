import os
import logging
import pickle
import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("btc-ai")

# Configuration
COINGECKO_API_URL = "https://api.coingecko.com/api/v3"
MODEL_PATH = "model.pkl"
PORT = int(os.getenv("PORT", 8080))

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events"""
    # Startup
    model_params = load_model()
    
    if model_params is None:
        logger.info("No model.pkl found — auto-training now...")
        try:
            df = fetch_btc_data(days=30)
            train_model(df)
        except Exception as e:
            logger.error(f"Auto-train failed: {e}")
    else:
        logger.info("Model loaded successfully")
    
    yield
    
    # Shutdown
    logger.info("Application shutting down")

app = FastAPI(lifespan=lifespan)

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

def train_model(df):
    """Train simple statistical model on BTC data"""
    try:
        logger.info("Training statistical model...")
        
        # Calculate simple statistical indicators
        recent_data = df.tail(24)  # Last 24 hours
        
        # Calculate moving averages
        ma_short = recent_data["price"].rolling(window=7).mean().iloc[-1]
        ma_long = recent_data["price"].rolling(window=24).mean().iloc[-1]
        
        # Calculate momentum
        momentum = (recent_data["price"].iloc[-1] - recent_data["price"].iloc[-24]) / recent_data["price"].iloc[-24]
        
        # Calculate volatility
        volatility = recent_data["price"].pct_change().std()
        
        # Save model parameters
        model_params = {
            "ma_short": ma_short,
            "ma_long": ma_long,
            "momentum": momentum,
            "volatility": volatility,
            "last_price": df["price"].iloc[-1],
            "timestamp": datetime.now().isoformat()
        }
        
        with open(MODEL_PATH, "wb") as f:
            pickle.dump(model_params, f)
        
        logger.info("Model training completed and saved")
        return model_params
    
    except Exception as e:
        logger.error(f"Model training failed: {e}")
        raise

def load_model():
    """Load trained statistical model"""
    try:
        if os.path.exists(MODEL_PATH):
            with open(MODEL_PATH, "rb") as f:
                model_params = pickle.load(f)
            logger.info("Loaded existing model")
            return model_params
        return None
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return None

def predict_price(model_params, df, hours=24):
    """Predict future BTC price using statistical indicators"""
    try:
        # Get current price
        current = df["price"].iloc[-1]
        
        # Calculate prediction based on momentum and moving averages
        # If short MA > long MA, trend is up
        trend_signal = 1 if model_params["ma_short"] > model_params["ma_long"] else -1
        
        # Predict based on momentum and trend
        momentum_factor = model_params["momentum"] * 24  # Scale to 24 hours
        trend_factor = trend_signal * (model_params["volatility"] * 2)
        
        predicted = current * (1 + momentum_factor + trend_factor)
        
        # Calculate confidence based on how close current price is to moving averages
        ma_diff = abs(model_params["ma_short"] - model_params["ma_long"]) / model_params["ma_long"]
        confidence = max(0.5, min(0.95, 1 - ma_diff))
        
        change_percent = ((predicted - current) / current) * 100
        
        return {
            "current_price": current,
            "predicted_price": predicted,
            "change_percent": change_percent,
            "confidence": confidence
        }
    
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/predict", response_model=PredictionResponse)
async def predict(request: PredictionRequest):
    """Predict BTC price"""
    try:
        # Load model
        model_params = load_model()
        if model_params is None:
            raise HTTPException(status_code=503, detail="Model not available")
        
        # Fetch latest data
        df = fetch_btc_data(days=30)
        
        # Predict
        prediction = predict_price(model_params, df, request.hours)
        
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
        train_model(df)
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
    uvicorn.run(app, host="0.0.0.0", port=PORT)
