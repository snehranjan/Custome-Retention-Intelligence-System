import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { Badge } from "./Badge";

/**
 * RetainIQ Enterprise Design System - Section Heading
 * Unslopped: weight 500-600 hierarchy, solid high-contrast highlight (zero gradient text),
 * and balanced responsive spacing.
 */
export function SectionHeading({
  badge,
  badgeVariant = "primary",
  title,
  highlight,
  subtitle,
  align = "center",
  className = "",
  titleAs: TitleTag = "h2",
}) {
  const alignStyles = {
    left: "text-left items-start",
    center: "text-center items-center mx-auto",
    right: "text-right items-end ml-auto",
  };

  return (
    <div className={twMerge(clsx("flex flex-col max-w-3xl mb-10 sm:mb-12", alignStyles[align], className))}>
      {badge && (
        <div className="mb-3">
          <Badge variant={badgeVariant}>{badge}</Badge>
        </div>
      )}
      <TitleTag className="font-heading text-2xl sm:text-3xl md:text-4xl font-semibold text-midnight tracking-tight leading-snug">
        {title}{" "}
        {highlight && (
          <span className="text-electric font-semibold">
            {highlight}
          </span>
        )}
      </TitleTag>
      {subtitle && (
        <p className="mt-3 text-sm sm:text-base text-text-secondary leading-relaxed max-w-2xl">
          {subtitle}
        </p>
      )}
    </div>
  );
}
