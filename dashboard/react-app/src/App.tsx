import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Layout } from "./components/Layout";
import { OverviewPage } from "./pages/OverviewPage";
import { MachinesPage } from "./pages/MachinesPage";
import { MachineDetailPage } from "./pages/MachineDetailPage";
import { AlertsPage } from "./pages/AlertsPage";
import { ProtocolHealthPage } from "./pages/ProtocolHealthPage";

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<OverviewPage />} />
          <Route path="/machines" element={<MachinesPage />} />
          <Route path="/machines/:machineId" element={<MachineDetailPage />} />
          <Route path="/alerts" element={<AlertsPage />} />
          <Route path="/protocols" element={<ProtocolHealthPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
};


export default App;
