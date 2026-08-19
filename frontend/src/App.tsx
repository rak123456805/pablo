import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/Navbar';
import { ViewerNavbar } from './components/ViewerNavbar';
import { LoginPage } from './pages/LoginPage';
import { ShowsListPage } from './pages/ShowsListPage';
import { ShowDetailPage } from './pages/ShowDetailPage';
import { PublishPage } from './pages/PublishPage';
import { ViewerHomePage } from './pages/ViewerHomePage';
import { ViewerSearchPage } from './pages/ViewerSearchPage';
import { ViewerShowDetailPage } from './pages/ViewerShowDetailPage';
import { GuidePage } from './pages/GuidePage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-950 flex items-center justify-center text-slate-400 text-xs font-mono">
        Loading CMS session...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
};

export const AppLayout: React.FC = () => {
  const location = useLocation();
  const isViewer = location.pathname.startsWith('/viewer');

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans">
      {/* Dynamic Header based on active mode */}
      {isViewer ? <ViewerNavbar /> : <Navbar />}

      <main className="flex-1">
        <Routes>
          {/* Public Child-Facing Viewer Routes */}
          <Route path="/viewer" element={<ViewerHomePage />} />
          <Route path="/viewer/explore" element={<ViewerSearchPage />} />
          <Route path="/viewer/shows/:slug" element={<ViewerShowDetailPage />} />

          {/* Internal CMS Studio Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/shows"
            element={
              <ProtectedRoute>
                <ShowsListPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/shows/:id"
            element={
              <ProtectedRoute>
                <ShowDetailPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/publish"
            element={
              <ProtectedRoute>
                <PublishPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/guide"
            element={
              <ProtectedRoute>
                <GuidePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/guide/editor"
            element={
              <ProtectedRoute>
                <GuidePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/admin/guide/admin"
            element={
              <ProtectedRoute>
                <GuidePage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/guide"
            element={
              <ProtectedRoute>
                <GuidePage />
              </ProtectedRoute>
            }
          />

          {/* Fallback to Viewer Home */}
          <Route path="*" element={<Navigate to="/viewer" replace />} />
        </Routes>
      </main>
    </div>
  );
};

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <AppLayout />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}
