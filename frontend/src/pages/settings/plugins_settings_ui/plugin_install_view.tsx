import React, { useState } from "react";
import { Button, Divider, Input, Select, Typography } from "antd";
import { LeftOutlined, RightOutlined } from "@ant-design/icons";

const { Text, Title } = Typography;

export type StepValues = {
  option?: string | number;
  input?: string;
};

function stepIsComplete(step: PluginManifestStep, values: StepValues): boolean {
  if (step.options && step.options.length > 0 && values.option === undefined)
    return false;
  if (step.input && !values.input?.trim()) return false;
  return true;
}

export const PluginSetupSubview: React.FC<{
  model: PluginModel;
  loading?: boolean;
  onInstall: (values: Record<number, StepValues>) => void;
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
    onInstall(stepValues);
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

    {step.input && (
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
