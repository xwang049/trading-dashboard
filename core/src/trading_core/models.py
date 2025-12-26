from datetime import datetime
from typing import Any, Optional, Dict
from pydantic import BaseModel

class StandardDataPacket(BaseModel):
    """
    全系统通用的数据标准。
    所有 Connector 抓回来的数据，必须清洗成这个样子才能进入系统。
    """
    source: str           # 数据源，例如 "kpler", "reuters"
    ticker: str           # 标识符，例如 "crude_oil_inventory_sg"
    timestamp: datetime   # 数据对应的时间
    value: float          # 核心数值
    unit: str             # 单位，例如 "bbl", "mt"
    
    # 原始数据保留一份，万一以后要查错
    raw_data: Any         
    
    # 额外的标签，方便以后做筛选 (e.g., {"region": "Singapore", "grade": "Fuel Oil"})
    metadata: Dict[str, Any] = {}