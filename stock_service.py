# # # # stock_service.py
# # # from fastapi import FastAPI, HTTPException
# # # from fastapi.middleware.cors import CORSMiddleware
# # # from pydantic import BaseModel
# # # from typing import List, Dict, Optional
# # # import yfinance as yf
# # # import asyncio
# # # from datetime import datetime, timedelta
# # # import logging

# # # # Configure logging
# # # logging.basicConfig(level=logging.INFO)
# # # logger = logging.getLogger(__name__)

# # # app = FastAPI(title="Indian Stock Market API", version="1.0.0")

# # # # CORS middleware for Next.js integration
# # # app.add_middleware(
# # #     CORSMiddleware,
# # #     allow_origins=["http://localhost:3000"],  # Next.js dev server
# # #     allow_credentials=True,
# # #     allow_methods=["*"],
# # #     allow_headers=["*"],
# # # )

# # # # Pydantic models
# # # class StockSymbol(BaseModel):
# # #     symbol: str
# # #     exchange: str = "NS"  # Default to NSE

# # # class StockPrice(BaseModel):
# # #     symbol: str
# # #     current_price: float
# # #     previous_close: float
# # #     change: float
# # #     change_percent: float
# # #     volume: int
# # #     market_cap: Optional[float] = None
# # #     last_updated: datetime

# # # class StockRequest(BaseModel):
# # #     symbols: List[str]

# # # class ErrorResponse(BaseModel):
# # #     error: str
# # #     message: str
# # #     symbol: Optional[str] = None

# # # # Helper function to format Indian stock symbols
# # # def format_indian_symbol(symbol: str, exchange: str = "NS") -> str:
# # #     """
# # #     Format symbol for Indian exchanges
# # #     NS = NSE, BO = BSE
# # #     """
# # #     symbol = symbol.upper().strip()
# # #     if not symbol.endswith(('.NS', '.BO')):
# # #         symbol = f"{symbol}.{exchange}"
# # #     return symbol

# # # # Helper function to get stock data
# # # async def get_stock_data(symbol: str) -> Dict:
# # #     """
# # #     Fetch real-time stock data using yfinance
# # #     """
# # #     try:
# # #         formatted_symbol = format_indian_symbol(symbol)
# # #         logger.info(f"Fetching data for {formatted_symbol}")
        
# # #         stock = yf.Ticker(formatted_symbol)
        
# # #         # Get current price and basic info
# # #         info = stock.info
# # #         hist = stock.history(period="2d")
        
# # #         if hist.empty:
# # #             raise ValueError(f"No data found for symbol {formatted_symbol}")
        
# # #         current_price = hist['Close'].iloc[-1]
# # #         previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
        
# # #         change = current_price - previous_close
# # #         change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
        
# # #         return {
# # #             "symbol": formatted_symbol,
# # #             "current_price": round(current_price, 2),
# # #             "previous_close": round(previous_close, 2),
# # #             "change": round(change, 2),
# # #             "change_percent": round(change_percent, 2),
# # #             "volume": int(hist['Volume'].iloc[-1]),
# # #             "market_cap": info.get('marketCap'),
# # #             "last_updated": datetime.now(),
# # #             "success": True
# # #         }
        
# # #     except Exception as e:
# # #         logger.error(f"Error fetching data for {symbol}: {str(e)}")
# # #         return {
# # #             "symbol": symbol,
# # #             "error": "FETCH_ERROR",
# # #             "message": str(e),
# # #             "success": False
# # #         }

# # # @app.get("/")
# # # async def root():
# # #     return {"message": "Indian Stock Market API", "status": "running"}

# # # @app.get("/health")
# # # async def health_check():
# # #     return {"status": "healthy", "timestamp": datetime.now()}

# # # @app.get("/stock/{symbol}")
# # # async def get_single_stock(symbol: str, exchange: str = "NS"):
# # #     """
# # #     Get real-time data for a single stock
# # #     """
# # #     try:
# # #         data = await get_stock_data(symbol)
        
# # #         if not data["success"]:
# # #             raise HTTPException(
# # #                 status_code=404, 
# # #                 detail=ErrorResponse(
# # #                     error=data["error"],
# # #                     message=data["message"],
# # #                     symbol=symbol
# # #                 ).dict()
# # #             )
        
