# BTC AI Prediction API

A FastAPI-based Bitcoin price prediction service using machine learning and CoinGecko API data.

## Features

- **Real-time BTC Data**: Fetches historical BTC data from CoinGecko API (no geo-restrictions)
- **ML Model**: Uses Random Forest regression for price prediction
- **Technical Indicators**: Includes RSI, moving averages, and other features
- **Auto-training**: Automatically trains model on startup if not available
- **REST API**: Clean endpoints for predictions and health checks

## Installation

```bash
pip install -r requirements.txt
```

## Running Locally

```bash
python main.py
```

The API will be available at `http://0.0.0.0:8080`

## API Endpoints

### GET `/`
Root endpoint with API information

### GET `/health`
Health check endpoint

### POST `/predict`
Predict BTC price
- Body: `{"hours": 24}` (optional, defaults to 24)
- Returns: Current price, predicted price, change percentage, and confidence score

### POST `/retrain`
Manually trigger model retraining with fresh data

## Deployment (Railway)

1. Create a new Railway project
2. Link this repository
3. Railway will automatically detect the Python project
4. Set environment variables if needed
5. Deploy!

## Key Improvements over Binance API

- **No Geo-restrictions**: CoinGecko API works globally
- **No API Key Required**: Free tier available
- **Reliable Data**: Consistent data availability
- **Better Error Handling**: Graceful fallbacks

## Model Details

- **Algorithm**: Random Forest Regressor
- **Features**: Returns, moving averages (7, 24, 48), standard deviation, RSI, price lags
- **Training Data**: 30 days of hourly BTC price data
- **Model Persistence**: Saved as `model.pkl` and `scaler.pkl`
