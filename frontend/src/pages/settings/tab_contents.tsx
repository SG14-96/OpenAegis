import React, { useEffect, useState } from "react";
import {
  Alert,
  Breadcrumb,
  Button,
  Col,
  Descriptions,
  List,
  Modal,
  Row,
  Spin,
  Tag,
  Typography,
} from "antd";
import { PluginBrandCard } from "./plugins_settings_ui/plugin_brand_card";
import { PluginModelCard } from "./plugins_settings_ui/plugin_model_card";
import { PluginSetupSubview } from "./plugins_settings_ui/plugin_install_view";
import type { StepValues } from "./plugins_settings_ui/plugin_install_view";
import { listAvailablePlugins, loadPlugin } from "../../services/plugins";
import { getCurrentUser } from "../../services/user";
import { useAppStore } from "../../store/appStore";

type AsyncState<T> = {
  data: T | null;
  isLoading: boolean;
  error: string | null;
};

function asyncInit<T>(): AsyncState<T> {
  return { data: null, isLoading: false, error: null };
}

export const InformationTab: React.FC = () => {
  const [userInfo, setUserInfo] = useState<AsyncState<User>>(asyncInit);

  useEffect(() => {
    setUserInfo({ data: null, isLoading: true, error: null });
    getCurrentUser()
      .then((data) => setUserInfo({ data, isLoading: false, error: null }))
      .catch((err) =>
        setUserInfo({
          data: null,
          isLoading: false,
          error: err?.message ?? "Failed to load user info",
        })
      );
  }, []);

  if (userInfo.isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spin size="large" />
      </div>
    );
  }

  if (userInfo.error) {
    return <Alert type="error" title={userInfo.error} />;
  }

  if (!userInfo.data) return null;

  const u = userInfo.data;
  const rows = [
    { label: "Username", value: u.username },
    { label: "Email", value: u.email },
    { label: "Full Name", value: `${u.full_name} ${u.last_name}`.trim() },
    { label: "Admin", value: u.is_superuser ? "Yes" : "No" },
  ];

  return (
    <div>
      <Typography.Title level={4}>User Information</Typography.Title>
      <List
        bordered
        dataSource={rows}
        renderItem={(item) => (
          <List.Item>
            <Typography.Text strong>{item.label}:</Typography.Text>&nbsp;
            {item.value}
          </List.Item>
        )}
      />
    </div>
  );
};