# # #         return StockPrice(**data)
        
# # #     except HTTPException:
# # #         raise
# # #     except Exception as e:
# # #         logger.error(f"Unexpected error for {symbol}: {str(e)}")
# # #         raise HTTPException(
# # #             status_code=500,
# # #             detail=ErrorResponse(
# # #                 error="INTERNAL_ERROR",
# # #                 message="Internal server error occurred",
# # #                 symbol=symbol
# # #             ).dict()
# # #         )

# # # @app.post("/stocks/batch")
# # # async def get_multiple_stocks(request: StockRequest):
# # #     """
# # #     Get real-time data for multiple stocks
# # #     """
# # #     try:
# # #         if not request.symbols:
# # #             raise HTTPException(
# # #                 status_code=400,
# # #                 detail=ErrorResponse(
# # #                     error="INVALID_REQUEST",
# # #                     message="Symbols list cannot be empty"
# # #                 ).dict()
# # #             )
        
# # #         if len(request.symbols) > 50:  # Limit batch size
# # #             raise HTTPException(
# # #                 status_code=400,
# # #                 detail=ErrorResponse(
# # #                     error="BATCH_SIZE_EXCEEDED",
# # #                     message="Maximum 50 symbols allowed per request"
# # #                 ).dict()
# # #             )
        
# # #         # Fetch all stocks concurrently
# # #         tasks = [get_stock_data(symbol) for symbol in request.symbols]
# # #         results = await asyncio.gather(*tasks)
        
# # #         successful_stocks = []
# # #         failed_stocks = []
        
# # #         for result in results:
# # #             if result["success"]:
# # #                 successful_stocks.append(StockPrice(**result))
# # #             else:
# # #                 failed_stocks.append(ErrorResponse(
# # #                     error=result["error"],
# # #                     message=result["message"],
# # #                     symbol=result["symbol"]
# # #                 ))
        
# # #         return {
# # #             "successful_stocks": successful_stocks,
# # #             "failed_stocks": failed_stocks,
# # #             "total_requested": len(request.symbols),
# # #             "successful_count": len(successful_stocks),
# # #             "failed_count": len(failed_stocks)
# # #         }
        
# # #     except HTTPException:
# # #         raise
# # #     except Exception as e:
# # #         logger.error(f"Batch request error: {str(e)}")
# # #         raise HTTPException(
# # #             status_code=500,
# # #             detail=ErrorResponse(
# # #                 error="BATCH_ERROR",
# # #                 message="Error processing batch request"
# # #             ).dict()
# # #         )

# # # @app.get("/stocks/popular")
# # # async def get_popular_indian_stocks():
# # #     """
# # #     Get data for popular Indian stocks
# # #     """
# # #     popular_symbols = [
# # #         "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
# # #         "ICICIBANK", "KOTAKBANK", "BHARTIARTL", "ITC", "SBIN"
# # #     ]
    
# # #     request = StockRequest(symbols=popular_symbols)
# # #     return await get_multiple_stocks(request)

# # # if __name__ == "__main__":
# # #     import uvicorn
# # #     uvicorn.run(app, host="0.0.0.0", port=8000)


# # # stock_service.py
# # from fastapi import FastAPI, HTTPException
# # from fastapi.middleware.cors import CORSMiddleware
# # from pydantic import BaseModel
# # from typing import List, Dict, Optional
# # import yfinance as yf
# # import asyncio
# # from datetime import datetime, timedelta
# # import logging
# # import os

# # # Configure logging
# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger(__name__)

# # app = FastAPI(title="Indian Stock Market API", version="1.0.0")

# # # Environment detection
# # IS_PRODUCTION = os.environ.get("RENDER") or os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT")
# # IS_DEVELOPMENT = not IS_PRODUCTION

# # # CORS configuration - Works for both local and production
# # def get_cors_origins():
# #     base_origins = [
# #         "http://localhost:3000",  # Local Next.js dev
# #         "http://127.0.0.1:3000",  # Alternative local
# #         "https://stock-app-eta-sable.vercel.app",  # Your deployed app
# #     ]
    
