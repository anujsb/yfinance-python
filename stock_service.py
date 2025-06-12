# stock_service.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import yfinance as yf
import asyncio
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Indian Stock Market API", version="1.0.0")

# CORS middleware for Next.js integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class StockSymbol(BaseModel):
    symbol: str
    exchange: str = "NS"  # Default to NSE

class StockPrice(BaseModel):
    symbol: str
    current_price: float
    previous_close: float
    change: float
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    last_updated: datetime

class StockRequest(BaseModel):
    symbols: List[str]

class ErrorResponse(BaseModel):
    error: str
    message: str
    symbol: Optional[str] = None

# Helper function to format Indian stock symbols
def format_indian_symbol(symbol: str, exchange: str = "NS") -> str:
    """
    Format symbol for Indian exchanges
    NS = NSE, BO = BSE
    """
    symbol = symbol.upper().strip()
    if not symbol.endswith(('.NS', '.BO')):
        symbol = f"{symbol}.{exchange}"
    return symbol

# Helper function to get stock data
async def get_stock_data(symbol: str) -> Dict:
    """
    Fetch real-time stock data using yfinance
    """
    try:
        formatted_symbol = format_indian_symbol(symbol)
        logger.info(f"Fetching data for {formatted_symbol}")
        
        stock = yf.Ticker(formatted_symbol)
        
        # Get current price and basic info
        info = stock.info
        hist = stock.history(period="2d")
        
        if hist.empty:
            raise ValueError(f"No data found for symbol {formatted_symbol}")
        
        current_price = hist['Close'].iloc[-1]
        previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
        
        change = current_price - previous_close
        change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
        
        return {
            "symbol": formatted_symbol,
            "current_price": round(current_price, 2),
            "previous_close": round(previous_close, 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "volume": int(hist['Volume'].iloc[-1]),
            "market_cap": info.get('marketCap'),
            "last_updated": datetime.now(),
            "success": True
        }
        
    except Exception as e:
        logger.error(f"Error fetching data for {symbol}: {str(e)}")
        return {
            "symbol": symbol,
            "error": "FETCH_ERROR",
            "message": str(e),
            "success": False
        }

@app.get("/")
async def root():
    return {"message": "Indian Stock Market API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

@app.get("/stock/{symbol}")
async def get_single_stock(symbol: str, exchange: str = "NS"):
    """
    Get real-time data for a single stock
    """
    try:
        data = await get_stock_data(symbol)
        
        if not data["success"]:
            raise HTTPException(
                status_code=404, 
                detail=ErrorResponse(
                    error=data["error"],
                    message=data["message"],
                    symbol=symbol
                ).dict()
            )
        
        return StockPrice(**data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error for {symbol}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="INTERNAL_ERROR",
                message="Internal server error occurred",
                symbol=symbol
            ).dict()
        )

@app.post("/stocks/batch")
async def get_multiple_stocks(request: StockRequest):
    """
    Get real-time data for multiple stocks
    """
    try:
        if not request.symbols:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="INVALID_REQUEST",
                    message="Symbols list cannot be empty"
                ).dict()
            )
        
        if len(request.symbols) > 50:  # Limit batch size
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="BATCH_SIZE_EXCEEDED",
                    message="Maximum 50 symbols allowed per request"
                ).dict()
            )
        
        # Fetch all stocks concurrently
        tasks = [get_stock_data(symbol) for symbol in request.symbols]
        results = await asyncio.gather(*tasks)
        
        successful_stocks = []
        failed_stocks = []
        
        for result in results:
            if result["success"]:
                successful_stocks.append(StockPrice(**result))
            else:
                failed_stocks.append(ErrorResponse(
                    error=result["error"],
                    message=result["message"],
                    symbol=result["symbol"]
                ))
        
        return {
            "successful_stocks": successful_stocks,
            "failed_stocks": failed_stocks,
            "total_requested": len(request.symbols),
            "successful_count": len(successful_stocks),
            "failed_count": len(failed_stocks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch request error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="BATCH_ERROR",
                message="Error processing batch request"
            ).dict()
        )

