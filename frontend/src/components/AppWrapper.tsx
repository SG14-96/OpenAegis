import React from "react";
import "./AppWrapper.css";
import { Button, Menu } from "antd";
import {
  HomeOutlined,
  BellOutlined,
  FileOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";
import { useAlarmSocket } from "../hooks/useAlarmSocket";
import Shield from "../assets/shield-clean.svg";
import { useNavigate } from "react-router-dom";

const AppWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();
  // Hydrates app-wide alarm state on mount and keeps it live for as long as
  // AppWrapper (i.e. an authenticated route) stays mounted.
  useAlarmSocket();

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
