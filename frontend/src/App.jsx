import { Navigate, Route, Routes } from 'react-router-dom';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './layouts/AppLayout';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import KeyloggerLabPage from './pages/KeyloggerLabPage';
import AnalyticsPage from './pages/AnalyticsPage';
import ThreatSimulationPage from './pages/ThreatSimulationPage';
import DetectionPage from './pages/DetectionPage';
import EventsPage from './pages/EventsPage';
import SettingsPage from './pages/SettingsPage';
import NotFoundPage from './pages/NotFoundPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />

      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/keylogger-lab" element={<KeyloggerLabPage />} />
        <Route path="/analytics" element={<AnalyticsPage />} />
        <Route path="/threat-simulation" element={<ThreatSimulationPage />} />
        <Route path="/detection" element={<DetectionPage />} />
        <Route path="/events" element={<EventsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>

      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
