import React, { useState, useEffect, useCallback } from "react";
import { Navbar } from "./components/layout/Navbar";
import { Footer } from "./components/layout/Footer";
import { HeroSection } from "./sections/HeroSection";
import { PlatformHighlights } from "./sections/PlatformHighlights";
import { FeatureShowcase } from "./sections/FeatureShowcase";
import { HowItWorks } from "./sections/HowItWorks";
import { AboutSection } from "./sections/AboutSection";
import { ActionModal } from "./components/common/ActionModal";
import { Container } from "./components/ui/Container";
import { EmployeeLoginPage } from "./pages/EmployeeLoginPage";
import { EmployeeDashboardPage } from "./pages/EmployeeDashboardPage";
import { AdminPortalPage } from "./pages/AdminPortalPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  const [currentPath, setCurrentPath] = useState(() => {
    return typeof window !== "undefined" ? window.location.pathname : "/";
  });

  const [modalState, setModalState] = useState({
    isOpen: false,
    data: null,
  });

  // Client-side navigation handler
  const navigate = useCallback((path) => {
    if (typeof window !== "undefined") {
      window.history.pushState({}, "", path);
      setCurrentPath(path);
      window.scrollTo({ top: 0, behavior: "instant" });
    }
  }, []);

  // Listen to browser Back/Forward navigation
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname);
    };
    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  // Handle direct hash navigation on initial landing page load (e.g., /#about)
  useEffect(() => {
    if (currentPath === "/" && window.location.hash) {
      const targetId = window.location.hash.replace("#", "");
      const targetElem = document.getElementById(targetId);
      if (targetElem) {
        targetElem.scrollIntoView({ behavior: "instant" });
      }
    }
  }, [currentPath]);

  // Dynamic Browser Page Titles & Search Engine Robots Meta Enforcement
  useEffect(() => {
    let robotsMeta = document.querySelector('meta[name="robots"]');
    if (!robotsMeta) {
      robotsMeta = document.createElement("meta");
      robotsMeta.name = "robots";
      document.head.appendChild(robotsMeta);
    }

    if (currentPath === "/") {
      document.title = "RetainIQ | Customer Retention Intelligence";
      robotsMeta.content = "index, follow";
    } else if (currentPath === "/employee/login") {
      document.title = "Employee Login | RetainIQ";
      robotsMeta.content = "noindex, nofollow";
    } else if (currentPath === "/employee/dashboard" || currentPath.startsWith("/employee/dashboard/")) {
      document.title = "Employee Dashboard | RetainIQ";
      robotsMeta.content = "noindex, nofollow";
    } else if (currentPath === "/admin" || currentPath.startsWith("/admin/")) {
      document.title = "Administrator Portal | RetainIQ";
      robotsMeta.content = "noindex, nofollow";
    } else {
      document.title = "Page Not Found | RetainIQ";
      robotsMeta.content = "noindex, nofollow";
    }
  }, [currentPath]);

  const handleOpenActionModal = (data) => {
    setModalState({
      isOpen: true,
      data,
    });
  };

  const handleCloseModal = () => {
    setModalState({
      isOpen: false,
      data: null,
    });
  };

  // Route 1: Employee Login Page (/employee/login)
  if (currentPath === "/employee/login") {
    return <EmployeeLoginPage onNavigate={navigate} />;
  }

  // Route 2: Employee Portal Dashboard (/employee/dashboard)
  if (currentPath === "/employee/dashboard" || currentPath.startsWith("/employee/dashboard/")) {
    return <EmployeeDashboardPage onNavigate={navigate} />;
  }

  // Route 3: Administrator Portal Page (/admin)
  if (currentPath === "/admin" || currentPath.startsWith("/admin/")) {
    return <AdminPortalPage onNavigate={navigate} />;
  }

  // Route 4: Public RetainIQ Showcase Landing Page (/)
  if (currentPath === "/" || currentPath.startsWith("/#")) {
    return (
      <div className="min-h-screen bg-bg text-text-primary flex flex-col justify-between selection:bg-electric selection:text-white">
        {/* RetainIQ Responsive Header & Navigation */}
        <Navbar onNavigate={navigate} onOpenActionModal={handleOpenActionModal} />

        {/* Main RetainIQ Landing Page Sections */}
        <main className="flex-grow">
          <HeroSection onNavigate={navigate} onOpenActionModal={handleOpenActionModal} />
          <PlatformHighlights onNavigate={navigate} onOpenActionModal={handleOpenActionModal} />
          <FeatureShowcase onNavigate={navigate} onOpenActionModal={handleOpenActionModal} />
          <HowItWorks onNavigate={navigate} onOpenActionModal={handleOpenActionModal} />
          <AboutSection onNavigate={navigate} onOpenActionModal={handleOpenActionModal} />
        </main>

        {/* Modal Dialog for Future Roadmap Links */}
        <ActionModal
          isOpen={modalState.isOpen}
          onClose={handleCloseModal}
          data={modalState.data}
          onNavigate={navigate}
        />

        {/* Comprehensive Website Footer */}
        <Footer onNavigate={navigate} />
      </div>
    );
  }

  // Route 5: Custom Branded 404 Page (for all unknown routes)
  return <NotFoundPage onNavigate={navigate} />;
}
