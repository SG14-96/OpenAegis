import React from "react";
import { Card, Divider, Empty, Space, Tag, Typography } from "antd";
import type { PartitionState, ZoneState } from "../../../types/alarm";

const { Text } = Typography;

export interface PartitionsZonesCardProps {
  loading: boolean;
  partitions: Record<string, PartitionState>;
  zones: Record<string, ZoneState>;
}

const PARTITION_STATE_CONFIG: Record<string, { label: string; color: string }> = {
  unknown: { label: "Unknown", color: "default" },
  ready: { label: "Ready", color: "green" },
  not_ready: { label: "Not Ready", color: "gold" },
  ready_to_force_arm: { label: "Ready (Force Arm)", color: "gold" },
  armed: { label: "Armed", color: "blue" },
  exit_delay: { label: "Exit Delay", color: "gold" },
  entry_delay: { label: "Entry Delay", color: "gold" },
  in_alarm: { label: "In Alarm", color: "red" },
  disarmed: { label: "Disarmed", color: "green" },
  keypad_lockout: { label: "Keypad Lockout", color: "red" },
  busy: { label: "Busy", color: "default" },
};

const ARM_MODE_LABELS: Record<string, string> = {
  stay: "Stay",
  away: "Away",
  stay_no_delay: "Stay (No Delay)",
  away_no_delay: "Away (No Delay)",
};

// Partition/zone ids arrive as string object keys (see types/alarm.ts) —
// sort numerically so "Zone 2" doesn't land after "Zone 10".
function byNumericId<T>(entries: [string, T][]): [string, T][] {
  return [...entries].sort(([a], [b]) => Number(a) - Number(b));
}

export const PartitionsZonesCard: React.FC<PartitionsZonesCardProps> = ({
  loading,
  partitions,
  zones,
}) => {
  const partitionEntries = byNumericId(Object.entries(partitions));
  const zoneEntries = byNumericId(Object.entries(zones));
  const hasData = partitionEntries.length > 0 || zoneEntries.length > 0;

  return (
    <Card loading={loading} title="Partitions & Zones">
      {!hasData ? (
        <Empty
          description="No partition or zone data yet. It appears once a plugin reports panel state."
          image={Empty.PRESENTED_IMAGE_SIMPLE}
        />
      ) : (
        <Space orientation="vertical" size="middle" style={{ width: "100%" }}>
          {partitionEntries.length > 0 && (
            <div>
              <Text type="secondary">Partitions</Text>
              <Space orientation="vertical" size="small" style={{ width: "100%", marginTop: 8 }}>
                {partitionEntries.map(([id, partition]) => {
                  const config = PARTITION_STATE_CONFIG[partition.state] ?? PARTITION_STATE_CONFIG.unknown;
                  return (
                    <div
                      key={id}
                      style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                    >
                      <Text>{partition.label || `Partition ${partition.partition_id}`}</Text>
                      <Space size={4}>
                        {partition.trouble && <Tag color="red">Trouble</Tag>}
                        {partition.is_armed && partition.arm_mode && (
                          <Tag>{ARM_MODE_LABELS[partition.arm_mode] ?? partition.arm_mode}</Tag>
                        )}
                        <Tag color={config.color}>{config.label}</Tag>
                      </Space>
                    </div>
                  );
                })}
              </Space>
            </div>
          )}

          {partitionEntries.length > 0 && zoneEntries.length > 0 && (
            <Divider style={{ margin: "8px 0" }} />
          )}

          {zoneEntries.length > 0 && (
            <div>
              <Text type="secondary">Zones</Text>
              <Space orientation="vertical" size="small" style={{ width: "100%", marginTop: 8 }}>
                {zoneEntries.map(([id, zone]) => (
                  <div
                    key={id}
                    style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}
                  >
                    <Text>{zone.label || `Zone ${zone.zone_id}`}</Text>
                    <Space size={4}>
                      {zone.tampered && <Tag color="red">Tampered</Tag>}
                      {zone.faulted && <Tag color="gold">Faulted</Tag>}
                      {zone.in_alarm && <Tag color="red">Alarm</Tag>}
                      <Tag color={zone.is_open === null ? "default" : zone.is_open ? "orange" : "green"}>
                        {zone.is_open === null ? "Unknown" : zone.is_open ? "Open" : "Closed"}
                      </Tag>
                    </Space>
                  </div>
                ))}
              </Space>
            </div>
          )}
        </Space>
      )}
    </Card>
  );
};
