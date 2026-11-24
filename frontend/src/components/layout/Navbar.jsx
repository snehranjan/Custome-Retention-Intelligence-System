import React, { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Menu,
  X,
  Lock,
  ArrowRight,
  ChevronRight,
  Shield,
  Layers,
  LayoutDashboard,
  LogOut,
  User,
} from "lucide-react";
import { Container } from "../ui/Container";
import { Button } from "../ui/Button";
import { IconButton } from "../ui/IconButton";
import { ThemeToggle } from "../ui/ThemeToggle";
import { useAuth } from "../../context/AuthContext";
import { supabase } from "../../lib/supabase";

/**
 * RetainIQ Header & Navigation Bar (Phase 8.4 Pre-Deployment Polish)
 * 
 * Requirements:
 * - Brand logo & clickable title navigating to top/home.
 * - Desktop navigation with active section highlights.
 * - Accessible mobile hamburger menu with backdrop click-outside closing.
 * - Escape key closing & background scroll lock while open.
 * - Role-sensitive navigation (Employee Dashboard vs Admin Portal vs Login).
 */
export function Navbar({ onNavigate, onOpenActionModal }) {
  const { session, user } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [activeHash, setActiveHash] = useState("#hero");
  const menuRef = useRef(null);

  // Monitor scroll to apply elevated backdrop & active section detection
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);

      // Simple active section detection based on scroll position
      const sections = ["about", "how-it-works", "features", "platform", "hero"];
      for (const sectionId of sections) {
        const el = document.getElementById(sectionId);
        if (el) {
          const rect = el.getBoundingClientRect();
          if (rect.top <= 120 && rect.bottom >= 120) {
            setActiveHash("#" + sectionId);
            break;
          }
        }
      }
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // Prevent background scrolling when mobile menu is open
  useEffect(() => {
    if (mobileMenuOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [mobileMenuOpen]);

  // Close mobile menu on Escape key
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "Escape" && mobileMenuOpen) {
        setMobileMenuOpen(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [mobileMenuOpen]);

  const navLinks = [
    { name: "Home", href: "#hero" },
    { name: "Platform", href: "#platform" },
    { name: "Features", href: "#features" },
    { name: "How It Works", href: "#how-it-works" },
    { name: "About", href: "#about" },
  ];

  const handleLinkClick = (e, link) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    setActiveHash(link.href);

    if (window.location.pathname !== "/") {
      if (onNavigate) {
        onNavigate("/" + link.href);
      } else {
        window.location.href = "/" + link.href;
      }
      return;
    }

    const targetId = link.href.replace("#", "");
    if (targetId === "hero") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      const element = document.getElementById(targetId);
      if (element) {
        element.scrollIntoView({ behavior: "smooth" });
      }
    }
  };

  const handleLogoClick = (e) => {
    e.preventDefault();
    setMobileMenuOpen(false);
    setActiveHash("#hero");
    if (window.location.pathname === "/") {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } else {
      if (onNavigate) {
        onNavigate("/");
      } else {
        window.location.pathname = "/";
      }
    }
  };

  const handleLoginClick = () => {
    setMobileMenuOpen(false);
    if (onNavigate) {
      onNavigate("/employee/login");
    } else {
      window.location.pathname = "/employee/login";
    }
  };

  const handleDashboardClick = () => {
    setMobileMenuOpen(false);
    if (onNavigate) {
      onNavigate("/employee/dashboard");
    } else {
      window.location.pathname = "/employee/dashboard";
    }
  };

  const handleAdminClick = () => {
    setMobileMenuOpen(false);
    if (onNavigate) {
      onNavigate("/admin");
    } else {
      window.location.pathname = "/admin";
    }
  };

  const handleSignOut = async () => {
    setMobileMenuOpen(false);
    try {
      if (supabase) {
        await supabase.auth.signOut();
      }
    } catch {
      // Ignore signout error
    }
    if (onNavigate) {
      onNavigate("/");
    } else {
      window.location.pathname = "/";
    }
  };

  const handleGetStartedClick = () => {
    setMobileMenuOpen(false);
    const platformElement = document.getElementById("platform");
    if (platformElement) {
      platformElement.scrollIntoView({ behavior: "smooth" });
    } else {
      window.scrollTo({ top: 400, behavior: "smooth" });
    }
  };

  return (
    <>
      <header
        className={`sticky top-0 z-50 transition-all duration-300 ${
          isScrolled
            ? "bg-surface/95 backdrop-blur-md border-b border-border shadow-subtle py-3"
            : "bg-surface/85 backdrop-blur-sm border-b border-border/60 py-4 sm:py-5"
        }`}
      >
        <Container size="default" className="flex items-center justify-between">
          {/* Brand Logo & Title (Clickable) */}
          <a
            href="/"
            onClick={handleLogoClick}
            className="flex items-center gap-2.5 group focus-visible:ring-2 focus-visible:ring-electric rounded-lg p-1"
            aria-label="RetainIQ Home"
          >
            {/* Custom RetainIQ Logo Mark */}
            <div className="w-9 h-9 rounded-lg bg-midnight flex items-center justify-center border border-slate-800 group-hover:border-slate-700 transition-colors">
              <svg
                className="w-4.5 h-4.5 text-white"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M4 12v-3a8 8 0 0 1 16 0v3" />
                <path d="M9 18l3 3 3-3" />
                <circle cx="12" cy="12" r="3" fill="#0052CC" stroke="none" />
              </svg>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-2">
                <span className="font-heading font-semibold text-lg text-midnight tracking-tight">
                  Retain<span className="text-electric">IQ</span>
                </span>
                <span className="hidden lg:inline-flex items-center px-1.5 py-0.5 text-[10px] font-mono font-medium uppercase rounded bg-slate-100 text-text-secondary border border-slate-200">
                  AI ML
                </span>
              </div>
              <span className="hidden sm:block text-[11px] text-text-secondary font-medium tracking-tight">
                Customer Retention Intelligence
              </span>
            </div>
          </a>

          {/* Desktop Navigation Links */}
          <nav className="hidden md:flex items-center gap-1 lg:gap-2" aria-label="Main Navigation">
            {navLinks.map((link) => {
              const isActive = activeHash === link.href;
              return (
                <a
                  key={link.name}
                  href={link.href}
                  onClick={(e) => handleLinkClick(e, link)}
                  className={`text-sm font-medium px-3 py-1.5 rounded-lg transition-colors focus-visible:ring-2 focus-visible:ring-electric ${
                    isActive
                      ? "text-electric bg-slate-100 font-semibold"
                      : "text-text-secondary hover:text-text-primary hover:bg-slate-50"
                  }`}
                >
                  {link.name}
                </a>
              );
            })}
          </nav>

          {/* Right-Side Desktop Actions (Role-Sensitive) */}
          <div className="hidden sm:flex items-center gap-2 lg:gap-3">
            {/* Theme Toggle Control */}
            <ThemeToggle size="sm" />

            {session && user ? (
              <>
                <Button
                  variant="outline"
                  size="sm"
                  icon={LayoutDashboard}
                  onClick={handleDashboardClick}
                  className="text-text-secondary hover:text-midnight font-medium text-xs lg:text-sm"
                >
                  Dashboard
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={Shield}
                  onClick={handleAdminClick}
                  className="text-text-secondary hover:text-midnight font-medium text-xs lg:text-sm"
                >
                  Admin
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={LogOut}
                  onClick={handleSignOut}
                  className="text-text-muted hover:text-rose-600 font-medium text-xs lg:text-sm"
                  title="Sign Out"
                >
                  Sign Out
                </Button>
              </>
            ) : (
              <>
                <Button
                  variant="ghost"
                  size="sm"
                  icon={Shield}
                  onClick={handleAdminClick}
                  className="text-text-secondary hover:text-midnight font-medium text-xs lg:text-sm"
                >
                  Admin Portal
                </Button>

                <Button
                  variant="outline"
                  size="sm"
                  icon={Lock}
                  onClick={handleLoginClick}
                  className="text-text-secondary hover:text-midnight font-medium text-xs lg:text-sm"
                >
                  Employee Login
                </Button>

                <Button
                  variant="primary"
                  size="sm"
                  icon={ArrowRight}
                  iconPosition="right"
                  onClick={handleGetStartedClick}
                  className="text-xs lg:text-sm"
                >
                  Explore Platform
                </Button>
              </>
            )}
          </div>

          {/* Mobile Actions: Theme Toggle + Hamburger Toggle Button */}
          <div className="flex items-center gap-2 sm:hidden">
            <ThemeToggle size="sm" />
            <IconButton
              icon={mobileMenuOpen ? X : Menu}
              label={mobileMenuOpen ? "Close navigation menu" : "Open navigation menu"}
              variant="subtle"
              size="md"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              aria-expanded={mobileMenuOpen}
              aria-controls="mobile-navigation-drawer"
            />
          </div>
        </Container>

        {/* Mobile Drawer Menu Overlay */}
        <AnimatePresence>
          {mobileMenuOpen && (
            <motion.div
              id="mobile-navigation-drawer"
              ref={menuRef}
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
              className="md:hidden border-b border-border bg-surface px-4 pt-3 pb-6 shadow-card overflow-hidden"
            >
              <nav className="flex flex-col gap-1 mb-5" aria-label="Mobile Navigation">
                {navLinks.map((link) => {
                  const isActive = activeHash === link.href;
                  return (
                    <a
                      key={link.name}
                      href={link.href}
                      onClick={(e) => handleLinkClick(e, link)}
                      className={`flex items-center justify-between text-base font-medium py-2.5 px-3 rounded-lg transition-colors ${
                        isActive
                          ? "bg-slate-100 text-electric font-semibold"
                          : "text-text-primary hover:bg-bg active:bg-border/60"
                      }`}
                    >
                      <span>{link.name}</span>
                      <ChevronRight className="w-4 h-4 text-text-muted" />
                    </a>
                  );
                })}
              </nav>

              <div className="flex flex-col gap-2.5 pt-3 border-t border-border">
                {session && user ? (
                  <>
                    <Button
                      variant="primary"
                      size="md"
                      icon={LayoutDashboard}
                      onClick={handleDashboardClick}
                      className="w-full justify-center"
                    >
                      Open Intelligence Dashboard
                    </Button>
                    <Button
                      variant="ghost"
                      size="md"
                      icon={Shield}
                      onClick={handleAdminClick}
                      className="w-full justify-center"
                    >
                      Admin Portal
                    </Button>
                    <Button
                      variant="outline"
                      size="md"
                      icon={LogOut}
                      onClick={handleSignOut}
                      className="w-full justify-center text-rose-600 hover:text-rose-700"
                    >
                      Sign Out ({user.email})
                    </Button>
                  </>
                ) : (
                  <>
                    <Button
                      variant="outline"
                      size="md"
                      icon={Lock}
                      onClick={handleLoginClick}
                      className="w-full justify-center"
                    >
                      Employee Sign In
                    </Button>
                    <Button
                      variant="ghost"
                      size="md"
                      icon={Shield}
                      onClick={handleAdminClick}
                      className="w-full justify-center"
                    >
                      Admin Portal
                    </Button>
                    <Button
                      variant="primary"
                      size="md"
                      icon={ArrowRight}
                      iconPosition="right"
                      onClick={handleGetStartedClick}
                      className="w-full justify-center"
                    >
                      Explore Platform
                    </Button>
                  </>
                )}

                {/* Mobile Drawer Theme Toggle Row */}
                <div className="pt-2.5 border-t border-border flex items-center justify-between">
                  <span className="text-xs font-mono text-text-muted">Appearance Theme</span>
                  <ThemeToggle variant="pill" size="sm" />
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </header>

      {/* Backdrop for click-outside closing on mobile */}
      {mobileMenuOpen && (
        <div
          onClick={() => setMobileMenuOpen(false)}
          className="fixed inset-0 top-[65px] bg-midnight/40 backdrop-blur-xs z-40 md:hidden"
          aria-hidden="true"
        />
      )}
    </>
  );
}
