/**
 * RetainIQ Customer Retention Intelligence System
 * Authentication Context & Hook (Phase 8.4.2)
 *
 * Requirements:
 * - Provides: session, user, isLoading, isAuthenticated, authError
 * - Synchronously handles INITIAL_SESSION, SIGNED_IN, SIGNED_OUT, TOKEN_REFRESHED, USER_UPDATED
 * - Graceful unmount cleanup without duplicate listeners or stale state updates
 * - No asynchronous network calls inside auth-state change callbacks
 * - Sensitive credentials (tokens, secrets) are NEVER logged
 */

import React, { createContext, useContext, useEffect, useState, useMemo } from "react";
import { supabase } from "../lib/supabase";

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [authError, setAuthError] = useState(null);

  useEffect(() => {
    let isMounted = true;

    if (!supabase) {
      if (isMounted) {
        setIsLoading(false);
      }
      return;
    }

    // 1. Initial Session Retrieval via getSession()
    supabase.auth
      .getSession()
      .then(({ data: { session: initialSession }, error }) => {
        if (!isMounted) return;
        if (error) {
          setAuthError(error);
        } else {
          setSession(initialSession);
          setUser(initialSession?.user ?? null);
          setAuthError(null);
        }
      })
      .catch((err) => {
        if (!isMounted) return;
        setAuthError(err);
      })
      .finally(() => {
        if (isMounted) {
          setIsLoading(false);
        }
      });

    // 2. Auth State Change Listener
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((event, currentSession) => {
      if (!isMounted) return;

      // Handle documented auth events synchronously
      switch (event) {
        case "INITIAL_SESSION":
        case "SIGNED_IN":
        case "TOKEN_REFRESHED":
        case "USER_UPDATED":
          setSession(currentSession);
          setUser(currentSession?.user ?? null);
          setAuthError(null);
          setIsLoading(false);
          break;
        case "SIGNED_OUT":
          setSession(null);
          setUser(null);
          setAuthError(null);
          setIsLoading(false);
          break;
        default:
          if (currentSession) {
            setSession(currentSession);
            setUser(currentSession.user ?? null);
          }
          break;
      }
    });

    // Cleanup subscription and unmount protection
    return () => {
      isMounted = false;
      if (subscription && typeof subscription.unsubscribe === "function") {
        subscription.unsubscribe();
      }
    };
  }, []);

  const value = useMemo(
    () => ({
      session,
      user,
      isLoading,
      isAuthenticated: Boolean(session?.access_token && user),
      authError,
    }),
    [session, user, isLoading, authError]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
};
