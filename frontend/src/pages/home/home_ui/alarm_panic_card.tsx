import React, { useState } from "react";
import { Card, Row, Col, Space, Button, Modal } from "antd";
import {
  HomeOutlined,
  LockOutlined,
  UnlockOutlined,
  SafetyCertificateOutlined,
  FireOutlined,
  MedicineBoxOutlined,
} from "@ant-design/icons";
import type { AlarmState, TriggerType } from "../../../store/appStore";
import { sendAlarmCommand } from "../../../services/alarmSocket";
import type { AlarmCommand } from "../../../types/alarm";

export interface AlarmPanicCardProps {
  loading: boolean;
  alarmState: AlarmState;
  setAlarmState: (alarmState: AlarmState) => void;
  trigger: (triggerType: TriggerType) => void;
}

type ArmMode = "armed_stay" | "armed_away";

type PendingAction =
  | { kind: "arm"; value: ArmMode }
  | { kind: "panic"; value: TriggerType };

const ARM_CONFIRMATION: Record<ArmMode, { label: string; description: string }> = {
  armed_stay: {
    label: "Arm - Stay",
    description:
      "Perimeter sensors will be active. Interior motion sensors will be bypassed.",
  },
  armed_away: {
    label: "Arm - Away",
    description: "All sensors will be active once the exit delay completes.",
  },
};

const PANIC_CONFIRMATION: Record<TriggerType, { label: string; description: string }> = {
  panic: {
    label: "Panic",
    description: "Emergency dispatch will be notified immediately.",
  },
  fire: {
    label: "Fire",
    description: "The fire department will be notified immediately.",
  },
  auxiliary: {
    label: "Auxiliary",
    description: "Medical assistance will be notified immediately.",
  },
};

export const AlarmPanicCard: React.FC<AlarmPanicCardProps> = ({
  loading,
  alarmState,
  setAlarmState,
  trigger,
}) => {
  const [pendingAction, setPendingAction] = useState<PendingAction | null>(null);

  const confirmation =
    pendingAction?.kind === "arm"
      ? ARM_CONFIRMATION[pendingAction.value]
      : pendingAction?.kind === "panic"
        ? PANIC_CONFIRMATION[pendingAction.value]
        : null;

  const ARM_COMMANDS: Record<ArmMode, AlarmCommand> = {
    armed_stay: "arm_stay",
    armed_away: "arm_away",
  };

  const handleConfirm = () => {
    // Optimistically reflect the action locally; the real confirmation
    // (and any correction, e.g. panel rejects the arm) arrives moments
    // later as a websocket event and overwrites this via the store.
    if (pendingAction?.kind === "arm") {
      setAlarmState(pendingAction.value);
      sendAlarmCommand({ command: ARM_COMMANDS[pendingAction.value] });
    } else if (pendingAction?.kind === "panic") {
      trigger(pendingAction.value);
      sendAlarmCommand({ command: "panic", panic_type: pendingAction.value });
    }
    setPendingAction(null);
  };

  const handleCancel = () => setPendingAction(null);

  const handleDisarm = () => {
    setAlarmState("disarmed");
    sendAlarmCommand({ command: "disarm" });
  };

  return (
    <Card loading={loading} title="Alarm & Panic Modes">
      <Row gutter={16}>
        <Col span={12}>
          <Space orientation="vertical" style={{ width: "100%" }}>
            <Button
              block
              icon={<HomeOutlined />}
              type={alarmState === "armed_stay" ? "primary" : "default"}
              onClick={() => setPendingAction({ kind: "arm", value: "armed_stay" })}
            >
              Arm - Stay
            </Button>
            <Button
              block
              icon={<LockOutlined />}
              type={alarmState === "armed_away" ? "primary" : "default"}
              onClick={() => setPendingAction({ kind: "arm", value: "armed_away" })}
            >
              Arm - Away
            </Button>
            <Button
              block
              icon={<UnlockOutlined />}
              type={alarmState === "disarmed" ? "primary" : "default"}
              onClick={handleDisarm}
            >
              Disarm
            </Button>
          </Space>
        </Col>
        <Col span={12}>
          <Space orientation="vertical" style={{ width: "100%" }}>
            <Button
              block
              color="blue"
              variant="solid"
              icon={<SafetyCertificateOutlined />}
              onClick={() => setPendingAction({ kind: "panic", value: "panic" })}
            >
              Panic
            </Button>
            <Button
              block
              danger
              type="primary"
              icon={<FireOutlined />}
              onClick={() => setPendingAction({ kind: "panic", value: "fire" })}
            >
              Fire
            </Button>
            <Button
              block
              color="yellow"
              variant="solid"
              icon={<MedicineBoxOutlined />}
              onClick={() => setPendingAction({ kind: "panic", value: "auxiliary" })}
            >
              Auxiliary
            </Button>
          </Space>
        </Col>
      </Row>

      <Modal
        open={pendingAction !== null}
        title={confirmation ? `Confirm ${confirmation.label}` : ""}
        onOk={handleConfirm}
        onCancel={handleCancel}
        okText="Confirm"
        cancelText="Cancel"
        okType={pendingAction?.kind === "panic" ? "danger" : "primary"}
      >
        {confirmation?.description}
      </Modal>
    </Card>
  );
};
