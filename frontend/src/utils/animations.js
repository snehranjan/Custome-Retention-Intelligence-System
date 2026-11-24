/**
 * RetainIQ Reusable Motion & Animation Conventions (Framer Motion)
 *
 * Provides standardized animation presets, entrance transitions, staggered reveals,
 * and reduced-motion accessibility helpers.
 */

// Basic fade in
export const fadeIn = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] },
  },
};

// Fade up (standard content entrance)
export const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
  },
};

// Fade down (header and alert entrances)
export const fadeDown = {
  hidden: { opacity: 0, y: -20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.4, ease: [0.16, 1, 0.3, 1] },
  },
};

// Slide in from left
export const slideInLeft = {
  hidden: { opacity: 0, x: -30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
  },
};

// Slide in from right
export const slideInRight = {
  hidden: { opacity: 0, x: 30 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { duration: 0.5, ease: [0.16, 1, 0.3, 1] },
  },
};

// Stagger container for lists and card grids
export const staggerContainer = (staggerChildren = 0.1, delayChildren = 0.05) => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren,
      delayChildren,
    },
  },
});

// Subtle scale in for badges, modals, and metric numbers
export const scaleUp = {
  hidden: { opacity: 0, scale: 0.94 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { duration: 0.35, ease: [0.16, 1, 0.3, 1] },
  },
};

// Micro-interaction hover states
export const cardHover = {
  rest: { y: 0, boxShadow: "0 4px 6px -1px rgba(11, 25, 44, 0.05)" },
  hover: {
    y: -4,
    boxShadow: "0 12px 20px -3px rgba(11, 25, 44, 0.08)",
    transition: { duration: 0.25, ease: "easeOut" },
  },
};

// Button press micro-interaction
export const buttonTap = {
  tap: { scale: 0.98 },
};
