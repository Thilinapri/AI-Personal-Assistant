import React from "react";

interface CardProps {
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<
  CardProps
> = ({
  title,
  subtitle,
  action,
  children,
  className = "",
}) => {
  return (
    <div
      className={`rounded-2xl border border-slate-200/80 bg-white/90 p-5 shadow-[0_8px_30px_rgba(15,23,42,0.045)] backdrop-blur-sm transition-all duration-200 hover:border-slate-300 hover:shadow-[0_14px_36px_rgba(15,23,42,0.07)] sm:p-6 ${className}`}
    >
      {(title || action) && (
        <div className="mb-5 flex items-start justify-between gap-4 border-b border-slate-100 pb-4">
          <div className="min-w-0">
            {title && (
              <h2 className="truncate text-[15px] font-bold tracking-tight text-slate-950">
                {title}
              </h2>
            )}

            {subtitle && (
              <p className="mt-1 text-[11px] leading-relaxed text-slate-500">
                {subtitle}
              </p>
            )}
          </div>

          {action && (
            <div className="shrink-0">
              {action}
            </div>
          )}
        </div>
      )}

      <div>{children}</div>
    </div>
  );
};