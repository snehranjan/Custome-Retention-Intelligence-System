import React from "react";
import { clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * RetainIQ Design System - Responsive Layout Container
 * Enforces unified horizontal padding and max-widths across 390px, 768px, 1024px, 1440px.
 */
export function Container({ children, size = "default", className = "", ...props }) {
  const sizeStyles = {
    narrow: "max-w-4xl",
    default: "max-w-7xl",
    wide: "max-w-screen-2xl",
    full: "max-w-full",
  };

  return (
    <div
      className={twMerge(
        clsx(
          "w-full mx-auto px-4 sm:px-6 md:px-8 lg:px-10",
          sizeStyles[size],
          className
        )
      )}
      {...props}
    >
      {children}
    </div>
  );
}
