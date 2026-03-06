import "./App.css";
import { AuthProvider } from "./context/AuthContext";
import useAuth from "./hooks/useAuth";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/login_page/login_page";
import AccountManagementPage from "./pages/account_management/account_management";
import AppWrapper from "./components/AppWrapper";
import { PrimeReactProvider } from "primereact/api";
import "primereact/resources/themes/lara-light-blue/theme.css";
import HomePage from "./pages/home/home_page";
import NotificationsPage from "./pages/notifications_page/notifications_page";

function HomeRedirect() {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) {
    return <Navigate to="/home" replace />;
  }
  return <Navigate to="/signin" replace />;
}

function App() {

  return (
    <PrimeReactProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<HomeRedirect />} />
            <Route path="/signin" element={
              <LoginPage />
            } />
            <Route path="/account" element={
              <ProtectedRoute>
                <AppWrapper>
                  <AccountManagementPage />
                </AppWrapper>
              </ProtectedRoute>
            } />
            <Route path="/home" element={
              <ProtectedRoute>
                <AppWrapper>
                  <HomePage />
                </AppWrapper>
              </ProtectedRoute>
            } />
            <Route path="/notifications" element={
              <ProtectedRoute>
                <AppWrapper>
                  <NotificationsPage />
                </AppWrapper>
              </ProtectedRoute>
            } />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </PrimeReactProvider>
  );
}

export default App;
