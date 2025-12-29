import sys
import os
import pandas as pd
from datetime import datetime, timedelta
from trading_core.models import StandardDataPacket

# 确保能找到同级目录的 .pyd
current_dir = os.path.dirname(__file__)
if current_dir not in sys.path:
    sys.path.append(current_dir)

try:
    import CSDataAPI
except ImportError:
    from . import CSDataAPI

class CurveSeriesClient:
    def __init__(self):
        # 🟢 核心修复：手动建立月份表，不再依赖系统语言
        self.month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }

    def _format_date(self, date_obj: datetime) -> str:
        if isinstance(date_obj, str): return date_obj
        return date_obj.strftime("%d-%b-%Y")

    def _parse_custom_date(self, date_str: str) -> datetime:
        """
        🟢 强力解析器：强制将 '26-Dec-2025' 拆解并转换，不查系统字典
        """
        try:
            # 1. 清洗掉后面的时间 (e.g. "26-Dec-2025 00:00:00.000" -> "26-Dec-2025")
            clean_str = date_str.split(' ')[0]
            
            # 2. 物理切割
            parts = clean_str.split('-') # ['26', 'Dec', '2025']
            if len(parts) != 3:
                return None
                
            day = int(parts[0])
            month_str = parts[1]
            year = int(parts[2])
            
            # 3. 查表转换
            # 优先查英文表，查不到就试数字
            month = self.month_map.get(month_str)
            if not month:
                month = int(month_str) # 防止已经是数字的情况
                
            return datetime(year, month, day)
        except Exception:
            return None

    def verify_connection(self) -> bool:
        print("正在连接 CurveSeries Desktop...")
        try:
            end = datetime.now()
            start = end - timedelta(days=5)
            CSDataAPI.getCSData('Brent_Crude_Futures_c1.Close', self._format_date(start), self._format_date(end))
            print("✅ CurveSeries 连接通道正常")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def fetch_history(self, equation: str, start_date: datetime = None, end_date: datetime = None) -> list[StandardDataPacket]:
        if not end_date: end_date = datetime.now()
        if not start_date: start_date = end_date - timedelta(days=30)

        s_str = self._format_date(start_date)
        e_str = self._format_date(end_date)
        results = []

        try:
            print(f"正在抓取: {equation} ({s_str} to {e_str})...")
            raw_data = CSDataAPI.getCSData(equation, s_str, e_str)
            
            if not raw_data:
                print(f"⚠️ {equation} 无数据返回")
                return []

            df = pd.DataFrame(raw_data)
            
            for index, row in df.iterrows():
                ts_obj = None
                val = 0.0
                
                for col in df.columns:
                    cell_val = row[col]
                    
                    # 1. 找价格
                    if isinstance(cell_val, (int, float)):
                        val = float(cell_val)
                        continue
                        
                    # 2. 找日期 (只要包含 '-' 就尝试解析)
                    if isinstance(cell_val, str) and not ts_obj:
                        if '-' in cell_val:
                            # 🟢 调用强力解析器
                            ts_obj = self._parse_custom_date(cell_val)

                # ⚠️ 关键：如果这一行解析不出日期，就直接扔掉！
                # 绝对不能用 datetime.now() 填充，否则图表会白屏
                if ts_obj is None:
                    continue

                packet = StandardDataPacket(
                    source="curveseries",
                    ticker=equation,
                    timestamp=ts_obj,
                    value=val,
                    unit="unit",
                    raw_data=row.to_dict(),
                    metadata={}
                )
                results.append(packet)
                
            print(f"✅ 成功提取 {len(results)} 条有效数据")
            return results

        except Exception as e:
            print(f"❌ CS 处理数据错误: {e}")
            return []