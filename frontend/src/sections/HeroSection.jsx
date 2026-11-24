import React from "react";
import { Container } from "../components/ui/Container";
import { HeroContent } from "../components/hero/HeroContent";
import { HeroDashboardPreview } from "../components/hero/HeroDashboardPreview";

/**
 * RetainIQ Standalone Animated Hero Section
 * Two-column desktop layout (text on left, product dashboard on right),
 * stacking vertically on mobile and tablet with responsive spacing.
 */
export function HeroSection({ onNavigate, onOpenActionModal }) {
  const handleExploreClick = () => {
    const platformElement = document.getElementById("platform");
    if (platformElement) {
      platformElement.scrollIntoView({ behavior: "smooth" });
    } else {
      const dashboardElement = document.getElementById("dashboard-preview");
      if (dashboardElement) {
        dashboardElement.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }
  };

  const handleLoginClick = () => {
    if (onNavigate) {
      onNavigate("/employee/login");
    } else {
      window.location.pathname = "/employee/login";
    }
  };

  return (
    <section
      id="hero"
      className="relative pt-8 pb-14 sm:pt-12 sm:pb-20 lg:pt-14 lg:pb-24 overflow-hidden bg-bg border-b border-border/60"
    >
      <Container size="default" className="relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 lg:gap-8 xl:gap-12 items-center">
          {/* Left Column: Hero Text Content */}
          <div className="lg:col-span-5 xl:col-span-5 flex justify-center lg:justify-start">
            <HeroContent
              onExploreClick={handleExploreClick}
              onLoginClick={handleLoginClick}
            />
          </div>

          {/* Right Column: Animated Product Dashboard Preview */}
          <div className="lg:col-span-7 xl:col-span-7 flex justify-center">
            <HeroDashboardPreview />
          </div>
        </div>
      </Container>
    </section>
  );
}
