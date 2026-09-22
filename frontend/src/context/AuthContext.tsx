import { useEffect, useState, type ReactNode } from 'react';
import type { User, LoginPayload, RegisterPayload } from '../types/auth';
import { authService } from '../services/authService';
import { getAuthToken, AUTH_EXPIRED_EVENT } from '../services/api';
import { AuthContext } from './AuthContextDefinition';

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = async () => {
    const token = getAuthToken();
    if (!token) {
      setUser(null);
      setIsLoading(false);
      return;
    }

    try {
      const currentUser = await authService.getCurrentUser();
      setUser(currentUser);
    } catch {
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshUser();

    // Har qanday so'rov 401 qaytarsa darvoza darhol login ekraniga qaytsin
    const onExpired = () => setUser(null);
    window.addEventListener(AUTH_EXPIRED_EVENT, onExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, onExpired);
  }, []);

  const login = async (payload: LoginPayload) => {
    const data = await authService.login(payload);
    setUser(data.user);
  };

  const register = async (payload: RegisterPayload) => {
    const data = await authService.register(payload);
    setUser(data.user);
  };

  const logout = async () => {
    await authService.logout();
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
