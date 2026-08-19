import React, { createContext, useContext, useEffect, useState } from 'react';
import { api } from '../api/client';
import type { User } from '../types';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  isAdmin: boolean;
  isEditor: boolean;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('peblo_token'));
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const fetchUser = async () => {
    if (!localStorage.getItem('peblo_token')) {
      setUser(null);
      setIsLoading(false);
      return;
    }
    try {
      const u = await api.getCurrentUser();
      setUser(u);
    } catch (err) {
      console.error('Failed to fetch user', err);
      localStorage.removeItem('peblo_token');
      setToken(null);
      setUser(null);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchUser();
  }, [token]);

  const login = async (newToken: string) => {
    localStorage.setItem('peblo_token', newToken);
    setToken(newToken);
    setIsLoading(true);
    await fetchUser();
  };

  const logout = () => {
    localStorage.removeItem('peblo_token');
    setToken(null);
    setUser(null);
  };

  const isAdmin = user?.role === 'admin';
  const isEditor = user?.role === 'editor' || isAdmin;

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        isLoading,
        login,
        logout,
        isAdmin,
        isEditor,
        refreshUser: fetchUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
