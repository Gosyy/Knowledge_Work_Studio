import type { CSSProperties } from "react";
import { ArtifactsPanel } from "@/components/artifacts/artifacts-panel";
import { ChatPanel } from "@/components/chat/chat-panel";
import { UploadPanel } from "@/components/upload/upload-panel";
import { TaskStatusPanel } from "@/components/task-status/task-status-panel";

const panelStyle: CSSProperties = {
  background: "#ffffff",
  border: "1px solid #d1d5db",
  borderRadius: "0.5rem",
  padding: "1rem",
  minHeight: "200px",
};

const gridStyle: CSSProperties = {
  display: "grid",
  gridTemplateColumns: "repeat(2, minmax(0, 1fr))",
  gap: "1rem",
};

const containerStyle: CSSProperties = {
  maxWidth: "1200px",
  margin: "0 auto",
  padding: "1.5rem",
};

export function WorkspaceShell() {
  return (
    <main style={containerStyle}>
      <h1>KW Studio Workspace</h1>
      <p>Bootstrap workspace shell for chat-driven knowledge workflows.</p>
      <section style={gridStyle} aria-label="workspace-panels">
        <div style={panelStyle}>
          <ChatPanel />
        </div>
        <div style={panelStyle}>
          <UploadPanel />
        </div>
        <div style={panelStyle}>
          <TaskStatusPanel />
        </div>
        <div style={panelStyle}>
          <ArtifactsPanel />
        </div>
      </section>
    </main>
  );
}
