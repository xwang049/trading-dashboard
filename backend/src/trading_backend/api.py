from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

# 引入我们的核心标准
from trading_core.models import StandardDataPacket

# 引入连接器
# 注意：这里我们用 try-except，防止万一某个连接器坏了导致整个服务起不来
try:
    from trading_connectors.curveseries.client import CurveSeriesClient
    cs_client = CurveSeriesClient()
    print("✅ CurveSeries 客户端已加载")
except Exception as e:
    print(f"⚠️ CurveSeries 加载失败: {e}")
    cs_client = None

# 初始化 FastAPI
app = FastAPI(
    title="Trading Dashboard API",
    description="统一数据接口：整合 CurveSeries, Kpler 等数据源",
    version="0.1.0"
)

# --- 首页测试 ---
@app.get("/")
def read_root():
    return {"status": "ok", "message": "Trading Dashboard Backend is Running!"}

# --- CurveSeries 接口 ---
@app.get("/api/curveseries/history", response_model=List[StandardDataPacket])
def get_curveseries_data(
    equation: str = Query(..., description="CurveSeries 公式，例如 Brent_Crude_Futures_c1.Close"),
    days: int = Query(30, description="获取过去多少天的数据")
):
    """
    前端通过这个接口，直接从 CurveSeries 桌面端拿数据
    """
    if not cs_client:
        raise HTTPException(status_code=503, detail="CurveSeries 服务不可用 (可能是桌面端未运行)")

    # 计算时间范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 验证连接 (可选，为了稳健)
    # if not cs_client.verify_connection():
    #     raise HTTPException(status_code=503, detail="无法连接到 CurveSeries 桌面端")

    # 抓取数据
    data = cs_client.fetch_history(equation, start_date, end_date)
    
    if not data:
        return []
        
    return data

# --- Kpler 接口 (预留) ---
# 等你拿到账号后，把这里取消注释即可
# @app.get("/api/kpler/inventory")
# def get_kpler_inventory(product: str = "crude"):
#     ...