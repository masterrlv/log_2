import React from 'react';
//import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { BrowserRouter,Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import { useAuth } from './context/AuthContext';
import { MantineProvider } from '@mantine/core';

function PrivateRoute({ children }: { children: JSX.Element }) {
  const { user, loading } = useAuth();
  console.log(localStorage.getItem('token'))
  if (loading) {
    return <div>Loading...</div>;
  }
  
  return localStorage.getItem('token') ? children : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
    <MantineProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <DashboardPage />
              </PrivateRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
      </MantineProvider>
    </AuthProvider>
  );
}

export default App;
