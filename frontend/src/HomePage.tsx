import { useNavigate } from 'react-router-dom';
import { authApi } from './api';

export function HomePage() {
  const nav = useNavigate();

  const handleLogout = () => {
    authApi.logout();
    nav('/auth');
  };

  return (
    <div style={{ textAlign: 'center', marginTop: 100, fontFamily: 'sans-serif' }}>
      <h1>🎉 Стартовая страница</h1>
      <p>Вы авторизованы. Токен хранится в localStorage.</p>
      <button onClick={handleLogout} style={{ padding: '10px 24px', cursor: 'pointer', marginTop: 20 }}>
        Выйти
      </button>
    </div>
  );
}