# #     if IS_DEVELOPMENT:
# #         # In development, be more permissive
# #         base_origins.extend([
# #             "http://localhost:3001",  # Alternative ports
# #             "http://localhost:3002",
# #             "http://localhost:8080",
# #         ])
# #         logger.info("Running in DEVELOPMENT mode")
# #     else:
# #         # In production, add Vercel preview URLs
# #         base_origins.extend([
# #             "https://stock-app-*.vercel.app",  # Vercel preview deployments
# #             "https://stock-app-eta-sable-*.vercel.app",  # Branch deployments
# #         ])
# #         logger.info("Running in PRODUCTION mode")
    
# #     return base_origins

# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=get_cors_origins(),
# #     allow_credentials=True,
# #     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
# #     allow_headers=["*"],
# #     allow_origin_regex=r"https://stock-app-.*\.vercel\.app" if IS_PRODUCTION else None,
# # )

# # # Pydantic models
# # class StockSymbol(BaseModel):
# #     symbol: str
# #     exchange: str = "NS"  # Default to NSE

# # class StockPrice(BaseModel):
# #     symbol: str
# #     current_price: float
# #     previous_close: float
# #     change: float
# #     change_percent: float
# #     volume: int
# #     market_cap: Optional[float] = None
# #     last_updated: datetime

# # class StockRequest(BaseModel):
# #     symbols: List[str]

# # class ErrorResponse(BaseModel):
# #     error: str
# #     message: str
# #     symbol: Optional[str] = None

# # # Helper function to format Indian stock symbols
# # def format_indian_symbol(symbol: str, exchange: str = "NS") -> str:
# #     """
# #     Format symbol for Indian exchanges
# #     NS = NSE, BO = BSE
# #     """
# #     symbol = symbol.upper().strip()
# #     if not symbol.endswith(('.NS', '.BO')):
# #         symbol = f"{symbol}.{exchange}"
# #     return symbol

# # # Helper function to get stock data
# # async def get_stock_data(symbol: str) -> Dict:
# #     """
# #     Fetch real-time stock data using yfinance
# #     """
# #     try:
# #         formatted_symbol = format_indian_symbol(symbol)
# #         logger.info(f"Fetching data for {formatted_symbol}")
        
# #         stock = yf.Ticker(formatted_symbol)
        
# #         # Get current price and basic info
# #         info = stock.info
# #         hist = stock.history(period="2d")
        
# #         if hist.empty:
# #             raise ValueError(f"No data found for symbol {formatted_symbol}")
        
# #         current_price = hist['Close'].iloc[-1]
# #         previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
        
# #         change = current_price - previous_close
# #         change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
        
# #         return {
# #             "symbol": formatted_symbol,
# #             "current_price": round(current_price, 2),
# #             "previous_close": round(previous_close, 2),
# #             "change": round(change, 2),
# #             "change_percent": round(change_percent, 2),
# #             "volume": int(hist['Volume'].iloc[-1]),
# #             "market_cap": info.get('marketCap'),
# #             "last_updated": datetime.now(),
# #             "success": True
# #         }
        
# #     except Exception as e:
# #         logger.error(f"Error fetching data for {symbol}: {str(e)}")
# #         return {
# #             "symbol": symbol,
# #             "error": "FETCH_ERROR",
# #             "message": str(e),
# #             "success": False
# #         }

# # @app.get("/")
# # async def root():
# #     return {
# #         "message": "Indian Stock Market API", 
# #         "status": "running",
# #         "environment": "production" if IS_PRODUCTION else "development",
# #         "version": "1.0.0"
# #     }

# # @app.get("/health")
# # async def health_check():
# #     return {
# #         "status": "healthy", 
# #         "timestamp": datetime.now(),
# #         "environment": "production" if IS_PRODUCTION else "development"
# #     }

# # @app.get("/stock/{symbol}")
# # async def get_single_stock(symbol: str, exchange: str = "NS"):
# #     """
# #     Get real-time data for a single stock
# #     """
# #     try:
# #         data = await get_stock_data(symbol)
        
