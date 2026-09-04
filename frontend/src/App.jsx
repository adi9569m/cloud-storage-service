import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import { ToastProvider } from './context/ToastContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

import DashboardPage from './pages/DashboardPage';
import RecentPage from './pages/RecentPage';
import StoragePage from './pages/StoragePage';
import SharedPage from './pages/SharedPage';
import StarredPage from './pages/StarredPage';
import TrashPage from './pages/TrashPage';
import TagsPage from './pages/TagsPage';
import ActivityPage from './pages/ActivityPage';
import SettingsPage from './pages/SettingsPage';
import SearchPage from './pages/SearchPage';
import PublicSharePage from './pages/PublicSharePage';
import NotFoundPage from './pages/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 2,
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <ToastProvider>
          <BrowserRouter>
            <Routes>

              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              <Route path="/share/:token" element={<PublicSharePage />} />
              <Route path="/public/links/:token" element={<PublicSharePage />} />

              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <AppLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="drive" element={<Navigate to="/" replace />} />
                <Route path="recent" element={<RecentPage />} />
                <Route path="shared" element={<SharedPage />} />
                <Route path="starred" element={<StarredPage />} />
                <Route path="trash" element={<TrashPage />} />
                <Route path="tags" element={<TagsPage />} />
                <Route path="activity" element={<ActivityPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="search" element={<SearchPage />} />
                <Route path="storage" element={<StoragePage />} />
              </Route>

              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </BrowserRouter>
        </ToastProvider>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
