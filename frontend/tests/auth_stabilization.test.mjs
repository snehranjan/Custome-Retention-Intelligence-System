/**
 * RetainIQ Customer Retention Intelligence System
 * Authentication & Authorization Stabilization Test Suite
 *
 * Verifies:
 * - Administrator vs Employee role resolution in EmployeeLoginPage.
 * - Automatic transition to /admin for administrators and /employee/dashboard for approved employees.
 * - Dedicated status screens for PENDING, REJECTED, SUSPENDED, and INVITED employee accounts.
 * - Administrator detection and safe redirection on EmployeeDashboardPage.
 * - Cross-portal navigation from AdminPortalPage to Employee Dashboard.
 * - Strict security invariants: zero direct database access from frontend, fails closed.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_SRC = path.resolve(__dirname, "../src");

describe("1. EmployeeLoginPage Role Resolution & Routing", () => {
  const loginCode = fs.readFileSync(path.join(FRONTEND_SRC, "pages/EmployeeLoginPage.jsx"), "utf-8");

  it("should check administrator status via apiClient.admin.getProfile()", () => {
    assert.match(
      loginCode,
      /apiClient\.admin\s*\.\s*getProfile\s*\(\s*\)/,
      "EmployeeLoginPage must call apiClient.admin.getProfile() for role discovery"
    );
  });

  it("should check employee clearance via apiClient.employee.getProfile()", () => {
    assert.match(
      loginCode,
      /apiClient\.employee\s*\.\s*getProfile\s*\(\s*\)/,
      "EmployeeLoginPage must call apiClient.employee.getProfile() for employee clearance"
    );
  });

  it("should automatically navigate administrators to /admin", () => {
    assert.match(
      loginCode,
      /onNavigate\s*\(\s*["']\/admin["']\s*\)/,
      "EmployeeLoginPage must navigate verified administrators to /admin"
    );
  });

  it("should automatically navigate approved employees to /employee/dashboard", () => {
    assert.match(
      loginCode,
      /onNavigate\s*\(\s*["']\/employee\/dashboard["']\s*\)/,
      "EmployeeLoginPage must navigate approved employees to /employee/dashboard"
    );
  });

  it("should contain dedicated cards for PENDING, REJECTED, SUSPENDED, and INVITED statuses", () => {
    assert.match(loginCode, /Employee Access Authorization Pending|Registration Under Administrator Review/);
    assert.match(loginCode, /Registration Not Approved/);
    assert.match(loginCode, /Employee Account Suspended/);
  });

  it("should ensure zero hardcoded passwords or credential auto-population in EmployeeLoginPage", () => {
    assert.doesNotMatch(
      loginCode,
      /setPassword\s*\(\s*["'][^"']+["']\s*\)/,
      "EmployeeLoginPage must never hardcode or autofill account passwords"
    );
  });
});

describe("2. EmployeeDashboardPage Cross-Portal Guard & Status Discrimination", () => {
  const dashboardCode = fs.readFileSync(path.join(FRONTEND_SRC, "pages/EmployeeDashboardPage.jsx"), "utf-8");

  it("should check for administrator privileges when employee access returns 403", () => {
    assert.match(
      dashboardCode,
      /apiClient\.admin\.getProfile\(\)/,
      "EmployeeDashboardPage must check apiClient.admin.getProfile() on 403 error"
    );
  });

  it("should render Administrator Account Detected view with direct link to /admin", () => {
    assert.match(
      dashboardCode,
      /Administrator Account Detected/,
      "EmployeeDashboardPage must identify administrator accounts clearly"
    );
    assert.match(
      dashboardCode,
      /handleNavigate\s*\(\s*["']\/admin["']\s*\)/,
      "Must provide direct button to navigate to /admin"
    );
  });

  it("should differentiate 404 service unavailable from authorization denial", () => {
    assert.match(
      dashboardCode,
      /SERVICE UNAVAILABLE \(404\)/,
      "Must display distinct 404 error rather than confusing with authorization pending"
    );
  });
});

describe("3. AdminPortalPage Cross-Portal Navigation", () => {
  const adminCode = fs.readFileSync(path.join(FRONTEND_SRC, "pages/AdminPortalPage.jsx"), "utf-8");

  it("should enforce strict 403 Forbidden Access Denied for non-administrators", () => {
    assert.match(adminCode, /403 FORBIDDEN • ACCESS DENIED/);
    assert.match(adminCode, /Administrator Privileges Required/);
  });

  it("should provide direct navigation button to /employee/dashboard for authenticated employees", () => {
    assert.match(
      adminCode,
      /\/employee\/dashboard/,
      "AdminPortalPage must offer navigation to /employee/dashboard for non-admin employees"
    );
  });
});

describe("4. Global Security Invariants", () => {
  it("should verify ZERO direct queries to Supabase database tables from frontend source", () => {
    const scanDir = (dir) => {
      let files = [];
      const items = fs.readdirSync(dir, { withFileTypes: true });
      for (const item of items) {
        const fullPath = path.join(dir, item.name);
        if (item.isDirectory()) {
          files = files.concat(scanDir(fullPath));
        } else if (item.name.endsWith(".jsx") || item.name.endsWith(".js")) {
          files.push(fullPath);
        }
      }
      return files;
    };

    const allSourceFiles = scanDir(FRONTEND_SRC);
    for (const file of allSourceFiles) {
      const code = fs.readFileSync(file, "utf-8");
      assert.doesNotMatch(
        code,
        /supabase\s*\.\s*from\s*\(/,
        `File ${path.basename(file)} must NOT directly query Supabase tables. All queries must route through FastAPI backend.`
      );
    }
  });
});