# #         if not data["success"]:
# #             raise HTTPException(
# #                 status_code=404, 
# #                 detail=ErrorResponse(
# #                     error=data["error"],
# #                     message=data["message"],
# #                     symbol=symbol
# #                 ).dict()
# #             )
        
# #         return StockPrice(**data)
        
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Unexpected error for {symbol}: {str(e)}")
# #         raise HTTPException(
# #             status_code=500,
# #             detail=ErrorResponse(
# #                 error="INTERNAL_ERROR",
# #                 message="Internal server error occurred",
# #                 symbol=symbol
# #             ).dict()
# #         )

# # @app.post("/stocks/batch")
# # async def get_multiple_stocks(request: StockRequest):
# #     """
# #     Get real-time data for multiple stocks
# #     """
# #     try:
# #         if not request.symbols:
# #             raise HTTPException(
# #                 status_code=400,
# #                 detail=ErrorResponse(
# #                     error="INVALID_REQUEST",
# #                     message="Symbols list cannot be empty"
# #                 ).dict()
# #             )
        
# #         if len(request.symbols) > 50:  # Limit batch size
# #             raise HTTPException(
# #                 status_code=400,
# #                 detail=ErrorResponse(
# #                     error="BATCH_SIZE_EXCEEDED",
# #                     message="Maximum 50 symbols allowed per request"
# #                 ).dict()
# #             )
        
# #         # Fetch all stocks concurrently
# #         tasks = [get_stock_data(symbol) for symbol in request.symbols]
# #         results = await asyncio.gather(*tasks)
        
# #         successful_stocks = []
# #         failed_stocks = []
        
# #         for result in results:
# #             if result["success"]:
# #                 successful_stocks.append(StockPrice(**result))
# #             else:
# #                 failed_stocks.append(ErrorResponse(
# #                     error=result["error"],
# #                     message=result["message"],
# #                     symbol=result["symbol"]
# #                 ))
        
# #         return {
# #             "successful_stocks": successful_stocks,
# #             "failed_stocks": failed_stocks,
# #             "total_requested": len(request.symbols),
# #             "successful_count": len(successful_stocks),
# #             "failed_count": len(failed_stocks)
# #         }
        
# #     except HTTPException:
# #         raise
# #     except Exception as e:
# #         logger.error(f"Batch request error: {str(e)}")
# #         raise HTTPException(
# #             status_code=500,
# #             detail=ErrorResponse(
# #                 error="BATCH_ERROR",
# #                 message="Error processing batch request"
# #             ).dict()
# #         )

# # @app.get("/stocks/popular")
# # async def get_popular_indian_stocks():
# #     """
# #     Get data for popular Indian stocks
# #     """
# #     popular_symbols = [
# #         "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
# #         "ICICIBANK", "KOTAKBANK", "BHARTIARTL", "ITC", "SBIN"
# #     ]
    
# #     request = StockRequest(symbols=popular_symbols)
# #     return await get_multiple_stocks(request)

# # # Startup event
# # @app.on_event("startup")
# # async def startup_event():
# #     logger.info(f"🚀 Indian Stock API starting up...")
# #     logger.info(f"📍 Environment: {'Production' if IS_PRODUCTION else 'Development'}")
# #     logger.info(f"🌐 CORS Origins: {get_cors_origins()}")

# # # Works for both local development and production
# # if __name__ == "__main__":
# #     import uvicorn
    
# #     # Port configuration
# #     port = int(os.environ.get("PORT", 8000))
# #     host = "0.0.0.0" if IS_PRODUCTION else "127.0.0.1"
    
# #     logger.info(f"Starting server on {host}:{port}")
    
# #     uvicorn.run(
# #         app, 
# #         host=host, 
# #         port=port,
# #         # reload=IS_DEVELOPMENT,  # Enable auto-reload in development
# #         log_level="info"
# #     )


# # stock_service.py
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List, Dict, Optional
# import yfinance as yf
# import asyncio
# from datetime import datetime, timedelta
# import logging
# import os

# # Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI(title="Indian Stock Market API", version="1.0.0")

# # Environment detection
# IS_PRODUCTION = os.environ.get("RENDER") or os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT")
# IS_DEVELOPMENT = not IS_PRODUCTION

