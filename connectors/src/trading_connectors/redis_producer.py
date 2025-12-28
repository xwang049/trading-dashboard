import json
import redis
import websocket
import time
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

class RedisBinanceProducer:
    def __init__(self):
        # 👇 修改点 1: 从环境变量读取配置，不再硬编码
        self.r = redis.Redis(
            host=os.getenv('REDIS_HOST'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            password=os.getenv('REDIS_PASSWORD'),
            ssl=True,  # Upstash 必须开启 SSL
            decode_responses=True
        )
        self.stream_key = "crypto_stream"
        
        # 👇 修改点 2: 初始化一个变量来记录上次发送的时间
        self.last_send_time = 0
        
        print(f"✅ 连接 Redis 成功: {os.getenv('REDIS_HOST')}")

    def on_message(self, ws, message):
        """
        这个函数会被 Binance 频繁触发（每秒可能几十次）。
        我们需要在这里通过判断时间来实现“每5秒发一次”。
        """
        current_time = time.time()

        # 👇 核心逻辑：如果距离上次发送还不到 5 秒，直接跳过，不处理
        if current_time - self.last_send_time < 5:
            return

        # --- 以下是 5 秒才执行一次的代码 ---
        
        try:
            data = json.loads(message)
            
            payload = {
                "symbol": data.get('s'),
                "price": data.get('p'),
                "quantity": data.get('q'),
                "timestamp": data.get('T')
            }

            # 写入 Redis Stream
            # maxlen=10000 意味着自动修剪，只保留最新的1万条
            self.r.xadd(self.stream_key, payload, maxlen=10000)
            
            # 更新上次发送时间
            self.last_send_time = current_time
            
            print(f"🚀 [每5秒更新] Sent to Redis: {payload['symbol']} @ {payload['price']}")
            
        except Exception as e:
            print(f"❌ 数据处理错误: {e}")

    def on_error(self, ws, error):
        print(f"❌ WebSocket 错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("🔌 WebSocket 连接已关闭")

    def start(self):
        socket = "wss://stream.binance.com:9443/ws/btcusdt@trade"
        # 建议加上 on_error 和 on_close 以便调试
        ws = websocket.WebSocketApp(
            socket, 
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        print("Waiting for Binance data...")
        ws.run_forever()

if __name__ == "__main__":
    producer = RedisBinanceProducer()
    try:
        producer.start()
    except KeyboardInterrupt:
        print("\n🛑 程序已停止")