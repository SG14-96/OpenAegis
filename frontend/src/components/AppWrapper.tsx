import React from "react";
import "./AppWrapper.css";
import { Avatar, Button, Menu } from "antd";
import {
  HomeOutlined,
  BellOutlined,
  FileOutlined,
  SettingOutlined,
} from "@ant-design/icons";
import { useAuth } from "../hooks/useAuth";
import Shield from "../assets/shield-clean.svg";
import { useNavigate } from "react-router-dom";

const AppWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { logout } = useAuth();
  const navigate = useNavigate();

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
      key: "activity",
      label: "Activity",
      icon: <FileOutlined />,
      onClick: () => navigate("/logs"),
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
      <div style={{ display: "flex", alignItems: "center", gap: "1em" }}>
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
        <Avatar
          src="https://primefaces.org/cdn/primereact/images/avatar/amyelsner.png"
          shape="circle"
          style={{ cursor: "pointer" }}
          onClick={() => navigate("/account")}
        />
        <Button style={{ marginInline: "1em" }} onClick={logout} size="small">
          Sign out
        </Button>
      </div>
      {children}
    </div>
  );
};

export default AppWrapper;
