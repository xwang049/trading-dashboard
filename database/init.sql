-- Trading Dashboard Database Schema
-- PostgreSQL + TimescaleDB

-- 创建 TimescaleDB 扩展
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 主数据表：存储所有时间序列数据
CREATE TABLE IF NOT EXISTS market_data (
    id BIGSERIAL,
    source VARCHAR(50) NOT NULL,           -- 数据源: curveseries, binance, reuters
    ticker VARCHAR(200) NOT NULL,          -- 标识符/公式
    timestamp TIMESTAMPTZ NOT NULL,        -- 数据时间戳
    value DOUBLE PRECISION NOT NULL,       -- 核心数值
    unit VARCHAR(50),                      -- 单位: USD, bbl, mt
    metadata JSONB DEFAULT '{}',           -- 额外标签和信息
    raw_data JSONB,                        -- 原始数据备份
    created_at TIMESTAMPTZ DEFAULT NOW(),  -- 入库时间
    PRIMARY KEY (id, timestamp)
);

-- 转换为 TimescaleDB 超表（hypertable）
-- 按时间分区，每个 chunk 存储 7 天数据
SELECT create_hypertable(
    'market_data', 
    'timestamp',
    chunk_time_interval => INTERVAL '7 days',
    if_not_exists => TRUE
);

