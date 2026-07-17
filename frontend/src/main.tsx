import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ConfigProvider } from "antd";
import "./index.css";
import "./styles/accountManagement.css";
import "./styles/pluginPage.css";
import App from "./App.tsx";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <ConfigProvider theme={{ token: {} }}>
      <App />
    </ConfigProvider>
  </StrictMode>
);
