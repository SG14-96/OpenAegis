import React from "react";
import { Tabs, Typography } from "antd";
import { AccountTab, OtherAccountsTab, PluginsTab } from "./tab_contents";

export const SettingsPage: React.FC = () => {
  const tabItems = [
    { key: "account", label: "My Account", children: <AccountTab /> },
    {
      key: "other-accounts",
      label: "Other Accounts",
      children: <OtherAccountsTab />,
    },
    { key: "plugins", label: "Plugins", children: <PluginsTab /> },
  ];

  return (
    <div className="settings-page p-6" style={{ marginTop: "15px" }}>
      <Typography.Title level={1}>Settings</Typography.Title>
      <Tabs items={tabItems} />
    </div>
  );
};