-- 创建索引以优化查询性能
CREATE INDEX IF NOT EXISTS idx_market_data_ticker_time 
    ON market_data (ticker, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_market_data_source 
    ON market_data (source, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_market_data_metadata 
    ON market_data USING GIN (metadata);

-- 创建数据源配置表
CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,      -- curveseries, binance
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB DEFAULT '{}',             -- 配置信息
    last_sync TIMESTAMPTZ,                 -- 最后同步时间
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 创建用户收藏表（保存常用公式）
CREATE TABLE IF NOT EXISTS user_favorites (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(100) DEFAULT 'default', -- 未来扩展用户系统
    ticker VARCHAR(200) NOT NULL,
    display_name VARCHAR(200),
    config JSONB DEFAULT '{}',              -- 图表配置
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_favorites_user 
    ON user_favorites (user_id, created_at DESC);

-- 创建数据质量监控表
CREATE TABLE IF NOT EXISTS data_quality_log (
    id BIGSERIAL PRIMARY KEY,
    source VARCHAR(50) NOT NULL,
    ticker VARCHAR(200),
    issue_type VARCHAR(50),                -- missing_data, invalid_value, duplicate
    description TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- 插入默认数据源配置
INSERT INTO data_sources (name, enabled, config) VALUES
    ('curveseries', TRUE, '{"description": "CurveSeries Desktop API"}'),
    ('binance', TRUE, '{"description": "Binance WebSocket Stream"}')
ON CONFLICT (name) DO NOTHING;

-- 创建自动更新 updated_at 的触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_data_sources_updated_at
    BEFORE UPDATE ON data_sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- 创建数据保留策略（可选：自动删除旧数据）
-- 保留 1 年数据，之后自动删除
-- SELECT add_retention_policy('market_data', INTERVAL '1 year');

-- 创建连续聚合视图（可选：用于快速查询统计数据）
-- 每小时的 OHLC 数据
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS bucket,
    source,
    ticker,
    first(value, timestamp) AS open,
    max(value) AS high,
    min(value) AS low,
    last(value, timestamp) AS close,
    count(*) AS data_points
FROM market_data
GROUP BY bucket, source, ticker
WITH NO DATA;

-- 设置连续聚合的刷新策略
SELECT add_continuous_aggregate_policy('market_data_hourly',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour',
    if_not_exists => TRUE);

-- 创建每日聚合视图
CREATE MATERIALIZED VIEW IF NOT EXISTS market_data_daily
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 day', timestamp) AS bucket,
    source,
    ticker,
    first(value, timestamp) AS open,
    max(value) AS high,
    min(value) AS low,
    last(value, timestamp) AS close,
    avg(value) AS avg_value,
    count(*) AS data_points
FROM market_data
GROUP BY bucket, source, ticker
WITH NO DATA;

SELECT add_continuous_aggregate_policy('market_data_daily',
    start_offset => INTERVAL '3 days',
    end_offset => INTERVAL '1 day',
    schedule_interval => INTERVAL '1 day',
    if_not_exists => TRUE);

-- 创建查询辅助函数
CREATE OR REPLACE FUNCTION get_latest_value(p_ticker VARCHAR, p_source VARCHAR DEFAULT NULL)
RETURNS TABLE (
    ticker VARCHAR,
    value DOUBLE PRECISION,
    ts TIMESTAMPTZ,
    unit VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        m.ticker,
        m.value,
        m.timestamp,
        m.unit
    FROM market_data m
    WHERE m.ticker = p_ticker
        AND (p_source IS NULL OR m.source = p_source)
    ORDER BY m.timestamp DESC
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- 创建数据插入辅助函数（带去重）
CREATE OR REPLACE FUNCTION insert_market_data(
    p_source VARCHAR,
    p_ticker VARCHAR,
    p_timestamp TIMESTAMPTZ,
    p_value DOUBLE PRECISION,
    p_unit VARCHAR DEFAULT NULL,
    p_metadata JSONB DEFAULT '{}',
    p_raw_data JSONB DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_id BIGINT;
BEGIN
    -- 检查是否已存在相同的数据点（去重）
    SELECT id INTO v_id
    FROM market_data
    WHERE source = p_source
        AND ticker = p_ticker
        AND timestamp = p_timestamp
    LIMIT 1;
    
    IF v_id IS NOT NULL THEN
        -- 如果已存在，更新数据
        UPDATE market_data
        SET value = p_value,
            unit = p_unit,
            metadata = p_metadata,
            raw_data = p_raw_data
        WHERE id = v_id;
        RETURN v_id;
    ELSE
        -- 插入新数据
        INSERT INTO market_data (source, ticker, timestamp, value, unit, metadata, raw_data)
        VALUES (p_source, p_ticker, p_timestamp, p_value, p_unit, p_metadata, p_raw_data)
        RETURNING id INTO v_id;
        RETURN v_id;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 创建批量插入函数
CREATE OR REPLACE FUNCTION bulk_insert_market_data(
    p_data JSONB
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER := 0;
    v_item JSONB;
BEGIN
    FOR v_item IN SELECT * FROM jsonb_array_elements(p_data)
    LOOP
        PERFORM insert_market_data(
            v_item->>'source',
            v_item->>'ticker',
            (v_item->>'timestamp')::TIMESTAMPTZ,
            (v_item->>'value')::DOUBLE PRECISION,
            v_item->>'unit',
            COALESCE(v_item->'metadata', '{}'::JSONB),
            v_item->'raw_data'
        );
        v_count := v_count + 1;
    END LOOP;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- 创建数据统计视图
CREATE OR REPLACE VIEW data_statistics AS
SELECT
    source,
    ticker,
    COUNT(*) AS total_records,
    MIN(timestamp) AS earliest_data,
    MAX(timestamp) AS latest_data,
    MIN(value) AS min_value,
    MAX(value) AS max_value,
    AVG(value) AS avg_value,
    STDDEV(value) AS stddev_value
FROM market_data
GROUP BY source, ticker;

-- 授权（如果需要特定用户）
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trader;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trader;

-- 完成提示
DO $$
BEGIN
    RAISE NOTICE '✅ Database schema initialized successfully!';
    RAISE NOTICE '📊 Tables created: market_data, data_sources, user_favorites, data_quality_log';
    RAISE NOTICE '⚡ TimescaleDB hypertable enabled on market_data';
    RAISE NOTICE '📈 Continuous aggregates created: market_data_hourly, market_data_daily';
END $$;
