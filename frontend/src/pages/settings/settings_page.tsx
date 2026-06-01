import React, { useState } from "react";
import { Tabs } from "antd";
import { InformationTab, PluginsTab } from "./tab_contents";

const tabItems = [
  { label: "Information", key: "1", children: <InformationTab /> },
  { label: "Plugins", key: "2", children: <PluginsTab /> },
];

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("1");

  return (
    <div className="settings-page p-6" style={{ marginTop: "15px" }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        type="card"
        items={tabItems}
      />
    </div>
  );
};
