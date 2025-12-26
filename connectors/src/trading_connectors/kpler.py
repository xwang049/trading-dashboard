import os
import requests
from datetime import datetime
from trading_core.models import StandardDataPacket

class KplerClient:
    # Kpler API 基础地址 (这里以 Inventory 为例，具体看你需要哪个 Endpoint)
    BASE_URL = "https://api.kpler.com/v1"

    def __init__(self, token: str = None):
        self.token = token or os.getenv("KPLER_TOKEN")
        
        # ---> 新增这几行调试代码 <---
        if self.token:
            print(f"DEBUG: Token 已加载，长度: {len(self.token)}")
            print(f"DEBUG: Token 前5位: {self.token[:5]}...") # 看看是不是 UWZYM
        else:
            print("DEBUG: ❌ 严重错误！Token 是空的！")
        # ---------------------------

        self.headers = {
            "Authorization": f"Basic {self.token}",
            "Accept": "application/json"
        }

    def fetch_inventory(self, product: str = "crude") -> list[StandardDataPacket]:
        """
        抓取库存数据，并清洗为标准格式
        """
        # 这是一个示例 Endpoint，用于获取库存
        # 如果你想看具体的（比如新加坡 Fuel Oil），我们需要查文档加参数
        url = f"{self.BASE_URL}/inventories"
        
        print(f"正在请求 Kpler API: {url} ...")
        
        try:
            # 发送请求
            # 注意：实际使用时可能需要加 params (如 zones, products, startDate)
            # 这里先裸跑一次看看连通性
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status() # 如果返回 401/403/500 会直接报错
            
            data = response.json()
            
            # --- 数据清洗 (Normalization) ---
            # 假设 Kpler 返回的数据里包含 date 和 value
            # 注意：真实的 Kpler 返回结构比较复杂，我们需要根据返回结果调整这里的解析逻辑
            # 下面是根据 Kpler 一般结构写的伪代码解析
            results = []
            
            # 如果 Kpler 返回的是一个列表
            raw_list = data.get('data', []) if isinstance(data, dict) else data
            
            for item in raw_list:
                packet = StandardDataPacket(
                    source="kpler",
                    ticker=f"{product}_inventory",
                    timestamp=datetime.strptime(item.get('date'), "%Y-%m-%d"), # 需根据实际格式调整
                    value=float(item.get('value', 0)),
                    unit="bbl", # 假设单位，需核实
                    raw_data=item,
                    metadata={"product": product}
                )
                results.append(packet)
                
            return results

        except Exception as e:
            print(f"Kpler 请求失败: {e}")
            # 如果失败，我们返回空列表，或者也可以选择抛出异常
            return []

    def verify_connection(self):
        """简单测试 Token 是否有效"""
        url = f"{self.BASE_URL}/status" # 或者是其他轻量级 endpoint
        # 既然我们不知道具体哪个 endpoint 最轻，可以直接尝试拿 trades 或 inventories
        # 如果返回 200 就说明 Token 没问题
        try:
            # 随便请求一个 users/me 或者 status 接口
            # Kpler 通常没有 status 接口，我们用 inventories 试探
            response = requests.get(f"{self.BASE_URL}/inventories", headers=self.headers, params={"size": 1})
            if response.status_code == 200:
                print("✅ Kpler 连接成功！Token 有效。")
                return True
            else:
                print(f"❌ 连接拒绝: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ 连接错误: {e}")
            return False