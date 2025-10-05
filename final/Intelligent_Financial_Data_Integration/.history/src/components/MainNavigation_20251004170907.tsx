import React from "react";
import PillNav from "./nav/PillNav";
import logo from "../assets/databridge-logo.png";

type MainNavigationProps = {
  currentView: string;
  onViewChange: (v: "integration" | "projects" | "collaboration" | "reports") => void;
  onProfileClick?: () => void;
};

export const MainNavigation: React.FC<MainNavigationProps> = ({
  currentView,
  onViewChange,
  onProfileClick
}) => {
  const items = [
    { label: "Integration", onClick: () => onViewChange("integration") },
    { label: "Projects", onClick: () => onViewChange("projects") },
    { label: "Team", onClick: () => onViewChange("collaboration") },
    { label: "Reports", onClick: () => onViewChange("reports") },
  ];

  const activeLabel =
    currentView === "collaboration" ? "Team" :
    currentView.charAt(0).toUpperCase() + currentView.slice(1);

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
              logo={logo}
              logoAlt="DataBridge"
              items={items}
              activeLabel={activeLabel}
              className=""
              ease="power2.easeOut"
              baseColor="#ffffff"
              pillColor="#0A0615"
              hoveredPillTextColor="#ffffff"
              pillTextColor="#ffffff"
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
    </header>
  );
};
