# trading-dashboard
graph TD
    %% Source Layer (杂乱的源头)
    subgraph "Source Layer (多源异构)"
        Kpler[Kpler API] -->|JSON| AdapterKpler
        Reuters[Reuters News] -->|HTML/Text| AdapterReuters
        Email[Email Reports] -->|PDF/Text| AdapterEmail
        Excel[Manual Excel] -->|XLSX| AdapterExcel
    end

    %% Ingestion Layer (标准化层 - 核心)
    subgraph "Ingestion Layer (适配器)"
        AdapterKpler[Connector: Kpler] -->|标准化| KafkaRaw
        AdapterReuters[Connector: Reuters] -->|标准化| KafkaRaw
        AdapterEmail[Connector: Email] -->|标准化| KafkaRaw
        AdapterExcel[Connector: Excel] -->|标准化| KafkaRaw
    end

    %% Storage & Processing
    KafkaRaw[Kafka: raw_data_stream] --> Processor[Data Processor / NLP]
    Processor -->|如果是价格/量| DB_Time[(TimescaleDB)]
    Processor -->|如果是新闻/文本| DB_Search[(Elasticsearch/PG FullText)]

    %% Serving
    DB_Time --> API[FastAPI]
    DB_Search --> API
    API --> Dashboard[Frontend Dashboard]