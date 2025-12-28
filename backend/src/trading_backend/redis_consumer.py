import redis
import time
import os
from dotenv import load_dotenv

# 1. 加载环境变量
load_dotenv()

# 2. 配置信息 (从 .env 读取)
REDIS_HOST = os.getenv('REDIS_HOST')
REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD')

# Stream 配置
STREAM_KEY = "crypto_stream"
GROUP_NAME = "dashboard_group"  # 消费者组名
CONSUMER_NAME = "worker_1"      # 消费者名 (如果你开多个终端跑，可以改名为 worker_2)

# 连接 Redis
r = redis.Redis(
    host=REDIS_HOST, 
    port=REDIS_PORT, 
    password=REDIS_PASSWORD, 
    ssl=True, 
    decode_responses=True
)

def create_group():
    """初始化消费者组 (只需运行一次，如果存在则忽略)"""
    try:
        # '0' 表示从头开始读历史数据
        # '$' 表示只读程序启动后新产生的数据 (通常用这个)
        r.xgroup_create(STREAM_KEY, GROUP_NAME, id='$', mkstream=True)
        print(f"✅ 消费者组 '{GROUP_NAME}' 创建成功")
    except redis.exceptions.ResponseError as e:
        # 如果组已经存在，Redis 会报错 BUSYGROUP，我们需要捕获它并继续
        if "BUSYGROUP" in str(e):
            print(f"ℹ️ 消费者组 '{GROUP_NAME}' 已存在，准备监听...")
        else:
            raise e

def consume():
    # 确保组存在
    create_group()
    print(f"🎧 {CONSUMER_NAME} 开始监听 Stream: {STREAM_KEY}...")

    while True:
        try:
            # 🚀 核心命令：XREADGROUP
            # group=GROUP_NAME, consumer=CONSUMER_NAME
            # {STREAM_KEY: '>'} 表示请求“未被组内其他消费者处理过的新消息”
            # block=2000: 如果没消息，阻塞等待 2000毫秒 (2秒)，比 while True + sleep 更高效
            entries = r.xreadgroup(
                GROUP_NAME, 
                CONSUMER_NAME, 
                {STREAM_KEY: '>'}, 
                count=1, 
                block=2000
            )

            if entries:
                for stream, messages in entries:
                    for message_id, data in messages:
                        print(f"📥 [{CONSUMER_NAME}] 收到数据: {data}")
                        
                        # --- 业务逻辑区域 ---
                        # 比如: insert_to_db(data)
                        # ------------------
                        
                        # ✅ ACK 确认
                        # 告诉 Redis "这条消息我处理完了"，否则下次崩溃重启后，Redis 还会发给你
                        r.xack(STREAM_KEY, GROUP_NAME, message_id)
            
            # 这里不需要 time.sleep()，因为 xreadgroup 的 block 参数已经帮我们实现了“有消息就处理，没消息就挂起”

        except redis.ConnectionError:
            print("❌ Redis 连接断开，3秒后重试...")
            time.sleep(3)
        except Exception as e:
            print(f"❌ 未知错误: {e}")
            time.sleep(1)

if __name__ == "__main__":
    try:
        consume()
    except KeyboardInterrupt:
        print("\n🛑 Consumer 已停止")