export const PluginsTab: React.FC = () => {
  const [plugins, setPlugins] =
    useState<AsyncState<PluginManufacturer[]>>(asyncInit);
  const [selectedManufacturer, setSelectedManufacturer] =
    React.useState<PluginManufacturer | null>(null);
  const [selectedModel, setSelectedModel] = React.useState<PluginModel | null>(
    null
  );
  const [setupModalVisible, setSetupModalVisible] = React.useState(false);
  const [showPluginInstallView, setShowPluginInstallView] = useState(false);
  const [installLoading, setInstallLoading] = useState(false);
  const [installStatus, setInstallStatus] = useState<
    "idle" | "success" | "failure"
  >("idle");
  const [installError, setInstallError] = useState<string | null>(null);

  const { activePlugin, setActivePlugin } = useAppStore();
  const [isCurrentPluginActive, setIsCurrentPluginActive] = useState(false);

  useEffect(() => {
    setPlugins({ data: null, isLoading: true, error: null });
    listAvailablePlugins()
      .then((data) => setPlugins({ data, isLoading: false, error: null }))
      .catch((err) =>
        setPlugins({
          data: null,
          isLoading: false,
          error: err?.message ?? "Failed to load plugins",
        })
      );
  }, []);

  const handleInstall = async (values: Record<number, StepValues>) => {
    if (!selectedModel) return;
    setInstallLoading(true);
    setInstallStatus("idle");
    try {
      const serialized = Object.fromEntries(
        Object.entries(values).map(([k, v]) => [k, v])
      );
      await loadPlugin(selectedModel.module_path, serialized).then((data) => {
        setActivePlugin(data);
        setInstallStatus("success");
        setShowPluginInstallView(false);
      });
    } catch (err) {
      setInstallStatus("failure");
      setInstallError(
        err instanceof Error ? err.message : "Failed to load plugin"
      );
    } finally {
      setInstallLoading(false);
    }
  };

  useEffect(() => {
    if (!activePlugin || !selectedModel) {
      setIsCurrentPluginActive(false);
      return;
    }
    setIsCurrentPluginActive(
      activePlugin.plugin === selectedModel.manifest?.name &&
        activePlugin.status === "loaded"
    );
  }, [activePlugin, selectedModel]);

  if (plugins.isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spin size="large" />
      </div>
    );
  }

  if (plugins.error) {
    return <Alert type="error" title={plugins.error} />;
  }

  if (!plugins.data || plugins.data.length === 0) {
    return <Alert type="info" title="No plugins available." />;
  }

  const breadcrumbItems = [
    {
      title: selectedManufacturer ? (
        <a
          onClick={() => {
            setSelectedManufacturer(null);
            setSelectedModel(null);
          }}
        >
          Manufacturers
        </a>
      ) : (
        "Manufacturers"
      ),
    },
    ...(selectedManufacturer
      ? [
          {
            title: selectedModel ? (
              <a onClick={() => setSelectedModel(null)}>
                {selectedManufacturer.manufacturer}
              </a>
            ) : (
              selectedManufacturer.manufacturer
            ),
          },
        ]
      : []),
    ...(selectedModel ? [{ title: selectedModel.name }] : []),
  ];

  return (
    <div className="overflow-y-auto max-h-96">
      {installStatus === "success" && (
        <Alert
          type="success"
          title="Plugin installed successfully."
          showIcon
          closable={{ afterClose: () => setInstallStatus("idle") }}
          style={{ marginBottom: 12 }}
        />
      )}
      {installStatus === "failure" && (
        <Alert
          type="error"
          title={installError ?? "Failed to install plugin."}
          showIcon
          closable={{ afterClose: () => setInstallStatus("idle") }}
          style={{ marginBottom: 12 }}
        />
      )}
      {showPluginInstallView && selectedModel ? (
        <PluginSetupSubview
          model={selectedModel}
          loading={installLoading}
          onInstall={handleInstall}
          onClose={() => setShowPluginInstallView(false)}
        />
      ) : (
        <>
          <Breadcrumb items={breadcrumbItems} style={{ marginBottom: 16 }} />

          {!selectedManufacturer && (
            <Row gutter={[16, 16]}>
              {plugins.data.map((manufacturer) => (
                <Col
                  key={manufacturer.manufacturer}
                  xs={24}
                  sm={12}
                  md={8}
                  lg={6}
                >
                  <PluginBrandCard
                    manufacturer={manufacturer.manufacturer}
                    models={manufacturer.models}
                    onClick={() => setSelectedManufacturer(manufacturer)}
                  />
                </Col>
              ))}
            </Row>
          )}

          {selectedManufacturer && !selectedModel && (
            <Row gutter={[16, 16]}>
              {selectedManufacturer.models.map((model) => (
                <Col key={model.module_path} xs={24} sm={12} md={8} lg={6}>
                  <PluginModelCard model={model} onClick={setSelectedModel} />
                </Col>
              ))}
            </Row>
          )}

          {selectedManufacturer && selectedModel && (
            <div className="plugin-page-main">
              <Modal
                title="Install Plugin"
                closable={{ "aria-label": "Custom Close Button" }}
                open={setupModalVisible}
                footer={[
                  <Button
                    key="cancel"
                    onClick={() => setSetupModalVisible(false)}
                  >
                    Cancel
                  </Button>,
                  <Button
                    key="install"
                    type="primary"
                    onClick={() => {
                      setSetupModalVisible(false);
                      setShowPluginInstallView(true);
                    }}
                  >
                    Install
                  </Button>,
                ]}
                onCancel={() => setSetupModalVisible(false)}
              >
                <div className="plugin-setup-subview">
                  <Typography.Title level={2} style={{ marginBottom: 16 }}>
                    Install {selectedModel.manifest?.name}
                  </Typography.Title>
                  <Typography.Paragraph type="secondary" style={{ marginBottom: 24 }}>
                    This will install the plugin "{selectedModel.manifest?.name}
                    " please follow the instructions provided to setup.
                  </Typography.Paragraph>
                </div>
              </Modal>
              {isCurrentPluginActive && (
                <Alert
                  type="success"
                  message="This plugin is currently active."
                  showIcon
                  style={{ marginBottom: 16 }}
                />
              )}
              <Descriptions bordered column={1} size="small">
                <Descriptions.Item label="Manufacturer">
                  {selectedManufacturer.manufacturer}
                </Descriptions.Item>
                {selectedModel.manifest && (
                  <>
                    <Descriptions.Item label="Plugin Name">
                      {selectedModel.manifest.name}
                    </Descriptions.Item>
                    <Descriptions.Item label="Version">
                      {selectedModel.manifest.version}
                    </Descriptions.Item>
                    <Descriptions.Item label="Author">
                      {selectedModel.manifest.author}
                    </Descriptions.Item>
                    <Descriptions.Item label="Connection Type">
                      {selectedModel.manifest.connectionType}
                    </Descriptions.Item>
                    {selectedModel.manifest.description && (
                      <Descriptions.Item label="Description">
                        {selectedModel.manifest.description}
                      </Descriptions.Item>
                    )}
                    {selectedModel.manifest.dependencies.length > 0 && (
                      <Descriptions.Item label="Dependencies">
                        {selectedModel.manifest.dependencies.join(", ")}
                      </Descriptions.Item>
                    )}
                  </>
                )}
              </Descriptions>
              <div>
                {isCurrentPluginActive ? (
                  <div>
                    <Typography.Paragraph>
                      Plugin is currently loaded and being used.
                    </Typography.Paragraph>
                  </div>
                ) : (
                  <Button
                    type="primary"
                    size="middle"
                    onClick={() => setSetupModalVisible(true)}
                  >
                    Install Plugin
                  </Button>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};
