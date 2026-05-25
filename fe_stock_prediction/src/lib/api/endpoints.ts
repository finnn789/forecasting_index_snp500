export const ENDPOINTS = {
  // Pipeline
  PIPELINE_STATUS:  '/api/pipeline/status',
  PIPELINE_RUN:     '/api/pipeline/run',
  PIPELINE_STOP:    '/api/pipeline/stop',
  PIPELINE_HISTORY: '/api/pipeline/history',
  PIPELINE_LOGS:    '/api/pipeline/logs',    // SSE endpoint

  // Prediction
  PREDICT:          '/api/predict',

  // Sentiment
  SENTIMENT:        '/api/sentiment',

  // EDA
  EDA_NEWS_PER_YEAR:          '/api/v1/data/eda/news-per-year',
  EDA_NEWS_PER_DAY:           '/api/v1/data/eda/news-per-day',
  EDA_HEADLINE_LENGTH:        '/api/v1/data/eda/headline-length',
  EDA_SENTIMENT_DISTRIBUTION: '/api/v1/data/eda/sentiment-distribution',
} as const
