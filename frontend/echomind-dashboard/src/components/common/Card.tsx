import React from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({
  title,
  subtitle,
  action,
  children,
  className = "",
}) => {
  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-5 shadow-xs sm:p-6 ${className}`}
    >
      {(title || action) && (
        <div className="mb-4 flex items-start justify-between gap-4 border-b border-slate-100 pb-3">
          <div>
            {title && (
              <h2 className="text-base font-semibold text-slate-900">{title}</h2>
            )}
            {subtitle && (
              <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div>{children}</div>
    </div>
  );
};