# # CORS configuration - FIXED VERSION
# def get_cors_origins():
#     # Base origins that should always be allowed
#     base_origins = [
#         "http://localhost:3000",  # Local Next.js dev
#         "http://127.0.0.1:3000",  # Alternative local
#         "https://stock-app-eta-sable.vercel.app",  # Your deployed app
#     ]
    
#     if IS_DEVELOPMENT:
#         # In development, be more permissive
#         base_origins.extend([
#             "http://localhost:3001",  # Alternative ports
#             "http://localhost:3002",
#             "http://localhost:8080",
#         ])
#         logger.info("Running in DEVELOPMENT mode")
#     else:
#         logger.info("Running in PRODUCTION mode")
    
#     return base_origins

# # FIXED CORS MIDDLEWARE CONFIGURATION
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins in production to fix immediate issue
#     allow_credentials=False,  # Set to False when using allow_origins=["*"]
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=["*"],
#     expose_headers=["*"],
# )

# # Alternative more restrictive CORS (comment above and uncomment below if you want stricter control)
# """
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=get_cors_origins(),
#     allow_credentials=True,
#     allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
#     allow_headers=[
#         "Accept",
#         "Accept-Language",
#         "Content-Language",
#         "Content-Type",
#         "Authorization",
#         "X-Requested-With",
#     ],
#     expose_headers=["*"],
# )
# """

# # Pydantic models
# class StockSymbol(BaseModel):
#     symbol: str
#     exchange: str = "NS"  # Default to NSE

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

# # Helper function to format Indian stock symbols
# def format_indian_symbol(symbol: str, exchange: str = "NS") -> str:
#     """
#     Format symbol for Indian exchanges
#     NS = NSE, BO = BSE
#     """
#     symbol = symbol.upper().strip()
#     if not symbol.endswith(('.NS', '.BO')):
#         symbol = f"{symbol}.{exchange}"
#     return symbol

# # Helper function to get stock data
# async def get_stock_data(symbol: str) -> Dict:
#     """
#     Fetch real-time stock data using yfinance
#     """
#     try:
#         formatted_symbol = format_indian_symbol(symbol)
#         logger.info(f"Fetching data for {formatted_symbol}")
        
#         stock = yf.Ticker(formatted_symbol)
        
#         # Get current price and basic info
#         info = stock.info
#         hist = stock.history(period="2d")
        
#         if hist.empty:
#             raise ValueError(f"No data found for symbol {formatted_symbol}")
        
#         current_price = hist['Close'].iloc[-1]
#         previous_close = info.get('previousClose', hist['Close'].iloc[-2] if len(hist) > 1 else current_price)
        
#         change = current_price - previous_close
#         change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
        
#         return {
#             "symbol": formatted_symbol,
#             "current_price": round(current_price, 2),
#             "previous_close": round(previous_close, 2),
#             "change": round(change, 2),
#             "change_percent": round(change_percent, 2),
#             "volume": int(hist['Volume'].iloc[-1]),
#             "market_cap": info.get('marketCap'),
#             "last_updated": datetime.now(),
#             "success": True
#         }
        
#     except Exception as e:
#         logger.error(f"Error fetching data for {symbol}: {str(e)}")
#         return {
#             "symbol": symbol,
#             "error": "FETCH_ERROR",
#             "message": str(e),
#             "success": False
#         }

# # Add explicit OPTIONS handler for CORS preflight
# @app.options("/{path:path}")
# async def options_handler(path: str):
#     return {"message": "OK"}

# @app.get("/")
# async def root():
#     return {
#         "message": "Indian Stock Market API", 
#         "status": "running",
#         "environment": "production" if IS_PRODUCTION else "development",
#         "version": "1.0.0",
#         "cors_origins": get_cors_origins()
#     }

# @app.get("/health")
# async def health_check():
#     return {
#         "status": "healthy", 
#         "timestamp": datetime.now(),
#         "environment": "production" if IS_PRODUCTION else "development"
#     }

# @app.get("/stock/{symbol}")
# async def get_single_stock(symbol: str, exchange: str = "NS"):
#     """
#     Get real-time data for a single stock
#     """
#     try:
#         data = await get_stock_data(symbol)
        
