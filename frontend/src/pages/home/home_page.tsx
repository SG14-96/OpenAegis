import React from "react";
import { useAppStore } from "../../store/appStore";

const HomePage = () => {
  const { activePlugin } = useAppStore();
  return (
    <div>
      <h1>Welcome to OpenAegis</h1>
      <p>Your smart home management system.</p>
    </div>
  );
};

export default HomePage;
