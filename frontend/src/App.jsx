/**
 * Root React application component configuring TanStack Query, Auth Provider,
 * and React Router navigation.
 */

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/common/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';

// Auth Pages
import LoginPage from './pages/auth/LoginPage';
import RegisterPage from './pages/auth/RegisterPage';

// App Views
import DashboardPage from './pages/DashboardPage';
import StoragePage from './pages/StoragePage';
import SharedPage from './pages/SharedPage';
import StarredPage from './pages/StarredPage';
import TrashPage from './pages/TrashPage';
import TagsPage from './pages/TagsPage';
import SearchPage from './pages/SearchPage';
import PublicSharePage from './pages/PublicSharePage';
import NotFoundPage from './pages/NotFoundPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60 * 2, // 2 minutes
    },
  },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Authentication Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />

            {/* Public Unauthenticated Share Viewer */}
            <Route path="/share/:token" element={<PublicSharePage />} />
            <Route path="/public/links/:token" element={<PublicSharePage />} />

            {/* Protected Drive Application Layout */}
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
              <Route path="shared" element={<SharedPage />} />
              <Route path="starred" element={<StarredPage />} />
              <Route path="trash" element={<TrashPage />} />
              <Route path="tags" element={<TagsPage />} />
              <Route path="search" element={<SearchPage />} />
              <Route path="storage" element={<StoragePage />} />
            </Route>

            {/* Fallback 404 Route */}
            <Route path="*" element={<NotFoundPage />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
