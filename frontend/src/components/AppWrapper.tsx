import React from "react";
import "./AppWrapper.css";
import { Menubar } from "primereact/menubar";
import { Avatar } from "primereact/avatar";
import { useAuth } from "../hooks/useAuth";
import { Button } from "primereact/button";
import Shield from "../assets/shield-clean.svg";
import { useNavigate } from "react-router-dom";

const AppWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const { logout } = useAuth();
    const navigate = useNavigate();
    const items = [
        {
            label: "Home",
            icon: "pi pi-home",
            command: () => {
                navigate("/");
            },
        },
        {
            label: "Notifications",
            icon: "pi pi-bell",
            command: () => {
                navigate("/notifications");
            },
        },
        {
            label: "Activity",
            icon: "pi pi-file",
            command: () => {
                navigate("/logs");
            },
        },
        {
            label: "Settings",
            icon: "pi pi-cog",
            command: () => {
                navigate("/settings");
            },
        }
    ]
    const start = <img alt="logo" src={Shield} height="40" className="mr-2"></img>;
    const end = (
        <div className="flex align-items-center gap-2">
            <Avatar image="https://primefaces.org/cdn/primereact/images/avatar/amyelsner.png" shape="circle" role="button" onClick={() => {
                navigate("/account");
            }} />
            <Button style={{ marginInline: "1em" }} label="Sign out" onClick={logout} size="small" />
        </div>
    );
    return (
        <div className="app-wrapper">
            <Menubar style={{ borderRadius: '15px' }} model={items} start={start} end={end} />
            {children}
        </div>
    );
};

export default AppWrapper;