import React, { useEffect, useState } from "react";
import { AutoComplete, Button, Divider, Input, Select, Typography } from "antd";
import { LeftOutlined, ReloadOutlined, RightOutlined } from "@ant-design/icons";
import { listSerialPorts, type SerialPortInfo } from "../../../services/hardware";
import type { PluginSetupValues } from "../../../services/plugins";

const { Text, Title } = Typography;

export type StepValues = {
  option?: string | number;
  input?: string;
};

// Flattens per-step form state into the plain values a plugin's on_load
// reads (setup_values["<step index>"]). Steps with nothing to answer
// (instruction-only) are omitted.
function toSetupValues(values: Record<number, StepValues>): PluginSetupValues {
  const out: PluginSetupValues = {};
  for (const [index, v] of Object.entries(values)) {
    const value = v.option ?? v.input?.trim();
    if (value !== undefined && value !== "") out[index] = value;
  }
  return out;
}

function stepIsComplete(step: PluginManifestStep, values: StepValues): boolean {
  if (step.options && step.options.length > 0 && values.option === undefined)
    return false;
  if (step.input && !values.input?.trim()) return false;
  return true;
}

export const PluginSetupSubview: React.FC<{
  model: PluginModel;
  loading?: boolean;
  onInstall: (values: PluginSetupValues) => void;
  onClose: () => void;
}> = ({ model, loading = false, onInstall, onClose }) => {
  const steps = model.manifest?.connectionSetupSteps || [];
  const [stepValues, setStepValues] = useState<Record<number, StepValues>>({});
  const [showErrors, setShowErrors] = useState(false);

  const incompleteIndexes = steps.reduce<number[]>((acc, step, i) => {
    if (!stepIsComplete(step, stepValues[i] ?? {})) acc.push(i);
    return acc;
  }, []);

  const handleChange = (index: number, patch: Partial<StepValues>) => {
    setStepValues((prev) => ({
      ...prev,
      [index]: { ...prev[index], ...patch },
    }));
  };

  const handleInitPlugin = () => {
    if (incompleteIndexes.length > 0) {
      setShowErrors(true);
      return;
    }
    onInstall(toSetupValues(stepValues));
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", minHeight: 320 }}>
      {steps.length > 0 ? (
        steps.map((step, index) => (
          <React.Fragment key={index}>
            <SetupStep
              step={step}
              values={stepValues[index] ?? {}}
              error={
                showErrors && !stepIsComplete(step, stepValues[index] ?? {})
              }
              onChange={(patch) => handleChange(index, patch)}
            />
            {index < steps.length - 1 && (
              <Divider style={{ borderWidth: 2, margin: "20px 0" }} />
            )}
          </React.Fragment>
        ))
      ) : (
        <Text type="secondary">No setup steps available.</Text>
      )}

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginTop: "auto",
          paddingTop: 20,
        }}
      >
        <Button icon={<LeftOutlined />} onClick={onClose}>
          Cancel
        </Button>
        <Button loading={loading} onClick={handleInitPlugin} type="primary">
          Initialize <RightOutlined />
        </Button>
      </div>
    </div>
  );
};

const SetupStep: React.FC<{
  step: PluginManifestStep;
  values: StepValues;
  error: boolean;
  onChange: (patch: Partial<StepValues>) => void;
}> = ({ step, values, error, onChange }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
    <Title level={5} style={{ margin: 0 }}>
      {step.step}
    </Title>
    <Text type="secondary" style={{ fontSize: 13 }}>
      {step.details}
    </Text>

    {step.options && step.options.length > 0 && (
      <>
        <Select
          style={{ width: "100%", marginTop: 4 }}
          placeholder="Select an option"
          status={error && values.option === undefined ? "error" : undefined}
          value={values.option}
          options={step.options.map((o) => ({
            label: o.label,
            value: o.value,
          }))}
          onChange={(val) => onChange({ option: val })}
        />
        {error && values.option === undefined && (
          <Text type="danger" style={{ fontSize: 12 }}>
            Please select an option.
          </Text>
        )}
      </>
    )}

    {step.input?.type === "serial_port" && (
      <SerialPortInput
        placeholder={step.input.placeholder}
        value={values.input}
        error={error && !values.input?.trim()}
        onChange={(input) => onChange({ input })}
      />
    )}

    {step.input && step.input.type !== "serial_port" && (
      <>
        <Input
          style={{ marginTop: 4 }}
          type={step.input.type === "password" ? "password" : "text"}
          placeholder={step.input.placeholder}
          status={error && !values.input?.trim() ? "error" : undefined}
          value={values.input ?? ""}
          onChange={(e) => onChange({ input: e.target.value })}
        />
        {error && !values.input?.trim() && (
          <Text type="danger" style={{ fontSize: 12 }}>
            This field is required.
          </Text>
        )}
      </>
    )}
  </div>
);

// Lets the user pick a serial port the backend can see, or type a path for
// one it can't enumerate (e.g. a symlinked /dev/serial/by-id/... entry).
const SerialPortInput: React.FC<{
  placeholder: string;
  value: string | undefined;
  error: boolean;
  onChange: (value: string) => void;
}> = ({ placeholder, value, error, onChange }) => {
  const [ports, setPorts] = useState<SerialPortInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  const fetchPorts = () => {
    listSerialPorts()
      .then((result) => {
        setPorts(result);
        setLoadError(null);
      })
      .catch(() => setLoadError("Couldn't list serial ports on the server."))
      .finally(() => setLoading(false));
  };

  const refresh = () => {
    setLoading(true);
    fetchPorts();
  };

  useEffect(fetchPorts, []);

  return (
    <>
      <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
        <AutoComplete
          style={{ flex: 1 }}
          placeholder={placeholder}
          status={error ? "error" : undefined}
          value={value}
          onChange={onChange}
          options={ports.map((p) => ({
            value: p.device,
            label: p.description && p.description !== "n/a" ? `${p.device} — ${p.description}` : p.device,
          }))}
          filterOption={(input, option) =>
            String(option?.label ?? "").toLowerCase().includes(input.toLowerCase())
          }
        />
        <Button icon={<ReloadOutlined />} loading={loading} onClick={refresh} aria-label="Refresh ports" />
      </div>
      {!loading && !loadError && ports.length === 0 && (
        <Text type="secondary" style={{ fontSize: 12 }}>
          No serial ports detected on the server. Check the USB connection, or type the path manually.
        </Text>
      )}
      {loadError && (
        <Text type="warning" style={{ fontSize: 12 }}>
          {loadError}
        </Text>
      )}
      {error && (
        <Text type="danger" style={{ fontSize: 12 }}>
          Please select or enter a serial port.
        </Text>
      )}
    </>
  );
};
