import React from "react";

interface PageHeaderProps {
  title: string;
  description: string;
  badge?: string;
  actions?: React.ReactNode;
}

export const PageHeader: React.FC<
  PageHeaderProps
> = ({
  title,
  description,
  badge,
  actions,
}) => {
  return (
    <div className="relative overflow-hidden rounded-3xl border border-slate-200/80 bg-white/90 px-5 py-6 shadow-[0_10px_35px_rgba(15,23,42,0.045)] backdrop-blur-sm sm:px-7 sm:py-7">
      <div className="pointer-events-none absolute -right-12 -top-20 h-48 w-48 rounded-full bg-indigo-100/55 blur-3xl" />

      <div className="pointer-events-none absolute right-28 top-0 h-28 w-28 rounded-full bg-sky-100/50 blur-3xl" />

      <div className="relative flex flex-col justify-between gap-5 sm:flex-row sm:items-center">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-3">
            <h1 className="text-2xl font-bold tracking-[-0.025em] text-slate-950 sm:text-[30px]">
              {title}
            </h1>

            {badge && (
              <span className="inline-flex rounded-full border border-indigo-100 bg-indigo-50 px-2.5 py-1 text-[10px] font-bold text-indigo-700 shadow-sm">
                {badge}
              </span>
            )}
          </div>

          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-500">
            {description}
          </p>
        </div>

        {actions && (
          <div className="flex shrink-0 items-center gap-2">
            {actions}
          </div>
        )}
      </div>
    </div>
  );
};