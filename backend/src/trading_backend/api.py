from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
import redis
import json
import asyncio
import os

app = FastAPI()

# 1. 允许跨域 (CORS)
# 这非常重要！否则你的 xiaoni.xyz 前端连不上 data.xiaoni.xyz
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境可以改成 ["https://xiaoni.xyz"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. 连接 Redis (填入你的 Upstash 密码)
# 建议放入环境变量，但现在为了跑通先硬编码
REDIS_HOST = 'clean-tahr-19753.upstash.io'
REDIS_PASS = 'AU0pAAIncDE4MGY1NzFhNTM5MDg0YjcwYjNhNjg0NzY0Zjc4MWVhMHAxMTk3NTM'  # ⚠️ 记得填密码！
STREAM_KEY = "crypto_stream"

r = redis.Redis(
    host=REDIS_HOST, port=6379, password=REDIS_PASS, 
    ssl=True, decode_responses=True
)

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Trading Dashboard API"}

# 3. 核心：WebSocket 实时推送接口
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("前端已连接 WebSocket!")
    
    # 这里的 last_id '$' 表示只读最新的，'0-0' 表示从头读
    last_id = '$' 
    
    try:
        while True:
            # 从 Redis Stream 读取新数据
            # block=1000 表示如果没有数据，等待 1秒，避免死循环卡死
            response = r.xread({STREAM_KEY: last_id}, count=1, block=1000)
            
            if response:
                for stream_name, messages in response:
                    for message_id, data in messages:
                        # 更新 last_id，确保下一轮只读更新的数据
                        last_id = message_id
                        
                        # 把数据发送给前端
                        await websocket.send_json(data)
            else:
                # 这是一个心跳包，防止连接断开 (可选)
                await asyncio.sleep(0.1)
                
    except Exception as e:
        print(f"WebSocket 断开: {e}")