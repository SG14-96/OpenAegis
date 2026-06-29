import React from "react";
import { InformationTab } from "./tab_contents";

export const SettingsPage: React.FC = () => {
  return (
    <div className="settings-page p-6" style={{ marginTop: "15px" }}>
      <InformationTab />
    </div>
  );
};
