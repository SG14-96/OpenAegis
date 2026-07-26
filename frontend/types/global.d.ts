declare global {
  type User = {
    user_uuid: string;
    username: string;
    email: string;
    full_name: string;
    disabled: boolean;
    isSuperUser: boolean;
  };

  type PluginManifestOption = {
    label: string;
    value: string | number;
  };

  type PluginManifestInput = {
    type: string;
    placeholder: string;
  };

  type PluginManifestStep = {
    step: string;
    details: string;
    options?: PluginManifestOption[];
    input?: PluginManifestInput;
  };

  type PluginManifest = {
    name: string;
    version: string;
    description?: string;
    author: string;
    connectionType: "mqtt" | "http" | "websocket" | "serial" | "other";
    connectionSetupSteps?: PluginManifestStep[];
    dependencies: string[];
  };

  type PluginModel = {
    name: string;
    module_path: string;
    manifest: PluginManifest | null;
  };

  type PluginManufacturer = {
    manufacturer: string;
    logoImg?: string;
    models: PluginModel[];
  };
}

export {};
