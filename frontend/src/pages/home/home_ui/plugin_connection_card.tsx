import React from "react";
import { Card, Space, Badge, Typography } from "antd";
import { ApiOutlined } from "@ant-design/icons";

const { Text } = Typography;

export interface PluginConnectionCardProps {
  loading: boolean;
  activePlugin: {
    plugin: string;
    status: "loaded" | "not_loaded";
  };
}

export const PluginConnectionCard: React.FC<PluginConnectionCardProps> = ({
  loading,
  activePlugin,
}) => {
  const isPluginConnected = activePlugin.status === "loaded";

  return (
    <Card loading={loading} title="Third Party Connections">
      <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
        <Space>
          <ApiOutlined style={{ fontSize: 18 }} />
          <Badge
            status={isPluginConnected ? "success" : "default"}
            text={isPluginConnected ? activePlugin.plugin : "No plugin connected"}
          />
        </Space>
        {!isPluginConnected && (
          <Text type="secondary">
            Connect a plugin from Settings to see live device data here.
          </Text>
        )}
      </Space>
    </Card>
  );
};
