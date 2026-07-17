import React from "react";
import { Card, Divider, Image, Tag, Space, Typography } from "antd";
import type { AlarmState, TriggerType } from "../../../store/appStore";

import greenLock from "../../../assets/icons/100x100/green-lock-open-100.svg";
import yellowLock from "../../../assets/icons/100x100/yellow-lock-100.svg";
import redLock from "../../../assets/icons/100x100/red-lock-100.svg";

const { Paragraph } = Typography;

const ZONES = ["Front Door", "Garage", "Hallway Motion"];

const TRIGGER_MESSAGES: Record<TriggerType, string> = {
  panic: "Panic alarm activated. Emergency dispatch notified.",
  fire: "Fire alarm activated. Fire department notified.",
  auxiliary: "Auxiliary alarm activated. Medical assistance notified.",
};

const ALARM_CONFIG: Record<
  AlarmState,
  { label: string; icon: string; tagColor: string; message?: string }
> = {
  disarmed: {
    label: "Disarmed",
    icon: greenLock,
    tagColor: "green",
  },
  armed_stay: {
    label: "Armed - Stay",
    icon: yellowLock,
    tagColor: "gold",
    message: "Perimeter sensors active. Interior motion sensors bypassed.",
  },
  armed_away: {
    label: "Armed - Away",
    icon: redLock,
    tagColor: "red",
    message: "All sensors active. Exit delay complete.",
  },
  triggered: {
    label: "Triggered",
    icon: redLock,
    tagColor: "red",
    message: "Intrusion detected at Front Door.",
  },
};

export interface AlarmStatusCardProps {
  loading: boolean;
  alarmState: AlarmState;
  triggerType: TriggerType;
}

export const AlarmStatusCard: React.FC<AlarmStatusCardProps> = ({
  loading,
  alarmState,
  triggerType,
}) => {
  const alarmConfig = ALARM_CONFIG[alarmState];
  const statusMessage =
    alarmState === "triggered"
      ? TRIGGER_MESSAGES[triggerType]
      : alarmConfig.message;

  return (
    <Card loading={loading} title="Alarm Status">
      <div style={{ textAlign: "center" }}>
        <Image
          src={alarmConfig.icon}
          alt={alarmConfig.label}
          preview={false}
          width={100}
        />
        <Divider style={{ margin: "16px 0" }} />
        <Tag
          color={alarmConfig.tagColor}
          style={{ fontSize: 14, padding: "4px 12px" }}
        >
          {alarmConfig.label}
        </Tag>
        {statusMessage && (
          <Paragraph type="secondary" style={{ marginTop: 12, marginBottom: 0 }}>
            {statusMessage}
          </Paragraph>
        )}
        {alarmState !== "disarmed" && (
          <div style={{ marginTop: 12 }}>
            <Space size={[4, 8]} wrap style={{ justifyContent: "center" }}>
              {ZONES.map((zone) => (
                <Tag key={zone} color={alarmState === "triggered" ? "red" : "blue"}>
                  {zone}
                </Tag>
              ))}
            </Space>
          </div>
        )}
      </div>
    </Card>
  );
};
