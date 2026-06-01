import React from "react";
import Card from "antd/lib/card";

interface PluginModelCardProps {
  model: PluginModel;
  onClick: (model: PluginModel) => void;
}

export const PluginModelCard: React.FC<PluginModelCardProps> = ({
  model,
  onClick,
}) => {
  return (
    <Card hoverable role="button" onClick={() => onClick(model)} variant="outlined">
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
        }}
      >
        <span style={{ fontSize: 14, fontWeight: 500 }}>{model.name}</span>
        <span style={{ fontSize: 12, color: "#9ca3af" }}>{model.module_path}</span>
      </div>
    </Card>
  );
};
