const API = 'http://localhost:8080/api/v1/auth';

export const authApi = {
  register: async (email: string, password: string) => {
    const res = await fetch(`${API}/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Registration failed');
    return res.json();
  },

  login: async (email: string, password: string) => {
    const res = await fetch(`${API}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) throw new Error('Login failed');
    const data = await res.json();
    
    // ⚡ Сохраняем токен из ответа
    if (data.token) {
      localStorage.setItem('access_token', data.token);
    }
    return data;
  },

  logout: () => localStorage.removeItem('access_token'),
  
  getToken: () => localStorage.getItem('access_token'),
};
