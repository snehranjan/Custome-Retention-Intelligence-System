/**
 * RetainIQ Customer Retention Intelligence System
 * Shared Supabase Client Module (Phase 8.4.2)
 *
 * Requirements:
 * - Singleton client instance configured with public publishable key only.
 * - Reads only VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY.
 * - Persistent browser session storage and automated token refresh enabled.
 * - Never includes or exposes secret/service-role credentials.
 */

import { createClient } from "@supabase/supabase-js";

const supabaseUrl =
  import.meta.env.VITE_SUPABASE_URL ||
  "https://hyngxdkuanugcvqhkaas.supabase.co";
const supabaseAnonKey =
  import.meta.env.VITE_SUPABASE_PUBLISHABLE_KEY ||
  "sb_publishable_NaJSKZOjztFxbMD_SOY0xA_aqwuEPf1";

export const isSupabaseConfigured = () => {
  return Boolean(
    supabaseUrl &&
    typeof supabaseUrl === "string" &&
    supabaseUrl.startsWith("https://") &&
    supabaseAnonKey &&
    typeof supabaseAnonKey === "string" &&
    supabaseAnonKey.length > 10
  );
};

if (!isSupabaseConfigured()) {
  console.warn(
    "[RetainIQ Auth] Supabase environment variables are missing or incomplete. " +
    "Verify VITE_SUPABASE_URL and VITE_SUPABASE_PUBLISHABLE_KEY in .env.local."
  );
}

export const supabase = isSupabaseConfigured()
  ? createClient(supabaseUrl, supabaseAnonKey, {
      auth: {
        persistSession: true,
        autoRefreshToken: true,
        detectSessionInUrl: true,
        storageKey: "retainiq_auth_session",
      },
    })
  : null;
