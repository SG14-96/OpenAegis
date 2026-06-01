import React from "react";
import Card from "antd/lib/card";

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
        <span style={{ fontSize: 14, fontWeight: 500 }}>{manufacturer}</span>
        <span style={{ fontSize: 12, color: "#9ca3af" }}>
          {models.length} model(s)
        </span>
      </div>
    </Card>
  );
};
