import "./App.css";
import { AuthProvider } from "./context/AuthContext";
import useAuth from "./hooks/useAuth";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/login_page/login_page";
import { AccountManagementPage } from "./pages/account_management/account_management";

import { PrimeReactProvider } from 'primereact/api';


function HomeRedirect() {
  const { isAuthenticated } = useAuth();
  if (isAuthenticated) {
    return <Navigate to="/account" replace />;
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
            <Route path="/signin" element={<LoginPage />} />
            <Route path="/account" element={
              <ProtectedRoute>
                <AccountManagementPage />
              </ProtectedRoute>
            } />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </PrimeReactProvider>
  );
}

export default App;
