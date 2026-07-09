import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authApi } from './api';

export function AuthPage() {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [pass, setPass] = useState('');
  const [err, setErr] = useState('');
  const nav = useNavigate();

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr('');
    try {
      if (isLogin) {
        await authApi.login(email, pass);
        nav('/');
      } else {
        await authApi.register(email, pass);
        alert('✅ Зарегистрирован! Теперь войдите.');
        setIsLogin(true);
      }
    } catch {
      setErr('Ошибка. Проверьте данные.');
    }
  };

  return (
    <div style={{ maxWidth: 360, margin: '80px auto', fontFamily: 'sans-serif' }}>
      <h2>{isLogin ? '🔑 Вход' : '📝 Регистрация'}</h2>
      <form onSubmit={submit}>
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)}
          required style={inp} />
        <input type="password" placeholder="Пароль" value={pass} onChange={e => setPass(e.target.value)}
          required style={inp} />
        {err && <p style={{ color: 'red', fontSize: 14 }}>{err}</p>}
        <button type="submit" style={btn}>
          {isLogin ? 'Войти' : 'Зарегистрироваться'}
        </button>
      </form>
      <p style={{ marginTop: 16, fontSize: 14 }}>
        {isLogin ? 'Нет аккаунта?' : 'Есть аккаунт?'}{' '}
        <a href="#" onClick={e => { e.preventDefault(); setIsLogin(!isLogin); }}>
          {isLogin ? 'Регистрация' : 'Войти'}
        </a>
      </p>
    </div>
  );
}

const inp: React.CSSProperties = { display: 'block', width: '100%', padding: 10, marginBottom: 10, boxSizing: 'border-box' };
const btn: React.CSSProperties = { width: '100%', padding: 12, cursor: 'pointer', background: '#4f46e5', color: '#fff', border: 'none', borderRadius: 4 };
