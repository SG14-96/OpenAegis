import React from "react";
import { Card, Typography } from "antd";

const { Text } = Typography;

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
        <Text style={{ fontSize: 14, fontWeight: 500 }}>{model.name}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {model.module_path}
        </Text>
      </div>
    </Card>
  );
};
