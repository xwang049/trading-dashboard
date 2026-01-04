# Windows Docker 启动指南

完整的 Windows 环境下使用 Docker Desktop 启动 Trading Dashboard 的步骤。

## 📋 前置条件

- Windows 10/11 (64-bit)
- 至少 4GB RAM
- 至少 10GB 可用磁盘空间

## 步骤 1: 安装 Docker Desktop

### 1.1 下载

访问 Docker 官网下载：
- 网址：https://www.docker.com/products/docker-desktop/
- 点击 "Download for Windows"
- 下载完成后运行 `Docker Desktop Installer.exe`

### 1.2 安装

1. 运行安装程序
2. 勾选 "Use WSL 2 instead of Hyper-V" (推荐)
3. 点击 "Ok" 开始安装
4. 安装完成后点击 "Close and restart"

### 1.3 启动 Docker Desktop

1. 重启后，从开始菜单启动 "Docker Desktop"
2. 首次启动可能需要几分钟
3. 等待右下角 Docker 图标变成绿色（表示 Docker 引擎已启动）
4. 如果提示安装 WSL 2，按照提示完成安装

### 1.4 验证安装

打开 PowerShell，运行：

```powershell
docker --version
docker compose version
```

应该看到类似输出：
```
Docker version 24.0.x, build xxxxx
Docker Compose version v2.x.x
```

## 步骤 2: 准备项目

### 2.1 确认项目文件

确保您在项目根目录：

```powershell
cd C:\git\trading-dashboard

# 查看目录结构
dir
```

应该看到以下关键文件：
- `docker-compose.yml` ✅
- `Dockerfile.backend` ✅
- `nginx.conf` ✅
- `.env.example` ✅
- `database/init.sql` ✅

### 2.2 创建环境变量文件

```powershell
# 复制环境变量模板
copy .env.example .env

# 使用记事本编辑（或使用 VS Code）
notepad .env
```

**推荐的 `.env` 配置**（Windows Docker 环境）：

```env
# Database Configuration
DATABASE_URL=postgresql://trader:trader123@postgres:5432/trading
DB_PASSWORD=trader123

# Redis Configuration
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=redis123
REDIS_SSL=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# CurveSeries Configuration
CURVESERIES_ENABLED=false

# Logging
LOG_LEVEL=INFO

# Environment
ENVIRONMENT=production
```

**重要提示**：
- 在 Docker 环境中，`CURVESERIES_ENABLED` 应设置为 `false`
- 如果需要使用 CurveSeries，需要在本地运行后端（见下文）

## 步骤 3: 启动服务

### 3.1 首次启动（构建镜像）

```powershell
# 在项目根目录
cd C:\git\trading-dashboard

# 启动所有服务（首次会自动构建镜像，需要几分钟）
docker compose up -d

# 查看构建和启动日志
docker compose logs -f
```

**预期输出**：
```
[+] Running 5/5
 ✔ Network trading-dashboard_trading-network  Created
 ✔ Volume "trading-dashboard_timescale_data"  Created
 ✔ Volume "trading-dashboard_redis_data"      Created
 ✔ Container trading-postgres                 Started
 ✔ Container trading-redis                    Started
 ✔ Container trading-backend                  Started
 ✔ Container trading-nginx                    Started
```

### 3.2 检查服务状态

```powershell
# 查看所有服务状态
docker compose ps
```

**预期输出**：
```
NAME               IMAGE                              STATUS         PORTS
trading-backend    trading-dashboard-backend          Up             0.0.0.0:8000->8000/tcp
trading-nginx      nginx:alpine                       Up             0.0.0.0:80->80/tcp
trading-postgres   timescale/timescaledb:latest-pg16  Up (healthy)   0.0.0.0:5432->5432/tcp
trading-redis      redis:7-alpine                     Up (healthy)   0.0.0.0:6379->6379/tcp
```

所有服务的 STATUS 都应该是 "Up" 或 "Up (healthy)"。

### 3.3 查看日志

```powershell
# 查看所有服务日志
docker compose logs -f

# 只查看后端日志
docker compose logs -f backend

# 只查看数据库日志
docker compose logs -f postgres
```

按 `Ctrl+C` 退出日志查看。

## 步骤 4: 验证服务

### 4.1 检查数据库初始化

```powershell
# 连接到数据库容器
docker compose exec postgres psql -U trader -d trading

# 在 psql 提示符下执行：
\dt

# 应该看到以下表：
# - market_data
# - data_sources
# - user_favorites
# - data_quality_log

# 退出
\q
```

### 4.2 测试 API

打开浏览器或使用 PowerShell：

```powershell
# 健康检查
curl http://localhost:8000/api/health

# 或在浏览器中访问：
# http://localhost:8000/docs
```

**预期响应**：
```json
{
  "status": "healthy",
  "database": true,
  "timescaledb": true,
  "environment": "production"
}
```

### 4.3 访问前端

在浏览器中打开：
- **前端界面**: http://localhost
- **API 文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/health

## 步骤 5: 使用 CurveSeries（可选）

Docker 容器内无法直接访问 CurveSeries Desktop。如果需要使用 CurveSeries，有两种方案：

### 方案 A: 本地运行后端（推荐）

```powershell
# 1. 停止 Docker 中的后端服务
docker compose stop backend

# 2. 修改 .env 文件
notepad .env
# 设置：
# CURVESERIES_ENABLED=true
# DATABASE_URL=postgresql://trader:trader123@localhost:5432/trading

# 3. 启动本地后端
python run.py

# 4. 前端仍然通过 http://localhost 访问
# API 通过 http://localhost:8000 访问
```

