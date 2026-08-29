import React, { useEffect } from "react";
import { useStore } from "../store/useStore";

const SectorHeatmap: React.FC = () => {
  const { sectorData, fetchSectorData } = useStore();

  useEffect(() => {
    fetchSectorData();
  }, [fetchSectorData]);

  if (!sectorData || sectorData.length === 0) return null;

  return (
    <div style={{ width: "100%", marginBottom: "24px", backgroundColor: "#1e293b", padding: "16px", borderRadius: "8px" }}>
      <h3 style={{ margin: "0 0 16px 0", color: "#fff", fontSize: "1.1rem" }}>🔥 S&P 500 Sector Momentum (5D)</h3>
      <div 
        style={{ 
          display: "grid", 
          gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))", 
          gap: "8px" 
        }}
      >
        {sectorData.map((s) => {
          const isPositive = s.return_pct >= 0;
          // Calculate opacity based on return magnitude (max roughly at 5%)
          const magnitude = Math.min(Math.abs(s.return_pct) / 5, 1);
          // Base color 10b981 (green) or ef4444 (red) mixed with some opacity
          const bgColor = isPositive 
            ? `rgba(16, 185, 129, ${0.3 + (magnitude * 0.7)})` 
            : `rgba(239, 68, 68, ${0.3 + (magnitude * 0.7)})`;

          // Format name nicely (e.g. "Consumer Discretionary" -> "Cons Discret" or let it wrap)
          // We can let it wrap via CSS
          return (
            <div 
              key={s.ticker}
              style={{
                backgroundColor: bgColor,
                color: "#fff",
                padding: "10px 8px",
                borderRadius: "4px",
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                textAlign: "center",
                minHeight: "70px",
                transition: "transform 0.2s",
                cursor: "pointer"
              }}
              title={`${s.name} (${s.ticker})\nReturn: ${s.return_pct > 0 ? "+" : ""}${s.return_pct}%\nCurrent: $${s.current}`}
              onMouseEnter={(e) => (e.currentTarget.style.transform = "scale(1.05)")}
              onMouseLeave={(e) => (e.currentTarget.style.transform = "scale(1)")}
            >
              <span style={{ fontSize: "0.75rem", fontWeight: "bold", lineHeight: "1.1", marginBottom: "4px", wordBreak: "break-word" }}>
                {s.name}
              </span>
              <span style={{ fontSize: "0.85rem", fontWeight: "bold" }}>
                {s.return_pct > 0 ? "+" : ""}{s.return_pct.toFixed(2)}%
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default SectorHeatmap;
