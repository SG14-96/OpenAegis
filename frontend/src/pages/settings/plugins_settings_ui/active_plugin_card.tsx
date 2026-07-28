import React, { useState } from "react";
import { Badge, Button, Card, Space, Typography } from "antd";
import { ApiOutlined } from "@ant-design/icons";
import { useAppStore } from "../../../store/appStore";
import { unloadPlugin } from "../../../services/plugins";

const { Text } = Typography;

export const ActivePluginCard: React.FC = () => {
  const { activePlugin, setActivePlugin } = useAppStore();
  const [unloading, setUnloading] = useState(false);
  const isLoaded = activePlugin.status === "loaded";

  const handleUnload = async () => {
    setUnloading(true);
    try {
      await unloadPlugin(activePlugin.plugin);
      setActivePlugin({ plugin: "None", status: "not_loaded" });
    } finally {
      setUnloading(false);
    }
  };

  return (
    <Card
      size="small"
      title="Plugin Attached to Alarm"
      style={{ marginBottom: 16 }}
      extra={
        isLoaded ? (
          <Button size="small" danger loading={unloading} onClick={handleUnload}>
            Unload
          </Button>
        ) : null
      }
    >
      <Space orientation="vertical" size="small" style={{ width: "100%" }}>
        <Space>
          <ApiOutlined style={{ fontSize: 18 }} />
          <Badge
            status={isLoaded ? "success" : "default"}
            text={isLoaded ? activePlugin.plugin : "No plugin currently attached"}
          />
        </Space>
        {!isLoaded && (
          <Text type="secondary">
            Select a manufacturer and model below to attach a plugin to the alarm.
          </Text>
        )}
      </Space>
    </Card>
  );
};
