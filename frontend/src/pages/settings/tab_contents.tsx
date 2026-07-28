import React, { useEffect, useState } from "react";
import {
  Alert,
  Breadcrumb,
  Button,
  Col,
  Descriptions,
  Form,
  Input,
  Modal,
  Row,
  Spin,
  Table,
  Tag,
  Typography,
} from "antd";
import { PluginBrandCard } from "./plugins_settings_ui/plugin_brand_card";
import { PluginModelCard } from "./plugins_settings_ui/plugin_model_card";
import { PluginSetupSubview } from "./plugins_settings_ui/plugin_install_view";
import type { StepValues } from "./plugins_settings_ui/plugin_install_view";
import { ActivePluginCard } from "./plugins_settings_ui/active_plugin_card";
import { listAvailablePlugins, loadPlugin } from "../../services/plugins";
import { getCurrentUser } from "../../services/user";
import {
  listUsers,
  updateUser as updateOtherUser,
  disableUser,
  enableUser,
  deleteUser,
} from "../../services/adminUsers";
import { useAppStore } from "../../store/appStore";
import "../../styles/accountManagement.css";

const { Paragraph } = Typography;

type AsyncState<T> = {
  data: T | null;
  isLoading: boolean;
  error: string | null;
};

function asyncInit<T>(): AsyncState<T> {
  return { data: null, isLoading: false, error: null };
}

function getErrorMessage(err: unknown, fallback: string): string {
  const detail = (err as { response?: { data?: { detail?: string } } })
    ?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (err instanceof Error) return err.message;
  return fallback;
}