### 方案 B: 预加载数据

在本地环境中使用 CurveSeries 预加载数据到数据库，然后 Docker 容器可以直接使用：

```powershell
# 1. 在本地运行后端（启用 CurveSeries）
python run.py

# 2. 预加载常用数据
curl -X POST "http://localhost:8000/api/sync/prefetch?tickers=Brent_Crude_Futures_c1.Close&tickers=WTI_Crude_Futures_c1.Close&days=90"

# 3. 停止本地后端，启动 Docker 后端
docker compose start backend
```

## 常用命令

### 服务管理

```powershell
# 启动所有服务
docker compose up -d

# 停止所有服务
docker compose down

# 重启特定服务
docker compose restart backend

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f [service_name]
```

### 数据库操作

```powershell
# 连接到数据库
docker compose exec postgres psql -U trader -d trading

# 备份数据库
docker compose exec postgres pg_dump -U trader trading > backup.sql

# 恢复数据库
docker compose exec -T postgres psql -U trader -d trading < backup.sql

# 查看数据库大小
docker compose exec postgres psql -U trader -d trading -c "SELECT pg_size_pretty(pg_database_size('trading'));"
```

### 容器管理

```powershell
# 进入后端容器
docker compose exec backend bash

# 查看容器资源使用
docker stats

# 清理未使用的资源
docker system prune -a
```

### 重建服务

```powershell
# 重建后端镜像（代码更新后）
docker compose build backend

# 重建并重启
docker compose up -d --build backend

# 完全重建所有服务
docker compose down
docker compose build --no-cache
docker compose up -d
```

## 故障排除

### 问题 1: Docker Desktop 无法启动

**解决方案**：
1. 确保已启用 WSL 2
2. 在 PowerShell（管理员）中运行：
   ```powershell
   wsl --update
   wsl --set-default-version 2
   ```
3. 重启 Docker Desktop

### 问题 2: 端口被占用

**错误信息**：
```
Error: Bind for 0.0.0.0:8000 failed: port is already allocated
```

**解决方案**：
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000

# 结束进程（替换 PID）
taskkill /PID <PID> /F

# 或修改 docker-compose.yml 中的端口映射
# 例如：将 "8000:8000" 改为 "8001:8000"
```

### 问题 3: 数据库初始化失败

**解决方案**：
```powershell
# 1. 停止所有服务
docker compose down

# 2. 删除数据卷
docker volume rm trading-dashboard_timescale_data

# 3. 重新启动
docker compose up -d

# 4. 查看初始化日志
docker compose logs postgres
```

### 问题 4: 后端无法连接数据库

**解决方案**：
```powershell
# 检查网络连接
docker compose exec backend ping postgres

# 检查数据库是否就绪
docker compose exec postgres pg_isready -U trader -d trading

# 重启后端服务
docker compose restart backend
```

### 问题 5: 前端无法访问

**解决方案**：
1. 检查 nginx 服务状态：`docker compose ps nginx`
2. 查看 nginx 日志：`docker compose logs nginx`
3. 确认端口 80 未被占用
4. 尝试访问：http://localhost:8000/docs（直接访问后端）

## 性能优化

### 1. 增加 Docker 资源

1. 打开 Docker Desktop
2. 设置 → Resources
3. 调整：
   - CPUs: 4+
   - Memory: 4GB+
   - Swap: 1GB+

### 2. 启用 BuildKit

在 PowerShell 中设置环境变量：
```powershell
$env:DOCKER_BUILDKIT=1
$env:COMPOSE_DOCKER_CLI_BUILD=1
```

### 3. 使用卷挂载加速

已在 `docker-compose.yml` 中配置，无需额外操作。

## 数据持久化

### 数据存储位置

Docker 卷存储在：
```
C:\Users\<YourUsername>\AppData\Local\Docker\wsl\data\
```

### 备份数据

```powershell
# 备份数据库
docker compose exec postgres pg_dump -U trader trading > backup_$(Get-Date -Format 'yyyyMMdd').sql

# 备份 Docker 卷
docker run --rm -v trading-dashboard_timescale_data:/data -v ${PWD}:/backup alpine tar czf /backup/timescale_backup.tar.gz /data
```

### 恢复数据

```powershell
# 恢复数据库
Get-Content backup.sql | docker compose exec -T postgres psql -U trader -d trading
```

## 停止和清理

### 停止服务（保留数据）

```powershell
docker compose down
```

### 完全清理（删除所有数据）

```powershell
# 停止并删除容器、网络、卷
docker compose down -v

# 删除镜像
docker rmi trading-dashboard-backend
```

## 下一步

1. ✅ 服务已启动
2. ✅ 数据库已初始化
3. ✅ API 可访问
4. ✅ 前端可访问

现在您可以：
- 访问 http://localhost 使用前端界面
- 访问 http://localhost:8000/docs 查看 API 文档
- 使用 API 测试数据查询功能
- 如需使用 CurveSeries，按照上述"方案 A"本地运行后端

## 获取帮助

如遇到问题：
1. 查看日志：`docker compose logs -f`
2. 检查服务状态：`docker compose ps`
3. 参考 SETUP_GUIDE.md
4. 在 GitHub 提交 issue

---

**祝您使用愉快！** 🚀
