# core/base_connector.py
from abc import ABC, abstractmethod
from datetime import datetime
from pydantic import BaseModel

# 1. 定义一个全公司通用的标准数据格式
class StandardDataPacket(BaseModel):
    source_name: str       # e.g., "kpler", "reuters"
    data_type: str         # e.g., "inventory", "news", "price"
    timestamp: datetime
    raw_content: dict      # 原始数据存一份
    normalized_value: float | str | None  # 提取出的核心值
    tags: list[str]        # e.g., ["crude", "sg_market"]

# 2. 定义连接器模板
class BaseConnector(ABC):
    def __init__(self, config):
        self.config = config

    @abstractmethod
    def connect(self):
        """建立连接 (登录/鉴权)"""
        pass

    @abstractmethod
    def fetch_latest(self) -> list[StandardDataPacket]:
        """抓取数据，并必须返回 StandardDataPacket 列表"""
        pass