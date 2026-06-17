import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { MainLayout } from './components/layout/MainLayout'
import { DashboardPage }  from './pages/DashboardPage'
import { StockDataPage } from './pages/StockDataPage'
import { SentimentDetailPage } from './pages/SentimentDetailPage'
import { PipelinePage }   from './pages/PipelinePage'
import { PredictionPage } from './pages/PredictionPage'
import { SentimentPage }  from './pages/SentimentPage'
import { LogsPage }       from './pages/LogsPage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/"           element={<DashboardPage />}  />
          <Route path="/overview/stocks"    element={<StockDataPage />}       />
          <Route path="/overview/sentiment" element={<SentimentDetailPage />} />
          <Route path="/pipeline"   element={<PipelinePage />}   />
          <Route path="/prediction" element={<PredictionPage />} />
          <Route path="/sentiment"  element={<SentimentPage />}  />
          <Route path="/logs"       element={<LogsPage />}       />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
