import React, { useEffect } from "react";
import "./AppWrapper.css";
import { Button, Menu, message } from "antd";
import {
  HomeOutlined,
  BellOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";
import { useAlarmSocket } from "../hooks/useAlarmSocket";
import Shield from "../assets/shield-clean.svg";
import { useNavigate } from "react-router-dom";
import { useAppStore } from "../store/appStore";

const AppWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  // Hydrates app-wide alarm state on mount and keeps it live for as long as
  // AppWrapper (i.e. an authenticated route) stays mounted.
  useAlarmSocket();

  // Surfaces panel/backend notices (rejected commands, troubles, plugin
  // errors) pushed into the store by the alarm websocket handler.
  const [messageApi, messageContext] = message.useMessage();
  const panelNotice = useAppStore((s) => s.panelNotice);
  useEffect(() => {
    if (panelNotice) messageApi.open({ type: panelNotice.level, content: panelNotice.text, duration: 5 });
  }, [panelNotice, messageApi]);

  const menuItems = [
    {
      key: "home",
      label: "Home",
      icon: <HomeOutlined />,
      onClick: () => navigate("/"),
    },
    {
      key: "notifications",
      label: "Notifications",
      icon: <BellOutlined />,
      onClick: () => navigate("/notifications"),
    },
    {
      key: "settings",
      label: "Settings",
      icon: <SettingOutlined />,
      onClick: () => navigate("/settings"),
    },
  ];

  return (
    <div className="app-wrapper">
      {messageContext}
      <div
        className="app-wrapper-nav"
        style={{ display: "flex", alignItems: "center", gap: "1em" }}
      >
        <img
          alt="logo"
          src={Shield}
          height="40"
          style={{ marginRight: "0.5em" }}
        />
        <Menu
          mode="horizontal"
          items={menuItems}
          style={{ flex: 1, border: "none" }}
        />
        <Button style={{ marginInline: "1em" }} onClick={logout} size="small">
          Sign out
        </Button>
      </div>
      <div className="app-wrapper-content">{children}</div>
    </div>
  );
};

export default AppWrapper;
