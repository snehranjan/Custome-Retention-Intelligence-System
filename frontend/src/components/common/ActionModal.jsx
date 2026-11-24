import React, { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, CheckCircle2, ArrowRight } from "lucide-react";
import { Button } from "../ui/Button";

/**
 * RetainIQ Action Feedback Modal
 * Displays accessible modal dialogues explaining future roadmap milestones.
 */
  export function ActionModal({ isOpen, onClose, data, onNavigate }) {
    useEffect(() => {
      const handleKeyDown = (e) => {
        if (e.key === "Escape" && isOpen) {
          onClose();
        }
      };
      window.addEventListener("keydown", handleKeyDown);
      return () => window.removeEventListener("keydown", handleKeyDown);
    }, [isOpen, onClose]);

    if (!isOpen || !data) return null;

    const Icon = data.icon || CheckCircle2;

    return (
      <AnimatePresence>
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-midnight/60 backdrop-blur-sm"
          />

          {/* Modal Window */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 15 }}
            transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }}
            className="relative w-full max-w-md bg-surface border border-border rounded-2xl shadow-elevated p-6 sm:p-7 z-10 overflow-hidden"
            role="dialog"
            aria-modal="true"
          >
            {/* Close button */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 p-2 rounded-xl text-text-secondary hover:text-text-primary hover:bg-bg transition-colors focus-visible:ring-2 focus-visible:ring-electric"
              aria-label="Close dialog"
            >
              <X className="w-5 h-5" />
            </button>

            {/* Icon Badge */}
            <div className="w-12 h-12 rounded-2xl bg-electric/10 text-electric border border-electric/20 flex items-center justify-center mb-4">
              <Icon className="w-6 h-6" />
            </div>

            {/* Content */}
            <div className="mb-6">
              <span className="text-[11px] font-heading font-bold uppercase tracking-wider text-electric block mb-1">
                {data.subtitle || "System Notice"}
              </span>
              <h3 className="font-heading text-xl font-bold text-midnight tracking-tight mb-3">
                {data.title}
              </h3>
              <p className="text-sm text-text-secondary leading-relaxed">
                {data.message}
              </p>
            </div>

                {/* Action buttons */}
                <div className="flex flex-col sm:flex-row justify-end gap-2.5 pt-4 border-t border-border">
                  {data?.actionRoute && onNavigate && (
                    <Button
                      variant="primary"
                      size="md"
                      onClick={() => {
                        onClose();
                        onNavigate(data.actionRoute);
                      }}
                      className="w-full sm:w-auto font-semibold"
                    >
                      {data.actionLabel || "Proceed to Sign In"}
                    </Button>
                  )}
                  <Button
                    variant={data?.actionRoute ? "ghost" : "primary"}
                    size="md"
                    onClick={onClose}
                    className="w-full sm:w-auto"
                  >
                    {data?.actionRoute ? "Dismiss" : "Understood"}
                  </Button>
                </div>
              </motion.div>
            </div>
          </AnimatePresence>
          );
}
