import React from 'react';

interface StatCardProps {
  label: string;
  value: string | number;
  icon: React.ReactNode;
  subtitle?: string;
  trend?: string;
}

export const StatCard: React.FC<StatCardProps> = ({
  label,
  value,
  icon,
  subtitle,
  trend,
}) => {
  return (
    <div className="stat-card">
      <div className="stat-header">
        <span className="stat-label">{label}</span>
        <div className="stat-icon-wrapper">{icon}</div>
      </div>
      <div className="stat-value">{value}</div>
      {(subtitle || trend) && (
        <div className="stat-meta">
          {trend && <span style={{ color: '#10B981', fontWeight: 600 }}>{trend}</span>}
          {subtitle && <span>{subtitle}</span>}
        </div>
      )}
    </div>
  );
};
