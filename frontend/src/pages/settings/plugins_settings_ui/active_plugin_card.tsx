import React, { useState } from "react";
import { Alert, Badge, Button, Card, Popconfirm, Space, Typography } from "antd";
import { ApiOutlined } from "@ant-design/icons";
import { useAppStore } from "../../../store/appStore";
import { detachPlugin } from "../../../services/plugins";

const { Text } = Typography;

export const ActivePluginCard: React.FC = () => {
  const { activePlugin, setActivePlugin } = useAppStore();
  const [unloading, setUnloading] = useState(false);
  const [unloadError, setUnloadError] = useState<string | null>(null);
  const isLoaded = activePlugin.status === "loaded";

  const handleUnload = async () => {
    setUnloading(true);
    setUnloadError(null);
    try {
      await detachPlugin();
      setActivePlugin({ plugin: "None", status: "not_loaded" });
    } catch {
      setUnloadError("Failed to unload the plugin.");
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
          <Popconfirm
            title="Unload plugin?"
            description="This disconnects from the panel and removes its saved setup."
            okText="Unload"
            okButtonProps={{ danger: true }}
            onConfirm={handleUnload}
          >
            <Button size="small" danger loading={unloading}>
              Unload
            </Button>
          </Popconfirm>
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
        {unloadError && <Alert type="error" title={unloadError} showIcon />}
        {!isLoaded && (
          <Text type="secondary">
            Select a manufacturer and model below to attach a plugin to the alarm.
          </Text>
        )}
      </Space>
    </Card>
  );
};
