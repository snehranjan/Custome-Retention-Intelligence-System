import React from "react";
import { motion } from "framer-motion";
import {
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Cpu,
  BarChart,
  Target,
} from "lucide-react";
import { Button } from "../ui/Button";
import { Badge } from "../ui/Badge";
import { fadeUp, staggerContainer } from "../../utils/animations";

/**
 * RetainIQ Hero Text Content
 * Left column containing eyebrow, Sora heading, paragraph, CTAs, and trust indicators.
 */
export function HeroContent({ onExploreClick, onLoginClick }) {
  const trustBadges = [
    { label: "Machine Learning Powered", icon: Cpu },
    { label: "Customer-Level Predictions", icon: Target },
    { label: "Actionable Retention Insights", icon: BarChart },
  ];

  return (
    <div className="flex flex-col items-start max-w-2xl">
      {/* Eyebrow Pill */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className="mb-4 sm:mb-5"
      >
        <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-md bg-surface border border-border text-xs font-mono text-text-secondary shadow-subtle">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 shrink-0" />
          <span>Customer Retention Intelligence • Research & Operations</span>
        </div>
      </motion.div>

      {/* Main Heading (Sora - Weight 600) */}
      <motion.h1
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.25, delay: 0.04 }}
        className="font-heading text-3xl sm:text-4xl md:text-5xl lg:text-[3.25rem] font-semibold text-midnight tracking-tight leading-[1.14] mb-5 sm:mb-6"
      >
        Predict customer churn.{" "}
        <span className="block mt-1 sm:mt-1.5 text-electric font-semibold">
          Protect customer relationships.
        </span>
      </motion.h1>

      {/* Supporting Paragraph (Inter) */}
      <p className="text-sm sm:text-base text-text-secondary leading-relaxed mb-8 max-w-xl font-normal">
        Turn customer transaction telemetry into disciplined retention decisions. RetainIQ identifies customer churn risk with 43 behavioral features, discovers 5 RFM personas, and prescribes explainable intervention playbooks.
      </p>

      {/* Primary & Secondary Action CTAs */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 sm:gap-4 w-full sm:w-auto mb-8 sm:mb-10">
        <Button
          variant="primary"
          size="lg"
          icon={ArrowRight}
          iconPosition="right"
          onClick={onExploreClick}
          className="justify-center text-sm sm:text-base font-semibold"
        >
          Explore Platform
        </Button>

        <Button
          variant="secondary"
          size="lg"
          icon={ShieldCheck}
          onClick={onLoginClick}
          className="justify-center text-sm sm:text-base font-medium"
        >
          Employee Login
        </Button>
      </div>

      {/* Supporting Trust Indicators */}
      <div className="w-full pt-6 border-t border-border/80">
        <div className="flex flex-wrap items-center gap-4 sm:gap-6 text-xs text-text-secondary">
          {trustBadges.map((badge) => {
            const Icon = badge.icon;
            return (
              <div key={badge.label} className="flex items-center gap-2">
                <div className="w-5 h-5 rounded-full bg-success/10 text-success flex items-center justify-center shrink-0">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                </div>
                <span className="font-heading font-medium text-text-primary tracking-tight">
                  {badge.label}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
