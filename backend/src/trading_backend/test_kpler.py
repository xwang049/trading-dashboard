print("DEBUG: 脚本第一行，如果你看到我，说明 Python 活了！")  # <--- 加这行
import sys
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 引入连接器
# 注意：如果这里报错 ModuleNotFoundError，我们需要调整运行方式，但先看能不能打印第一行
try:
    from trading_connectors.kpler import KplerClient
except ImportError as e:
    print(f"DEBUG: 导入失败: {e}")
    print("DEBUG: Python路径是:", sys.path)
    sys.exit(1)

def main():
    print("--- 进入 Main 函数 ---")
    try:
        client = KplerClient()
        if client.verify_connection():
            print("连接成功！尝试拉取数据...")
            data = client.fetch_inventory()
            print(f"拿到数据条数: {len(data)}")
            if data:
                print("样例数据:", data[0])
        else:
            print("连接验证失败")
    except Exception as e:
        print(f"运行出错: {e}")

if __name__ == "__main__":
    main()

