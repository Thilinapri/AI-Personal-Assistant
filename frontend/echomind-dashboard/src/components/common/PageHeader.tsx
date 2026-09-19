import React from "react";

interface PageHeaderProps {
  title: string;
  description: string;
  badge?: string;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<PageHeaderProps> = ({
  title,
  description,
  badge,
  actions,
}) => {
  return (
    <div className="mb-6 flex flex-col justify-between gap-4 border-b border-slate-200 pb-5 sm:flex-row sm:items-center">
      <div>
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            {title}
          </h1>
          {badge && (
            <span className="rounded-full bg-indigo-50 px-2.5 py-0.5 text-xs font-semibold text-indigo-700 ring-1 ring-inset ring-indigo-600/20">
              {badge}
            </span>
          )}
        </div>
        <p className="mt-1 text-sm text-slate-600 sm:text-base">
          {description}
        </p>
      </div>

      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
};