#         if not data["success"]:
#             raise HTTPException(
#                 status_code=404, 
#                 detail=ErrorResponse(
#                     error=data["error"],
#                     message=data["message"],
#                     symbol=symbol
#                 ).dict()
#             )
        
#         return StockPrice(**data)
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Unexpected error for {symbol}: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=ErrorResponse(
#                 error="INTERNAL_ERROR",
#                 message="Internal server error occurred",
#                 symbol=symbol
#             ).dict()
#         )

# @app.post("/stocks/batch")
# async def get_multiple_stocks(request: StockRequest):
#     """
#     Get real-time data for multiple stocks
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
        
#         if len(request.symbols) > 50:  # Limit batch size
#             raise HTTPException(
#                 status_code=400,
#                 detail=ErrorResponse(
#                     error="BATCH_SIZE_EXCEEDED",
#                     message="Maximum 50 symbols allowed per request"
#                 ).dict()
#             )
        
#         # Fetch all stocks concurrently
#         tasks = [get_stock_data(symbol) for symbol in request.symbols]
#         results = await asyncio.gather(*tasks)
        
#         successful_stocks = []
#         failed_stocks = []
        
#         for result in results:
#             if result["success"]:
#                 successful_stocks.append(StockPrice(**result))
#             else:
#                 failed_stocks.append(ErrorResponse(
#                     error=result["error"],
#                     message=result["message"],
#                     symbol=result["symbol"]
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
#     Get data for popular Indian stocks
#     """
#     popular_symbols = [
#         "RELIANCE", "TCS", "HDFCBANK", "INFY", "HINDUNILVR",
#         "ICICIBANK", "KOTAKBANK", "BHARTIARTL", "ITC", "SBIN"
#     ]
    
#     request = StockRequest(symbols=popular_symbols)
#     return await get_multiple_stocks(request)

# # Startup event
# @app.on_event("startup")
# async def startup_event():
#     logger.info(f"🚀 Indian Stock API starting up...")
#     logger.info(f"📍 Environment: {'Production' if IS_PRODUCTION else 'Development'}")
#     logger.info(f"🌐 CORS Origins: {get_cors_origins()}")

# # Works for both local development and production
# if __name__ == "__main__":
#     import uvicorn
    
#     # Port configuration
#     port = int(os.environ.get("PORT", 8000))
#     host = "0.0.0.0" if IS_PRODUCTION else "127.0.0.1"
    
#     logger.info(f"Starting server on {host}:{port}")
    
#     uvicorn.run(
#         app, 
#         host=host, 
#         port=port,
#         # reload=IS_DEVELOPMENT,  # Enable auto-reload in development
#         log_level="info"
#     )


# stock_service.py - Enhanced version with rate limiting and caching
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import yfinance as yf
import asyncio
from datetime import datetime, timedelta
import logging
import os
import time
from collections import defaultdict
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Indian Stock Market API", version="2.0.0")

# Environment detection
IS_PRODUCTION = os.environ.get("RENDER") or os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PORT")
IS_DEVELOPMENT = not IS_PRODUCTION

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Pydantic models (same as before)
class StockSymbol(BaseModel):
    symbol: str
    exchange: str = "NS"

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

# ===== RATE LIMITING & CACHING SYSTEM =====

class RateLimiter:
    def __init__(self, max_requests: int = 5, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = defaultdict(list)
    
    def can_make_request(self, identifier: str = "global") -> bool:
        now = time.time()
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] 
            if now - req_time < self.time_window
        ]
        
        # Check if we can make a new request
        return len(self.requests[identifier]) < self.max_requests
    
    def record_request(self, identifier: str = "global"):
        self.requests[identifier].append(time.time())
    
    def get_wait_time(self, identifier: str = "global") -> float:
        if self.can_make_request(identifier):
            return 0
        
        now = time.time()
        oldest_request = min(self.requests[identifier])
        return max(0, self.time_window - (now - oldest_request))

