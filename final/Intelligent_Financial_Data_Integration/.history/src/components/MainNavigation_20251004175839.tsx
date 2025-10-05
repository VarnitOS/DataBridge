import React, { useState } from "react";
import PillNav from "./nav/PillNav";
import { AddTabDialog, CustomTab } from "./AddTabDialog";
import logo from "../assets/databridge-logo.png";

type MainNavigationProps = {
  currentView: string;
  onViewChange: (v: "integration" | "projects" | "collaboration" | "reports" | string) => void;
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
    { label: "Projects", onClick: () => onViewChange("projects") },
    { label: "Team", onClick: () => onViewChange("collaboration") },
    { label: "Reports", onClick: () => onViewChange("reports") },
  ];

  const customTabItems = customTabs.map(tab => ({
    label: tab.label,
    onClick: () => onViewChange(tab.id),
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
    if (currentView.startsWith("custom-")) {
      const customTab = customTabs.find(tab => tab.id === currentView);
      return customTab ? customTab.label : "New Tab";
    }
    return currentView.charAt(0).toUpperCase() + currentView.slice(1);
  })();

  return (
    <header className="w-full sticky top-0 z-50 bg-transparent">
      <div className="max-w-7xl mx-auto px-6 pt-4">
        {/* 3-column grid: [left | center | right] */}
        <div className="grid grid-cols-[auto_1fr_auto] items-center gap-4">

          {/* LEFT: logo + brand */}
          <div className="flex items-center gap-3">
            <img
              src={logo}
              alt="DataBridge"
              className="h-12 w-12 rounded-full object-contain"
            />
            <div className="leading-tight">
              <div className="text-xl font-semibold">DataBridge</div>
              <div className="text-sm text-white/60">Your data, Our bridge.</div>
            </div>
          </div>

          {/* CENTER: PillNav is truly centered by the middle grid cell */}
          <div className="flex justify-center">
            <PillNav
              items={items}
              activeLabel={activeLabel}
              className=""
              ease="power2.easeOut"
              baseColor="#ffffff"
              pillColor="#0A0615"
              hoveredPillTextColor="#ffffff"
              pillTextColor="#ffffff"
              onAddTab={handleQuickAddTab}
            />
          </div>

          {/* RIGHT: profile button (optional) */}
          <div className="flex justify-end">
            {onProfileClick && (
              <button
                onClick={onProfileClick}
                className="rounded-full border border-white/20 px-3 py-1 text-sm hover:bg-white/10"
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
