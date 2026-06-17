export const ENDPOINTS = {
  // Prediction
  PREDICT:             '/api/v1/predict',
  PREDICT_STATUS:      '/api/v1/predict/model/status',
  PREDICT_BACKTEST:    '/api/v1/predict/backtest',

  // System
  HEALTH:              '/api/health',
  STATUS:              '/api/status',

  // Stocks EDA
  STOCK_TIMESERIES:    '/api/v1/data/eda/stocks/time-series',
  STOCK_RAW:           '/api/v1/data/eda/stocks/raw',
  STOCK_RETURNS:       '/api/v1/data/eda/stocks/daily-returns',
  STOCK_DRAWDOWN:      '/api/v1/data/eda/stocks/drawdown',
  STOCK_DESC_STATS:    '/api/v1/data/eda/stocks/descriptive-stats',
  STOCK_SUMMARY:       '/api/v1/data/eda/stocks/summary',

  // Sentiment / News EDA
  SENTIMENT_DIST:      '/api/v1/data/eda/sentiment-distribution',
  NEWS_PER_YEAR:       '/api/v1/data/eda/news-per-year',
  NEWS_PER_DAY:        '/api/v1/data/eda/news-per-day',
  HEADLINE_LENGTH:     '/api/v1/data/eda/headline-length',
  SENTIMENT_PREVIEW:   '/api/v1/sentiment/data/preview',
  SENTIMENT_MODEL:     '/api/v1/sentiment/model/status',

  // Sentiment Pipeline
  PIPELINE_STATUS:     '/api/v1/sentiment/pipeline/status',
  PIPELINE_RUN:        '/api/v1/sentiment/pipeline/run',

  // Feature engineering
  FE_COLUMNS:          '/api/v1/feature-engineering/columns',
  FE_INFO:             '/api/v1/feature-engineering/info',
  FE_PREVIEW:          '/api/v1/feature-engineering/preview',

  // --- Backward-compat aliases (consumed by eda.api.ts and sentiment.api.ts) ---
  EDA_NEWS_PER_YEAR:           '/api/v1/data/eda/news-per-year',
  EDA_NEWS_PER_DAY:            '/api/v1/data/eda/news-per-day',
  EDA_HEADLINE_LENGTH:         '/api/v1/data/eda/headline-length',
  EDA_SENTIMENT_DISTRIBUTION:  '/api/v1/data/eda/sentiment-distribution',
  SENTIMENT:                   '/api/v1/data/eda/sentiment-distribution',
  STOCK_HISTORY:               '/api/v1/data/eda/stocks/raw',
} as const
