import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

# 这一步是为了让 Python 能找到 trading_connectors
sys.path.append(os.path.join(os.getcwd(), "connectors/src"))

try:
    from trading_connectors.curveseries.client import CurveSeriesClient
except ImportError as e:
    print(f"导入失败: {e}")
    sys.exit(1)

def main():
    print("--- 开始测试 CurveSeries ---")
    print("⚠️  请确保 CS Desktop 软件已打开！")
    
    client = CurveSeriesClient()
    
    if client.verify_connection():
        # 这里用你示例里的那个 equation
        equation = 'roll_month(Swap_GO_10_EW_2020F.Close,"1")'
        # 或者用个简单的: 'Brent_Crude_Futures_c1.Close'
        
        print(f"\n尝试查询公式: {equation}")
        
        data = client.fetch_history(
            equation, 
            start_date=datetime.now() - timedelta(days=10),
            end_date=datetime.now()
        )
        
        print(f"获取到 {len(data)} 条数据")
        if len(data) > 0:
            print("第一条数据:", data[0])
    else:
        print("连接失败，请检查桌面端。")

if __name__ == "__main__":
    main()