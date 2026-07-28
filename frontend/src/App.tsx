import "./App.css";
import { useAppStore } from "./store/appStore";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthGuard } from "./components/AuthGuard";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/login_page/login_page";
import AppWrapper from "./components/AppWrapper";
import HomePage from "./pages/home/home_page";
import NotificationsPage from "./pages/notifications_page/notifications_page";
import { SettingsPage } from "./pages/settings/settings_page";

function HomeRedirect() {
  const isAuthenticated = useAppStore((s) => !!s.accessToken);
  if (isAuthenticated) {
    return <Navigate to="/home" replace />;
  }
  return <Navigate to="/signin" replace />;
}

function App() {
  return (
    <BrowserRouter>
      <AuthGuard />
      <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/signin" element={<LoginPage />} />
          <Route
            path="/home"
            element={
              <ProtectedRoute>
                <AppWrapper>
                  <HomePage />
                </AppWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/notifications"
            element={
              <ProtectedRoute>
                <AppWrapper>
                  <NotificationsPage />
                </AppWrapper>
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <AppWrapper>
                  <SettingsPage />
                </AppWrapper>
              </ProtectedRoute>
            }
          />
        </Routes>
    </BrowserRouter>
  );
}

export default App;
