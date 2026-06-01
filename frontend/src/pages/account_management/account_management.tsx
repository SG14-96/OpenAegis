import { Button, Tag, Input, Tabs, Form, Table, Modal, Spin } from "antd";
import "../../styles/accountManagement.css";
import { useEffect, useState } from "react";
import { getCurrentUser } from "../../services/user";

const AccountManagementPage = () => {
  const [isLoading, setIsLoading] = useState(true);
  // For managing the current user's account details
  const [isEditingCurrentUser, setIsEditingCurrentUser] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [draftUser, setDraftUser] = useState<User | null>(null);
  // For managing other user accounts (admin functionality)
  const [userBeingEdited, setUserBeingEdited] = useState<User | null>(null);
  const [isEditingUser, setIsEditingUser] = useState(false);

  useEffect(() => {
    setIsLoading(true);
    new Promise((resolve) => setTimeout(resolve, 2000))
      .then(() => getCurrentUser())
      .then((userData) => {
        setUser(userData);
      })
      .catch((err) => {
        console.error("Failed to fetch user data:", err);
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const handleEditAccount = (record: User) => {
    console.log("Edit account for:", record);
    // Implement edit functionality here
  };
  const handleDisableAccount = (record: User) => {
    console.log("Disable account for:", record);
    // Implement disable functionality here
  };
  const handleDeleteAccount = (record: User) => {
    console.log("Delete account for:", record);
    // Implement delete functionality here
  };

  const myAccountTab = (
    <div>
      <p>Change account settings and preferences.</p>
      <Tag color="orange">Admin</Tag>
      <div className="account-details-container">
        <div className="account-details-item">
          <Form
            labelCol={{ span: 4 }}
            wrapperCol={{ span: 14 }}
            layout="vertical"
            disabled={!isEditingCurrentUser}
          >
            <Form.Item label="Name:">
              <Input
                value={
                  (isEditingCurrentUser ? draftUser : user)?.full_name || "N/A"
                }
                size="small"
                onChange={(e) =>
                  setDraftUser((d) => d && { ...d, full_name: e.target.value })
                }
              />
            </Form.Item>
            <Form.Item label="Username:">
              <Input
                value={
                  (isEditingCurrentUser ? draftUser : user)?.username || "N/A"
                }
                size="small"
                onChange={(e) =>
                  setDraftUser((d) => d && { ...d, username: e.target.value })
                }
              />
            </Form.Item>
            <Form.Item label="Email:">
              <Input
                value={
                  (isEditingCurrentUser ? draftUser : user)?.email || "N/A"
                }
                size="small"
                onChange={(e) =>
                  setDraftUser((d) => d && { ...d, email: e.target.value })
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
            {!isEditingCurrentUser ? (
              <Button
                variant="solid"
                color="primary"
                onClick={() => {
                  setDraftUser(user);
                  setIsEditingCurrentUser(true);
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
                    setIsEditingCurrentUser(false);
                  }}
                >
                  Cancel
                </Button>
                <Button
                  variant="solid"
                  color="primary"
                  onClick={() => {
                    setUser(draftUser);
                    setDraftUser(null);
                    setIsEditingCurrentUser(false);
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

  const dataSource: User[] = [
    {
      user_uuid: "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      username: "mike_smith",
      email: "mike@example.com",
      full_name: "Mike",
      last_name: "Smith",
      is_superuser: true,
    },
    {
      user_uuid: "b2c3d4e5-f6a7-8901-bcde-f12345678901",
      username: "john_doe",
      email: "john@example.com",
      full_name: "John",
      last_name: "Doe",
      is_superuser: false,
    },
    {
      user_uuid: "c3d4e5f6-a7b8-9012-cdef-123456789012",
      username: "alice_wonder",
      email: "alice@example.com",
      full_name: "Alice",
      last_name: "Wonder",
      is_superuser: false,
    },
    {
      user_uuid: "d4e5f6a7-b8c9-0123-defa-234567890123",
      username: "bob_builder",
      email: "bob@example.com",
      full_name: "Bob",
      last_name: "Builder",
      is_superuser: false,
    },
  ];

  const columns = [
    {
      title: "Full Name",
      key: "full_name",
      render: (_: unknown, record: User) =>
        `${record.full_name} ${record.last_name}`,
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
      key: "is_superuser",
      render: (_: unknown, record: User) => (
        <Tag color={record.is_superuser ? "orange" : "blue"}>
          {record.is_superuser ? "Admin" : "User"}
        </Tag>
      ),
    },
    {
      title: "Actions",
      key: "actions",
      render: (_: unknown, record: User) =>
        !record.is_superuser ? (
          <div className="account-actions-container">
            <Button
              variant="outlined"
              color="primary"
              onClick={() => {
                setUserBeingEdited(record);
                setIsEditingUser(true);
              }}
            >
              Edit
            </Button>
            <Button
              variant="outlined"
              color="orange"
              onClick={() => handleDisableAccount(record)}
            >
              Disable
            </Button>
            <Button
              variant="outlined"
              danger
              onClick={() => handleDeleteAccount(record)}
            >
              Delete
            </Button>
          </div>
        ) : null,
    },
  ];

  const otherAccountsTab = (
    <div>
      <p>Manage other user accounts in the system.</p>
      <Table dataSource={dataSource} columns={columns} rowKey="user_uuid" />
    </div>
  );

  const tabItems = [
    { key: "my-account", label: "My Account", children: myAccountTab },
    {
      key: "other-accounts",
      label: "Other Accounts",
      children: otherAccountsTab,
    },
  ];

  return (
    <div className="account-management-container">
      <Modal
        title="Edit User Account Details"
        closable={{ "aria-label": "Custom Close Button" }}
        open={isEditingUser}
        onOk={() => userBeingEdited && handleEditAccount(userBeingEdited)}
        onCancel={() => {
          setIsEditingUser(false);
          setUserBeingEdited(null);
        }}
      >
        <p>Some contents...</p>
        <p>Some contents...</p>
        <p>Some contents...</p>
      </Modal>
      {isLoading ? (
        <div className="account-spinner-container">
          <Spin size="large" />
        </div>
      ) : (
        <>
          <h1>Account Management</h1>
          <Tabs items={tabItems} />
        </>
      )}
    </div>
  );
};

export default AccountManagementPage;
