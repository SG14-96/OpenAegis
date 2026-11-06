import React from "react";
import { Alert, Card, Divider, Image, Tag, Space, Typography } from "antd";
import type { AlarmState, TriggerType } from "../../../store/appStore";
import type { PartitionState, ZoneState } from "../../../types/alarm";
import { troubleLabel } from "../../../services/alarmSocket";

import greenLock from "../../../assets/icons/100x100/green-lock-open-100.svg";
import yellowLock from "../../../assets/icons/100x100/yellow-lock-100.svg";
import redLock from "../../../assets/icons/100x100/red-lock-100.svg";

const { Paragraph, Text } = Typography;

const TRIGGER_MESSAGES: Record<TriggerType, string> = {
  panic: "Panic alarm activated.",
  fire: "Fire alarm activated.",
  auxiliary: "Auxiliary (medical) alarm activated.",
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
    message: "Perimeter armed. Interior zones are bypassed while you're home.",
  },
  armed_away: {
    label: "Armed - Away",
    icon: redLock,
    tagColor: "red",
    message: "All zones armed.",
  },
  triggered: {
    label: "Triggered",
    icon: redLock,
    tagColor: "red",
  },
};

// Transitional partition states worth calling out over the generic
// armed/disarmed message.
const PARTITION_STATE_MESSAGES: Record<string, string> = {
  exit_delay: "Exit delay in progress — leave now.",
  entry_delay: "Entry delay in progress — disarm now.",
  not_ready: "Not ready to arm. Close or bypass the open zones below.",
  ready_to_force_arm: "Ready to force arm — open zones will be bypassed.",
  keypad_lockout: "Keypad locked out after too many invalid codes.",
  busy: "Panel is busy.",
};

function zoneName(zone: ZoneState): string {
  return zone.label || `Zone ${zone.zone_id}`;
}

export interface AlarmStatusCardProps {
  loading: boolean;
  alarmState: AlarmState;
  triggerType: TriggerType;
  // The primary partition (partition 1), if the panel has reported it.
  partition: PartitionState | undefined;
  zones: Record<string, ZoneState>;
  troubles: Record<string, true>;
}

export const AlarmStatusCard: React.FC<AlarmStatusCardProps> = ({
  loading,
  alarmState,
  triggerType,
  partition,
  zones,
  troubles,
}) => {
  const alarmConfig = ALARM_CONFIG[alarmState];
  const allZones = Object.values(zones).sort((a, b) => a.zone_id - b.zone_id);
  const alarmZones = allZones.filter((z) => z.in_alarm);
  const openZones = allZones.filter((z) => z.is_open);

  let statusMessage: string | undefined;
  if (alarmState === "triggered") {
    statusMessage =
      alarmZones.length > 0
        ? `Alarm in ${alarmZones.map(zoneName).join(", ")}.`
        : TRIGGER_MESSAGES[triggerType];
  } else {
    statusMessage = (partition && PARTITION_STATE_MESSAGES[partition.state]) ?? alarmConfig.message;
  }

  // Alarm zones while triggered; otherwise open zones, which are what
  // block arming (disarmed) or will trip the alarm (armed).
  const highlightedZones = alarmState === "triggered" ? alarmZones : openZones;
  const troubleTypes = Object.keys(troubles);

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
        {highlightedZones.length > 0 && (
          <div style={{ marginTop: 12 }}>
            <Text type="secondary" style={{ display: "block", marginBottom: 4 }}>
              {alarmState === "triggered" ? "Zones in alarm" : "Open zones"}
            </Text>
            <Space size={[4, 8]} wrap style={{ justifyContent: "center" }}>
              {highlightedZones.map((zone) => (
                <Tag key={zone.zone_id} color={alarmState === "triggered" ? "red" : "orange"}>
                  {zoneName(zone)}
                </Tag>
              ))}
            </Space>
          </div>
        )}
        {troubleTypes.length > 0 && (
          <Alert
            type="warning"
            showIcon
            style={{ marginTop: 16, textAlign: "left" }}
            title="System trouble"
            description={troubleTypes.map(troubleLabel).join(", ")}
          />
        )}
      </div>
    </Card>
  );
};
