import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { Navbar } from '../components/layout/Navbar'
import { Providers } from './providers'
import { DashboardPage } from '../features/dashboard/DashboardPage'
import { AnalystPage } from '../features/analyst/AnalystPage'
import { PersonasPage } from '../features/personas/PersonasPage'

export function App() {
  return (
    <Providers>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950">
          <Navbar />
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/analyst" element={<AnalystPage />} />
            <Route path="/personas" element={<PersonasPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </BrowserRouter>
    </Providers>
  )
}