class StockDataCache:
    def __init__(self, default_ttl: int = 300):  # 5 minutes default
        self.cache = {}
        self.default_ttl = default_ttl
    
    def get(self, symbol: str) -> Optional[Dict]:
        if symbol in self.cache:
            data, expiry = self.cache[symbol]
            if datetime.now() < expiry:
                return data
            else:
                del self.cache[symbol]
        return None
    
    def set(self, symbol: str, data: Dict, ttl: Optional[int] = None):
        ttl = ttl or self.default_ttl
        expiry = datetime.now() + timedelta(seconds=ttl)
        self.cache[symbol] = (data, expiry)
    
    def clear_expired(self):
        now = datetime.now()
        expired_keys = [
            key for key, (_, expiry) in self.cache.items()
            if now >= expiry
        ]
        for key in expired_keys:
            del self.cache[key]

# Initialize rate limiter and cache
rate_limiter = RateLimiter(max_requests=3, time_window=60)  # 3 requests per minute
stock_cache = StockDataCache(default_ttl=300)  # 5-minute cache

# Helper function to format Indian stock symbols
def format_indian_symbol(symbol: str, exchange: str = "NS") -> str:
    symbol = symbol.upper().strip()
    if not symbol.endswith(('.NS', '.BO')):
        symbol = f"{symbol}.{exchange}"
    return symbol

# Enhanced stock data fetching with rate limiting and retry logic
async def get_stock_data_with_retry(symbol: str, max_retries: int = 3) -> Dict:
    """
    Fetch stock data with rate limiting, caching, and retry logic
    """
    formatted_symbol = format_indian_symbol(symbol)
    
    # Check cache first
    cached_data = stock_cache.get(formatted_symbol)
    if cached_data:
        logger.info(f"Cache hit for {formatted_symbol}")
        return {**cached_data, "from_cache": True}
    
    # Check rate limit
    if not rate_limiter.can_make_request():
        wait_time = rate_limiter.get_wait_time()
        logger.warning(f"Rate limit hit, waiting {wait_time:.1f} seconds")
        await asyncio.sleep(wait_time + random.uniform(1, 3))  # Add jitter
    
    for attempt in range(max_retries):
        try:
            # Record the request
            rate_limiter.record_request()
            
            logger.info(f"Fetching data for {formatted_symbol} (attempt {attempt + 1})")
            
            # Create ticker with session reuse
            stock = yf.Ticker(formatted_symbol)
            
            # Try to get data using history first (more reliable)
            hist = stock.history(period="5d", interval="1d")
            
            if hist.empty:
                raise ValueError(f"No historical data found for {formatted_symbol}")
            
            # Get the latest data
            current_price = hist['Close'].iloc[-1]
            previous_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
            volume = int(hist['Volume'].iloc[-1]) if not hist['Volume'].empty else 0
            
            # Calculate changes
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100 if previous_close != 0 else 0
            
            # Try to get additional info (optional)
            market_cap = None
            try:
                info = stock.info
                market_cap = info.get('marketCap')
            except Exception as e:
                logger.warning(f"Could not fetch info for {formatted_symbol}: {e}")
            
            stock_data = {
                "symbol": formatted_symbol,
                "current_price": round(float(current_price), 2),
                "previous_close": round(float(previous_close), 2),
                "change": round(float(change), 2),
                "change_percent": round(float(change_percent), 2),
                "volume": volume,
                "market_cap": market_cap,
                "last_updated": datetime.now(),
                "success": True,
                "from_cache": False
            }
            
            # Cache the successful result
            stock_cache.set(formatted_symbol, stock_data, ttl=300)  # 5-minute cache
            
            return stock_data
            
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed for {symbol}: {str(e)}")
            
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.info(f"Retrying in {wait_time:.1f} seconds...")
                await asyncio.sleep(wait_time)
            else:
                # Final attempt failed
                return {
                    "symbol": symbol,
                    "error": "FETCH_ERROR_AFTER_RETRIES",
                    "message": f"Failed after {max_retries} attempts: {str(e)}",
                    "success": False
                }