export const AccountTab: React.FC = () => {
  const [userInfo, setUserInfo] = useState<AsyncState<User>>(asyncInit);
  const [isEditing, setIsEditing] = useState(false);
  const [draftUser, setDraftUser] = useState<User | null>(null);

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

  const user = userInfo.data;
  const displayedUser = isEditing ? draftUser ?? user : user;

  return (
    <div>
      <Paragraph>Change account settings and preferences.</Paragraph>
      {user.isSuperUser && <Tag color="orange">Admin</Tag>}
      <div className="account-details-container">
        <div className="account-details-item">
          <Form
            labelCol={{ span: 4 }}
            wrapperCol={{ span: 14 }}
            layout="vertical"
            disabled={!isEditing}
          >
            <Form.Item label="Name:">
              <Input
                value={displayedUser.full_name || "N/A"}
                size="small"
                onChange={(e) =>
                  setDraftUser((d) => ({
                    ...(d ?? user),
                    full_name: e.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Username:">
              <Input
                value={displayedUser.username || "N/A"}
                size="small"
                onChange={(e) =>
                  setDraftUser((d) => ({
                    ...(d ?? user),
                    username: e.target.value,
                  }))
                }
              />
            </Form.Item>
            <Form.Item label="Email:">
              <Input
                value={displayedUser.email || "N/A"}
                size="small"
                onChange={(e) =>
                  setDraftUser((d) => ({
                    ...(d ?? user),
                    email: e.target.value,
                  }))
                }
              />
            </Form.Item>
          </Form>
          <div
            style={{
              display: "flex",
              flexDirection: "row",
              justifyContent: "center",
            }}
          >
            {!isEditing ? (
              <Button
                variant="solid"
                color="primary"
                onClick={() => {
                  setDraftUser(user);
                  setIsEditing(true);
                }}
              >
                Edit Account Details
              </Button>
            ) : (
              <div
                style={{
                  display: "flex",
                  flexDirection: "row",
                  justifyContent: "center",
                  gap: "20px",
                }}
              >
                <Button
                  variant="outlined"
                  onClick={() => {
                    setDraftUser(null);
                    setIsEditing(false);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="solid"
                  color="primary"
                  onClick={() => {
                    if (draftUser) {
                      setUserInfo((s) => ({ ...s, data: draftUser }));
                    }
                    setDraftUser(null);
                    setIsEditing(false);
                  }}
                >
                  Update Account Details
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
      <div className="account-buttons-container">
        <Button variant="outlined">Change Password</Button>
        <Button variant="outlined" danger>
          Delete Account
        </Button>
      </div>
    </div>
  );
};

type EditUserFormValues = {
  full_name: string;
  username: string;
  email: string;
};

type ConfirmAction = {
  type: "disable" | "delete";
  user: User;
};

export const OtherAccountsTab: React.FC = () => {
  const [users, setUsers] = useState<AsyncState<User[]>>(asyncInit);

  const [userBeingEdited, setUserBeingEdited] = useState<User | null>(null);
  const [editForm] = Form.useForm<EditUserFormValues>();
  const [editSaving, setEditSaving] = useState(false);
  const [editError, setEditError] = useState<string | null>(null);

  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(
    null
  );
  const [confirmLoading, setConfirmLoading] = useState(false);
  const [confirmError, setConfirmError] = useState<string | null>(null);

  const [enablingUuid, setEnablingUuid] = useState<string | null>(null);
  const [enableError, setEnableError] = useState<string | null>(null);

  const fetchUsers = () => {
    setUsers({ data: null, isLoading: true, error: null });
    listUsers()
      .then((data) => setUsers({ data, isLoading: false, error: null }))
      .catch((err) =>
        setUsers({
          data: null,
          isLoading: false,
          error: getErrorMessage(err, "Failed to load users"),
        })
      );
  };

  useEffect(fetchUsers, []);

  const openEdit = (record: User) => {
    setEditError(null);
    setUserBeingEdited(record);
    editForm.setFieldsValue({
      full_name: record.full_name,
      username: record.username,
      email: record.email,
    });
  };

  const closeEdit = () => {
    setUserBeingEdited(null);
    setEditError(null);
    editForm.resetFields();
  };

  const handleEditSubmit = async () => {
    if (!userBeingEdited) return;
    let values: EditUserFormValues;
    try {
      values = await editForm.validateFields();
    } catch {
      return; // antd already surfaces field-level validation errors
    }
    setEditSaving(true);
    setEditError(null);
    try {
      const updated = await updateOtherUser(userBeingEdited.user_uuid, values);
      setUsers((s) => ({
        ...s,
        data: (s.data ?? []).map((u) =>
          u.user_uuid === updated.user_uuid ? updated : u
        ),
      }));
      closeEdit();
    } catch (err) {
      setEditError(getErrorMessage(err, "Failed to update user"));
    } finally {
      setEditSaving(false);
    }
  };

  const closeConfirm = () => {
    setConfirmAction(null);
    setConfirmError(null);
  };

  const handleConfirm = async () => {
    if (!confirmAction) return;
    setConfirmLoading(true);
    setConfirmError(null);
    try {
      if (confirmAction.type === "disable") {
        const updated = await disableUser(confirmAction.user.user_uuid);
        setUsers((s) => ({
          ...s,
          data: (s.data ?? []).map((u) =>
            u.user_uuid === updated.user_uuid ? updated : u
          ),
        }));
      } else {
        await deleteUser(confirmAction.user.user_uuid);
        setUsers((s) => ({
          ...s,
          data: (s.data ?? []).filter(
            (u) => u.user_uuid !== confirmAction.user.user_uuid
          ),
        }));
      }
      closeConfirm();
    } catch (err) {
      setConfirmError(
        getErrorMessage(err, `Failed to ${confirmAction.type} user`)
      );
    } finally {
      setConfirmLoading(false);
    }
  };

  const handleEnable = async (record: User) => {
    setEnableError(null);
    setEnablingUuid(record.user_uuid);
    try {
      const updated = await enableUser(record.user_uuid);
      setUsers((s) => ({
        ...s,
        data: (s.data ?? []).map((u) =>
          u.user_uuid === updated.user_uuid ? updated : u
        ),
      }));
    } catch (err) {
      setEnableError(getErrorMessage(err, "Failed to enable user"));
    } finally {
      setEnablingUuid(null);
    }
  };

  const columns = [
    {
      title: "Full Name",
      dataIndex: "full_name",
      key: "full_name",
    },
    {
      title: "Username",
      dataIndex: "username",
      key: "username",
    },
    {
      title: "Email",
      dataIndex: "email",
      key: "email",
    },
    {
      title: "Role",
      key: "isSuperUser",
      render: (_: unknown, record: User) => (
        <Tag color={record.isSuperUser ? "orange" : "blue"}>
          {record.isSuperUser ? "Admin" : "User"}
        </Tag>
      ),
    },
    {
      title: "Status",
      key: "disabled",
      render: (_: unknown, record: User) => (
        <Tag color={record.disabled ? "red" : "green"}>
          {record.disabled ? "Disabled" : "Active"}
        </Tag>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: User) =>
        !record.isSuperUser ? (
          <div className="account-actions-container">
            <Button
              variant="outlined"
              color="primary"
              onClick={() => openEdit(record)}
            >
              Edit
            </Button>
            {record.disabled ? (
              <Button
                variant="outlined"
                color="green"
                loading={enablingUuid === record.user_uuid}
                onClick={() => handleEnable(record)}
              >
                Enable
              </Button>
            ) : (
              <Button
                variant="outlined"
                color="orange"
                onClick={() =>
                  setConfirmAction({ type: "disable", user: record })
                }
              >
                Disable
              </Button>
            )}
            <Button
              variant="outlined"
              danger
              onClick={() => setConfirmAction({ type: "delete", user: record })}
            >
              Delete
            </Button>
          </div>
        ) : null,
    },
  ];

  if (users.isLoading) {
    return (
      <div className="flex justify-center p-8">
        <Spin size="large" />
      </div>
    );
  }

  if (users.error) {
    return <Alert type="error" title={users.error} />;
  }

  return (
    <div>
      <Modal
        title={`Edit ${userBeingEdited?.username ?? "User"}`}
        closable={{ "aria-label": "Custom Close Button" }}
        open={!!userBeingEdited}
        onOk={handleEditSubmit}
        onCancel={closeEdit}
        confirmLoading={editSaving}
        okText="Save Changes"
      >
        {editError && (
          <Alert
            type="error"
            title={editError}
            showIcon
            style={{ marginBottom: 12 }}
          />
        )}
        <Form form={editForm} layout="vertical">
          <Form.Item
            name="full_name"
            label="Full Name"
            rules={[{ required: true, message: "Full name is required" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: "Username is required" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: "Email is required" },
              { type: "email", message: "Enter a valid email" },
            ]}
          >
            <Input />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={confirmAction?.type === "delete" ? "Delete User" : "Disable User"}
        closable={{ "aria-label": "Custom Close Button" }}
        open={!!confirmAction}
        onOk={handleConfirm}
        onCancel={closeConfirm}
        confirmLoading={confirmLoading}
        okText={confirmAction?.type === "delete" ? "Delete" : "Disable"}
        okButtonProps={{ danger: true }}
      >
        {confirmError && (
          <Alert
            type="error"
            title={confirmError}
            showIcon
            style={{ marginBottom: 12 }}
          />
        )}
        <Paragraph>
          {confirmAction?.type === "delete"
            ? `Are you sure you want to delete "${confirmAction.user.username}"? This action cannot be undone.`
            : `Are you sure you want to disable "${confirmAction?.user.username}"? They will no longer be able to sign in.`}
        </Paragraph>
      </Modal>

      <Paragraph>Manage other user accounts in the system.</Paragraph>
      {enableError && (
        <Alert
          type="error"
          title={enableError}
          showIcon
          closable={{ afterClose: () => setEnableError(null) }}
          style={{ marginBottom: 12 }}
        />
      )}
      <Table
        dataSource={users.data ?? []}
        columns={columns}
        rowKey="user_uuid"
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
      <div>
        <ActivePluginCard />
        <div className="flex justify-center p-8">
          <Spin size="large" />
        </div>
      </div>
    );
  }

  if (plugins.error) {
    return (
      <div>
        <ActivePluginCard />
        <Alert type="error" title={plugins.error} />
      </div>
    );
  }

  if (!plugins.data || plugins.data.length === 0) {
    return (
      <div>
        <ActivePluginCard />
        <Alert type="info" title="No plugins available." />
      </div>
    );
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
      <ActivePluginCard />
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
