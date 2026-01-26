import os
import sys
import uvicorn

if __name__ == "__main__":
    # 1. 获取项目根目录
    root_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. 构造三个核心文件夹的 src 路径
    backend_src = os.path.join(root_dir, "backend", "src")
    connectors_src = os.path.join(root_dir, "connectors", "src")
    core_src = os.path.join(root_dir, "core", "src")
    
    # 3. 【关键】同时修改当前进程 path 和 系统环境变量
    # 这样无论是当前进程，还是 Uvicorn 重启的子进程，都能找到包
    sys.path.insert(0, backend_src)
    sys.path.insert(0, connectors_src)
    sys.path.insert(0, core_src)

    # 设置环境变量 PYTHONPATH (Windows 用 ; 分隔)
    os.environ["PYTHONPATH"] = f"{backend_src};{connectors_src};{core_src};{os.environ.get('PYTHONPATH', '')}"

    print("\n🚀 Trading Dashboard API 正在启动...")
    print("👉 接口文档: http://127.0.0.1:8000/docs\n")

    # 4. 启动服务器
    try:
        # 注意：这里直接运行，不要用 uv run 再次包裹，避免环境重置
        uvicorn.run("trading_backend.main:app", host="127.0.0.1", port=8000, reload=True)
    except KeyboardInterrupt:
        print("\n🛑 服务器已停止")