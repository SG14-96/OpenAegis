import React from "react";
import { Card, Space, Badge, Typography } from "antd";
import { CloudServerOutlined } from "@ant-design/icons";

const { Text } = Typography;

export interface ServerStatusCardProps {
  loading: boolean;
}

export const ServerStatusCard: React.FC<ServerStatusCardProps> = ({ loading }) => {
  return (
    <Card loading={loading} title="OpenAegis Server">
      <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
        <Space>
          <CloudServerOutlined style={{ fontSize: 18 }} />
          <Badge status="success" text="Online" />
        </Space>
        <div>
          <Text type="secondary">Version</Text>
          <br />
          <Text>v0.1.0</Text>
        </div>
        <div>
          <Text type="secondary">Uptime</Text>
          <br />
          <Text>3d 4h 12m</Text>
        </div>
      </Space>
    </Card>
  );
};
