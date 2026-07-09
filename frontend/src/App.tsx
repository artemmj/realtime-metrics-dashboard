import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthPage } from './AuthPage';
import { HomePage } from './HomePage';
import { authApi } from './api';

// Простейшая защита: если нет токена → редирект на /auth
function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return authApi.getToken() ? <>{children}</> : <Navigate to="/auth" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/auth" element={<AuthPage />} />
        <Route path="/" element={<ProtectedRoute><HomePage /></ProtectedRoute>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