@app.get("/stocks/popular")
async def get_popular_indian_stocks():
    """
    Get data for popular Indian stocks
    """
    popular_symbols = [
        "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
        "ICICIBANK", "KOTAKBANK", "BHARTIARTL", "ITC", "SBIN"
    ]
    
    request = StockRequest(symbols=popular_symbols)
    return await get_multiple_stocks(request)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)












# # test_stock_service.py - Simple version for testing
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List, Dict, Optional
# from datetime import datetime
# import logging

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Indian Stock Market API Test", version="1.0.0")

# # CORS middleware for Next.js integration
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins for testing
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Pydantic models
# class StockPrice(BaseModel):
#     symbol: str
#     current_price: float
#     previous_close: float
#     change: float
#     change_percent: float
#     volume: int
#     market_cap: Optional[float] = None
#     last_updated: datetime

# class StockRequest(BaseModel):
#     symbols: List[str]

# class ErrorResponse(BaseModel):
#     error: str
#     message: str
#     symbol: Optional[str] = None

# @app.get("/")
# async def root():
#     return {"message": "Indian Stock Market API Test", "status": "running"}

# @app.get("/health")
# async def health_check():
#     return {"status": "healthy", "timestamp": datetime.now()}

# @app.get("/stock/{symbol}")
# async def get_single_stock(symbol: str, exchange: str = "NS"):
#     """
#     Get mock data for a single stock for testing
#     """
#     try:
#         logger.info(f"Fetching mock data for {symbol}")
        
#         # Mock data for testing
#         mock_data = {
#             "symbol": f"{symbol.upper()}.{exchange}",
#             "current_price": 2450.75,
#             "previous_close": 2420.50,
#             "change": 30.25,
#             "change_percent": 1.25,
#             "volume": 1250000,
#             "market_cap": 1500000000000,
#             "last_updated": datetime.now()
#         }
        
#         return StockPrice(**mock_data)
        
#     except Exception as e:
#         logger.error(f"Error fetching data for {symbol}: {str(e)}")
#         raise HTTPException(
#             status_code=404, 
#             detail=ErrorResponse(
#                 error="FETCH_ERROR",
#                 message=str(e),
#                 symbol=symbol
#             ).dict()
#         )

# @app.post("/stocks/batch")
# async def get_multiple_stocks(request: StockRequest):
#     """
#     Get mock data for multiple stocks
#     """
#     try:
#         if not request.symbols:
#             raise HTTPException(
#                 status_code=400,
#                 detail=ErrorResponse(
#                     error="INVALID_REQUEST",
#                     message="Symbols list cannot be empty"
#                 ).dict()
#             )
        
#         successful_stocks = []
#         failed_stocks = []
        
#         for symbol in request.symbols:
#             try:
#                 mock_data = {
#                     "symbol": f"{symbol.upper()}.NS",
#                     "current_price": 2450.75,
#                     "previous_close": 2420.50,
#                     "change": 30.25,
#                     "change_percent": 1.25,
#                     "volume": 1250000,
#                     "market_cap": 1500000000000,
#                     "last_updated": datetime.now()
#                 }
#                 successful_stocks.append(StockPrice(**mock_data))
#             except Exception as e:
#                 failed_stocks.append(ErrorResponse(
#                     error="FETCH_ERROR",
#                     message=str(e),
#                     symbol=symbol
#                 ))
        
#         return {
#             "successful_stocks": successful_stocks,
#             "failed_stocks": failed_stocks,
#             "total_requested": len(request.symbols),
#             "successful_count": len(successful_stocks),
#             "failed_count": len(failed_stocks)
#         }
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Batch request error: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=ErrorResponse(
#                 error="BATCH_ERROR",
#                 message="Error processing batch request"
#             ).dict()
#         )

# @app.get("/stocks/popular")
# async def get_popular_indian_stocks():
#     """
#     Get mock data for popular Indian stocks
#     """
#     popular_symbols = [
#         "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR"
#     ]
    
#     request = StockRequest(symbols=popular_symbols)
#     return await get_multiple_stocks(request)

# if __name__ == "__main__":
#     import uvicorn
#     print("Starting test stock service on http://localhost:8000")
#     print("Available endpoints:")
#     print("- GET /health")
#     print("- GET /stock/RELIANCE")
#     print("- POST /stocks/batch")
#     print("- GET /stocks/popular")
#     uvicorn.run(app, host="0.0.0.0", port=8000)