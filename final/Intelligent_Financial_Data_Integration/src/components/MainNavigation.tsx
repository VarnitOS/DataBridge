import React, { useState } from "react";
import PillNav from "./nav/PillNav";
import { AddTabDialog, CustomTab } from "./AddTabDialog";
import logo from "../assets/databridge-logo.png";

type MainNavigationProps = {
  currentView: string;
  onViewChange: (v: "integration" | "agents" | "projects" | "collaboration" | "reports" | string) => void;
  onProfileClick?: () => void;
  onUpdateTabLabel?: (tabId: string, newLabel: string) => void;
  customTabs: CustomTab[];
  onAddTab: (tab: CustomTab) => void;
  onCloseTab?: (tabId: string) => void;
};

export const MainNavigation: React.FC<MainNavigationProps> = ({
  currentView,
  onViewChange,
  onProfileClick,
  onUpdateTabLabel,
  customTabs,
  onAddTab,
  onCloseTab
}) => {
  const [isAddTabDialogOpen, setIsAddTabDialogOpen] = useState(false);

  const defaultItems = [
    { label: "Integration", onClick: () => onViewChange("integration") },
    { label: "Agents", onClick: () => onViewChange("agents") },
    { label: "Projects", onClick: () => onViewChange("projects") },
    { label: "Team", onClick: () => onViewChange("collaboration") },
    { label: "Reports", onClick: () => onViewChange("reports") },
  ];

  const customTabItems = customTabs.map(tab => ({
    label: tab.label,
    onClick: () => onViewChange(tab.id),
    onClose: () => onCloseTab?.(tab.id),
    closable: true,
    style: { 
      backgroundColor: tab.color + '20',
      borderColor: tab.color + '40',
      color: tab.color
    }
  }));

  const items = [...defaultItems, ...customTabItems];

  const handleQuickAddTab = () => {
    const quickTab: CustomTab = {
      id: `custom-${Date.now()}`,
      label: "New Tab",
      color: '#3B82F6', // Default blue color
      createdAt: new Date(),
    };
    onAddTab(quickTab);
  };

  const activeLabel = (() => {
    if (currentView === "collaboration") return "Team";
    if (currentView === "agents") return "Agents";
    if (currentView.startsWith("custom-")) {
      const customTab = customTabs.find(tab => tab.id === currentView);
      return customTab ? customTab.label : "New Tab";
    }
    return currentView.charAt(0).toUpperCase() + currentView.slice(1);
  })();

  return (
    <header className="w-full bg-white relative">
      <div className="max-w-7xl mx-auto px-6 pt-6 pb-4 bg-white">
        {/* Single row layout: [logo+name | nav | profile] */}
        <div className="flex items-center justify-between gap-6">

          {/* LEFT: logo + brand */}
          <button 
            onClick={() => onViewChange("integration")} 
            className="flex items-center gap-6 px-12 py-6 transition-all cursor-pointer min-w-[1120px]"
          >
            <img
              src={logo}
              alt="DataBridge"
              className="h-12 w-auto object-contain"
            />
            <div className="leading-tight text-left flex-1">
              <div className="text-6xl font-bold bg-gradient-to-r from-primary via-purple-600 to-blue-600 bg-clip-text text-transparent">DataBridge</div>
              <div className="text-2xl text-muted-foreground mt-2">Your data, Our bridge.</div>
            </div>
          </button>

          {/* CENTER: PillNav */}
          <div className="flex-1 flex justify-center">
            <PillNav
              items={items}
              activeLabel={activeLabel}
              className="-translate-x-16"
              ease="power2.easeOut"
              baseColor="#6B7280"
              pillColor="#030213"
              hoveredPillTextColor="#ffffff"
              pillTextColor="#ffffff"
              onAddTab={handleQuickAddTab}
            />
          </div>

          {/* RIGHT: profile button (optional) */}
          <div className="flex justify-end min-w-fit">
            {onProfileClick && (
              <button
                onClick={onProfileClick}
                className="rounded-full border border-border px-4 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Profile
              </button>
            )}
          </div>

        </div>
      </div>
      
      <AddTabDialog
        isOpen={isAddTabDialogOpen}
        onClose={() => setIsAddTabDialogOpen(false)}
        onAddTab={onAddTab}
      />
    </header>
  );
};
