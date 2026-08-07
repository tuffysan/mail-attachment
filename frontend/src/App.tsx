import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { ProtectedRoute } from './components/ProtectedRoute'
import { DashboardPage } from './pages/DashboardPage'
import { LoginPage } from './pages/LoginPage'
import { EmailAccountsPage } from './pages/EmailAccountsPage'
import { RulesPage } from './pages/RulesPage'
import { StoragePage } from './pages/StoragePage'
import { AdminPage } from './pages/AdminPage'
import { SetupWizardPage } from './pages/SetupWizardPage'
import { SetupGuard } from './components/SetupGuard'
import { GoogleOAuthSetupPage } from './pages/GoogleOAuthSetupPage'
import { BackupsPage } from './pages/BackupsPage'

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/setup" element={<ProtectedRoute><SetupWizardPage /></ProtectedRoute>} />
        <Route path="/" element={<ProtectedRoute><SetupGuard><DashboardPage /></SetupGuard></ProtectedRoute>} />
        <Route path="/email-accounts" element={<ProtectedRoute><SetupGuard><EmailAccountsPage /></SetupGuard></ProtectedRoute>} />
        <Route path="/rules" element={<ProtectedRoute><SetupGuard><RulesPage /></SetupGuard></ProtectedRoute>} />
        <Route path="/storage" element={<ProtectedRoute><SetupGuard><StoragePage /></SetupGuard></ProtectedRoute>} />
        <Route path="/admin" element={<ProtectedRoute><SetupGuard><AdminPage /></SetupGuard></ProtectedRoute>} />
        <Route path="/admin/google-oauth" element={<ProtectedRoute><SetupGuard><GoogleOAuthSetupPage /></SetupGuard></ProtectedRoute>} />
        <Route path="/admin/backups" element={<ProtectedRoute><SetupGuard><BackupsPage /></SetupGuard></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  )
}
