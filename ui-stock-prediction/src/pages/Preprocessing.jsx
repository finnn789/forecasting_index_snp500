import { useState } from 'react'
import PageContainer from '../layout/PageContainer'
import Card, { CardContent } from '../components/Card'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../components/ui/tabs'
import AnalysisPanel from '../components/data-analysis/AnalysisPanel'

const TABS = [
  { value: 'pipeline-steps', label: 'OHLCV + Sentiment Mean', path: '/data-analysis/combined/pipeline-steps' },
  { value: 'stocks',         label: 'OHLCV Saja',             path: '/data-analysis/stocks/preprocessing' },
]

export default function Preprocessing() {
  const [activeTab, setActiveTab] = useState(TABS[0].value)

  return (
    <PageContainer
      title="Data Preprocessing"
      description="Tahap-tahap pembersihan & transformasi data sebelum masuk model — dari data mentah hingga siap latih."
    >
      <Card>
        <CardContent className="p-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList>
              {TABS.map((tab) => (
                <TabsTrigger key={tab.value} value={tab.value}>
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>

            {TABS.map((tab) => (
              <TabsContent key={tab.value} value={tab.value}>
                {activeTab === tab.value && <AnalysisPanel path={tab.path} />}
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </PageContainer>
  )
}
