import type React from "react";
import useAuth from "../../hooks/useAuth";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Button, Input } from "antd";

import "./login_page.css";

export function DemoAuthControls() {
  const { isAuthenticated, user, login, logout } = useAuth();
  const [usernameVal, setUsernameVal] = useState("");
  const [passwordVal, setPasswordVal] = useState("");

  const handleLogin = async () => {
    try {
      await login(usernameVal, passwordVal);
    } catch (e) {
      console.error("Login failed", e);
      alert("Login failed: " + e);
    }
  };

  return (
    <Card
      title="OpenAegis Security System"
      style={{ width: "400px", margin: "0 auto", marginTop: "50px" }}
    >
      <div style={{ marginTop: 12 }}>
        {isAuthenticated ? (
          <>
            <div>Signed in as: {user?.username}</div>
            <button onClick={() => logout()}>Sign out</button>
          </>
        ) : (
          <div>
            <p>Enter your credentials to sign in.</p>
            <div className="input-field">
              <label htmlFor="username">Username</label>
              <Input
                id="username"
                value={usernameVal}
                onChange={(e) => setUsernameVal(e.target.value)}
                style={{ width: "100%" }}
              />
            </div>
            <div className="input-field" style={{ marginTop: "1em" }}>
              <label htmlFor="password">Password</label>
              <Input.Password
                id="password"
                value={passwordVal}
                onChange={(e) => setPasswordVal(e.target.value)}
                style={{ width: "100%" }}
              />
            </div>
            <Button
              style={{ marginTop: "1em" }}
              type="primary"
              onClick={handleLogin}
            >
              Sign in
            </Button>
          </div>
        )}
      </div>
    </Card>
  );
}

const LoginPage = (): React.ReactElement => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/account", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  return (
    <div className="signin-screen-container">
      <DemoAuthControls />
    </div>
  );
};

export default LoginPage;
