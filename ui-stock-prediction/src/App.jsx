import { BrowserRouter, Routes, Route } from 'react-router-dom'
import MainLayout from './layout/MainLayout'
import Pipeline from './pages/Pipeline'
import DataAnalysis from './pages/DataAnalysis'
import Preprocessing from './pages/Preprocessing'
import ModelTraining from './pages/ModelTraining'
import Predictions from './pages/Predictions'
import Sentiment from './pages/Sentiment'
import Settings from './pages/Settings'
import DataInformation from './pages/DataInformation'
import Workflow from './pages/Workflow'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<MainLayout />}>
          <Route path="/" element={<Predictions />} />
          <Route path="/pipeline" element={<Pipeline />} />
          <Route path="/data-analysis" element={<DataAnalysis />} />
          <Route path="/preprocessing" element={<Preprocessing />} />
          <Route path="/training" element={<ModelTraining />} />
          <Route path="/data-information" element={<DataInformation />} />
          <Route path="/workflow" element={<Workflow />} />
          <Route path="/sentiment" element={<Sentiment />} />
          <Route path="/settings" element={<Settings />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
