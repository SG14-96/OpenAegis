import React, { useState } from "react";
import { Typography, Row, Col } from "antd";
import { useAppStore } from "../../store/appStore";
import { AlarmStatusCard } from "./home_ui/alarm_status_card";
import { AlarmPanicCard } from "./home_ui/alarm_panic_card";
import { ServerStatusCard } from "./home_ui/server_status_card";
import { PluginConnectionCard } from "./home_ui/plugin_connection_card";
import { PartitionsZonesCard } from "./home_ui/partitions_zones_card";

const { Title } = Typography;

const HomePage = () => {
  const { activePlugin, alarmState, triggerType, setAlarmState, trigger, partitions, zones } =
    useAppStore();
  const [isLoadingData] = useState(false);

  return (
    <div>
      <Title>Welcome to OpenAegis</Title>
      <Row gutter={[16, 16]} align="top">
        <Col span={18} offset={3}>
          <AlarmStatusCard
            loading={isLoadingData}
            alarmState={alarmState}
            triggerType={triggerType}
          />
        </Col>

        <Col span={18} offset={3}>
          <AlarmPanicCard
            loading={isLoadingData}
            alarmState={alarmState}
            setAlarmState={setAlarmState}
            trigger={trigger}
          />
        </Col>

        <Col span={18} offset={3}>
          <ServerStatusCard loading={isLoadingData} />
        </Col>

        <Col span={18} offset={3}>
          <PluginConnectionCard loading={isLoadingData} activePlugin={activePlugin} />
        </Col>

        <Col span={18} offset={3}>
          <PartitionsZonesCard loading={isLoadingData} partitions={partitions} zones={zones} />
        </Col>
      </Row>
    </div>
  );
};

export default HomePage;
