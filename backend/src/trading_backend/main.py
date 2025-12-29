from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime, timedelta
from trading_core.models import StandardDataPacket

# 只引入 CurveSeries
try:
    from trading_connectors.curveseries.client import CurveSeriesClient
    cs_client = CurveSeriesClient()
    print("✅ CurveSeries 客户端已加载")
except Exception as e:
    print(f"⚠️ CurveSeries 加载失败: {e}")
    cs_client = None

app = FastAPI(title="Trading Dashboard API (CurveSeries Only)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许任何来源 (开发环境方便，生产环境可以改成 ["http://localhost:5500"])
    allow_credentials=True,
    allow_methods=["*"],  # 允许 GET, POST 等所有方法
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "ok", "source": "CurveSeries"}

@app.get("/api/curveseries/history", response_model=List[StandardDataPacket])
def get_curveseries_data(
    equation: str = Query(..., description="CurveSeries 公式"),
    days: int = Query(30, description="过去多少天")
):
    if not cs_client:
        raise HTTPException(status_code=503, detail="服务未就绪")

    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    return cs_client.fetch_history(equation, start_date, end_date)