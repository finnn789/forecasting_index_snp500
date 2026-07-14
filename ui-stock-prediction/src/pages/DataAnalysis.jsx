import { useState } from 'react'
import PageContainer from '../layout/PageContainer'
import Card, { CardContent } from '../components/Card'
import Dropdown from '../components/ui/dropdown'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import AnalysisPanel from '../components/data-analysis/AnalysisPanel'

const CATEGORIES = [
  {
    value: 'stocks',
    label: 'Data OHLCV Saham',
    description: '^GSPC — harga, volume, dan statistik time-series',
    icon: 'candlestick_chart',
    tabs: [
      { value: 'raw-info', label: 'Info Data Mentah', path: '/data-analysis/stocks/raw-info' },
      { value: 'descriptive-stats', label: 'Statistik Deskriptif', path: '/data-analysis/stocks/descriptive-stats' },
      { value: 'price-volume', label: 'Harga & Volume', path: '/data-analysis/stocks/price-volume' },
      { value: 'daily-returns', label: 'Daily Return', path: '/data-analysis/stocks/daily-returns' },
      { value: 'rolling-stats', label: 'Rolling Stats', path: '/data-analysis/stocks/rolling-stats' },
      { value: 'ohlc-spread', label: 'OHLC Spread', path: '/data-analysis/stocks/ohlc-spread' },
      { value: 'correlation', label: 'Correlation', path: '/data-analysis/stocks/correlation' },
      { value: 'seasonality', label: 'Seasonality', path: '/data-analysis/stocks/seasonality' },
      { value: 'cumulative-return-drawdown', label: 'Return & Drawdown', path: '/data-analysis/stocks/cumulative-return-drawdown' },
      { value: 'summary', label: 'Ringkasan EDA', path: '/data-analysis/stocks/summary' },
    ],
  },
  {
    value: 'sentiment',
    label: 'Data Sentimen Berita',
    description: 'Headline berita + skor FinBERT',
    icon: 'newspaper',
    tabs: [
      { value: 'raw-info', label: 'Info Data Mentah', path: '/data-analysis/sentiment/raw-info' },
      { value: 'news-per-year', label: 'Berita per Tahun', path: '/data-analysis/sentiment/news-per-year' },
      { value: 'news-per-day', label: 'Berita per Hari', path: '/data-analysis/sentiment/news-per-day' },
      { value: 'headline-length', label: 'Panjang Headline', path: '/data-analysis/sentiment/headline-length' },
      { value: 'closing-price', label: 'Closing Price', path: '/data-analysis/sentiment/closing-price' },
      { value: 'scoring-distribution', label: 'Skor FinBERT', path: '/data-analysis/sentiment/scoring-distribution' },
      { value: 'daily-aggregation', label: 'Agregasi Harian', path: '/data-analysis/sentiment/daily-aggregation' },
      { value: 'method-comparison', label: 'Perbandingan Metode', path: '/data-analysis/sentiment/method-comparison' },
    ],
  },
]

export default function DataAnalysis() {
  const [categoryValue, setCategoryValue] = useState(CATEGORIES[0].value)
  const category = CATEGORIES.find((c) => c.value === categoryValue)
  const [activeTab, setActiveTab] = useState(category.tabs[0].value)

  function handleCategoryChange(value) {
    setCategoryValue(value)
    const next = CATEGORIES.find((c) => c.value === value)
    setActiveTab(next.tabs[0].value)
  }

  const activePath = category.tabs.find((t) => t.value === activeTab)?.path

  return (
    <PageContainer
      title="Data Analysis"
      description="Eksplorasi setiap langkah alur EDA — pilih kategori data, lalu telusuri tab analisisnya."
    >
      <Dropdown value={categoryValue} onChange={handleCategoryChange} options={CATEGORIES} className="max-w-sm" />

      <Card>
        <CardContent className="p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              {category.tabs.map((tab) => (
                <TabsTrigger key={tab.value} value={tab.value}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>

            {category.tabs.map((tab) => (
              <TabsContent key={tab.value} value={tab.value}>
                {activeTab === tab.value && <AnalysisPanel path={activePath} />}
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
