import React from "react";
import { Card, Typography } from "antd";

const { Text } = Typography;

export interface PluginBrandCardProps {
  manufacturer: string;
  models: PluginModel[];
  onClick: (manufacturer: string) => void;
}

export const PluginBrandCard: React.FC<PluginBrandCardProps> = ({
  manufacturer,
  models,
  onClick,
}) => {
  return (
    <Card
      hoverable
      role="button"
      onClick={() => {
        onClick(manufacturer);
      }}
      variant="outlined"
    >
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: 8,
        }}
      >
        <Text style={{ fontSize: 14, fontWeight: 500 }}>{manufacturer}</Text>
        <Text type="secondary" style={{ fontSize: 12 }}>
          {models.length} model(s)
        </Text>
      </div>
    </Card>
  );
};