# Batch processing with staggered requests
async def get_stock_data_batch_staggered(symbols: List[str]) -> List[Dict]:
    """
    Process multiple stocks with staggered timing to avoid rate limits
    """
    results = []
    
    for i, symbol in enumerate(symbols):
        # Add delay between requests (except for the first one)
        if i > 0:
            delay = random.uniform(2, 4)  # 2-4 second delay between requests
            logger.info(f"Waiting {delay:.1f}s before fetching {symbol}")
            await asyncio.sleep(delay)
        
        result = await get_stock_data_with_retry(symbol)
        results.append(result)
        
        # Clear expired cache entries periodically
        if i % 5 == 0:
            stock_cache.clear_expired()
    
    return results

# Updated API endpoints
@app.options("/{path:path}")
async def options_handler(path: str):
    return {"message": "OK"}

@app.get("/")
async def root():
    return {
        "message": "Enhanced Indian Stock Market API", 
        "status": "running",
        "environment": "production" if IS_PRODUCTION else "development",
        "version": "2.0.0",
        "features": ["rate_limiting", "caching", "retry_logic"],
        "cache_size": len(stock_cache.cache)
    }

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "environment": "production" if IS_PRODUCTION else "development",
        "cache_entries": len(stock_cache.cache),
        "rate_limiter_status": "available" if rate_limiter.can_make_request() else "limited"
    }

@app.get("/stock/{symbol}")
async def get_single_stock(symbol: str, exchange: str = "NS"):
    """
    Get real-time data for a single stock with enhanced error handling
    """
    try:
        data = await get_stock_data_with_retry(symbol)
        
        if not data["success"]:
            raise HTTPException(
                status_code=429 if "rate" in data["error"].lower() else 404,
                detail=ErrorResponse(
                    error=data["error"],
                    message=data["message"],
                    symbol=symbol
                ).dict()
            )
        
        return StockPrice(**{k: v for k, v in data.items() if k not in ["success", "from_cache"]})
        
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
    Get real-time data for multiple stocks with staggered requests
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
        
        if len(request.symbols) > 20:  # Reduced batch size
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="BATCH_SIZE_EXCEEDED",
                    message="Maximum 20 symbols allowed per request (reduced for rate limiting)"
                ).dict()
            )
        
        # Use staggered processing instead of concurrent
        results = await get_stock_data_batch_staggered(request.symbols)
        
        successful_stocks = []
        failed_stocks = []
        
        for result in results:
            if result["success"]:
                stock_data = {k: v for k, v in result.items() if k not in ["success", "from_cache"]}
                successful_stocks.append(StockPrice(**stock_data))
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
            "failed_count": len(failed_stocks),
            "processing_time": "staggered_to_avoid_rate_limits"
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
    Get data for popular Indian stocks (reduced list for rate limiting)
    """
    # Reduced to 5 most popular stocks to avoid rate limits
    popular_symbols = ["RELIANCE", "TCS", "HDFCBANK", "INFY", "ICICIBANK"]
    
    request = StockRequest(symbols=popular_symbols)
    return await get_multiple_stocks(request)

@app.get("/cache/stats")
async def get_cache_stats():
    """
    Get cache statistics for debugging
    """
    stock_cache.clear_expired()
    return {
        "cache_size": len(stock_cache.cache),
        "cached_symbols": list(stock_cache.cache.keys()),
        "rate_limiter_available": rate_limiter.can_make_request(),
        "next_available_in": rate_limiter.get_wait_time()
    }

@app.post("/cache/clear")
async def clear_cache():
    """
    Clear the cache (useful for development)
    """
    stock_cache.cache.clear()
    return {"message": "Cache cleared", "cache_size": 0}

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info(f"🚀 Enhanced Indian Stock API starting up...")
    logger.info(f"📍 Environment: {'Production' if IS_PRODUCTION else 'Development'}")
    logger.info(f"⚡ Features: Rate Limiting, Caching, Retry Logic")
    logger.info(f"🔄 Rate Limit: {rate_limiter.max_requests} requests per {rate_limiter.time_window}s")
    logger.info(f"💾 Cache TTL: {stock_cache.default_ttl}s")

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.environ.get("PORT", 8000))
    host = "0.0.0.0" if IS_PRODUCTION else "127.0.0.1"
    
    logger.info(f"Starting enhanced server on {host}:{port}")
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        log_level="info"
    )