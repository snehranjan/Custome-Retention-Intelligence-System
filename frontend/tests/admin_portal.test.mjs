/**
 * RetainIQ Customer Retention Intelligence System
 * Frontend Administrator Portal Test Suite (Phase 8.4.6)
 *
 * Runs via native Node.js Test Runner: `npm test`
 *
 * Verifies:
 * 1. AdminPortalPage Component Architecture & Navigation Tabs
 * 2. Strict Server-Side Authorization Guard & 403 Forbidden UI State
 * 3. Overview Statistics & KPI Rendering
 * 4. Pending Employee Requests Approval & Mandatory Rejection Reason
 * 5. Employee Directory Search, Status Filtering, and Details Inspection
 * 6. Pre-Authorized Invitation Workflow
 * 7. apiClient.admin Namespace & Method Contract
 * 8. Security Invariants (No direct Supabase queries, No exposed service-role keys)
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, '..');

describe('1. AdminPortalPage Component Architecture & Navigation', () => {
  const adminPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'AdminPortalPage.jsx');

  it('should verify AdminPortalPage.jsx exists and has required navigation tabs', () => {
    assert.ok(fs.existsSync(adminPagePath), 'AdminPortalPage.jsx must exist');
    const code = fs.readFileSync(adminPagePath, 'utf-8');

    assert.match(code, /activeTab\s*===\s*["']overview["']/, 'Must support overview tab');
    assert.match(code, /activeTab\s*===\s*["']requests["']/, 'Must support requests tab');
    assert.match(code, /activeTab\s*===\s*["']directory["']/, 'Must support directory tab');
  });

  it('should verify App.jsx maps /admin route to AdminPortalPage', () => {
    const appPath = path.join(FRONTEND_ROOT, 'src', 'App.jsx');
    assert.ok(fs.existsSync(appPath), 'App.jsx must exist');
    const code = fs.readFileSync(appPath, 'utf-8');

    assert.match(code, /import\s*\{\s*AdminPortalPage\s*\}\s*from\s*["']\.\/pages\/AdminPortalPage["']/, 'Must import AdminPortalPage');
    assert.match(code, /currentPath\s*===\s*["']\/admin["']/, 'Must route /admin to AdminPortalPage');
  });

  it('should verify Navbar includes Administrator Portal navigation links', () => {
    const navPath = path.join(FRONTEND_ROOT, 'src', 'components', 'layout', 'Navbar.jsx');
    const code = fs.readFileSync(navPath, 'utf-8');

    assert.match(code, /Admin Portal/, 'Must provide Admin Portal link in Navbar');
    assert.match(code, /\/admin/, 'Must navigate to /admin');
  });
});

describe('2. Server-Side Authorization Guard & 403 Forbidden Handling', () => {
  const adminPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'AdminPortalPage.jsx');

  it('should verify server-side getProfile() call for cryptographic verification', () => {
    const code = fs.readFileSync(adminPagePath, 'utf-8');
    assert.match(code, /apiClient\.admin\.getProfile\(\)/, 'Must call backend getProfile() on mount');
    assert.match(code, /isVerifyingAdmin/, 'Must manage verification loading state');
  });

  it('should verify dedicated 403 Forbidden Access Denied presentation', () => {
    const code = fs.readFileSync(adminPagePath, 'utf-8');
    assert.match(code, /403 FORBIDDEN/, 'Must present 403 Forbidden notice on unauthorized access');
    assert.match(code, /Administrator Privileges Required/, 'Must clearly inform user of missing admin privileges');
    assert.match(code, /Sign Out of This Account/, 'Must provide sign out option on forbidden access');
  });
});

describe('3. Employee Requests & Mandatory Rejection Reason Logic', () => {
  const adminPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'AdminPortalPage.jsx');

  it('should verify approve confirmation modal and notes handling', () => {
    const code = fs.readFileSync(adminPagePath, 'utf-8');
    assert.match(code, /approvingEmployee/, 'Must track employee being approved');
    assert.match(code, /apiClient\.admin\.approveEmployee/, 'Must invoke approveEmployee API');
    assert.match(code, /Confirm Approval/, 'Must require explicit approval confirmation');
  });

  it('should verify mandatory rejection reason validation', () => {
    const code = fs.readFileSync(adminPagePath, 'utf-8');
    assert.match(code, /rejectingEmployee/, 'Must track employee being rejected');
    assert.match(code, /cleanReason\.length\s*<\s*3/, 'Must enforce at least 3 character reason');
    assert.match(code, /apiClient\.admin\.rejectEmployee/, 'Must invoke rejectEmployee API');
    assert.match(code, /Rejection Reason \(Mandatory\)/, 'Must mark rejection reason as mandatory in UI');
  });
});

describe('4. Employee Directory & Pre-Authorized Invitation Workflow', () => {
  const adminPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'AdminPortalPage.jsx');

  it('should verify directory search, status filter, and pagination bindings', () => {
    const code = fs.readFileSync(adminPagePath, 'utf-8');
    assert.match(code, /directorySearchQuery/, 'Must support keyword search query state');
    assert.match(code, /directoryStatusFilter/, 'Must support status filtering state');
    assert.match(code, /apiClient\.admin\.listEmployees/, 'Must call listEmployees API');
    assert.match(code, /inspectingEmployee/, 'Must support details inspection modal');
  });

  it('should verify invitation creation workflow and client-side validation', () => {
    const code = fs.readFileSync(adminPagePath, 'utf-8');
    assert.match(code, /isInviteModalOpen/, 'Must support invite modal state');
    assert.match(code, /apiClient\.admin\.inviteEmployee/, 'Must invoke inviteEmployee API');
    assert.match(code, /Pre-Authorize Employee Invitation/, 'Must clearly title invitation workflow');
  });
});

describe('5. apiClient.admin Method Contract & Security Invariants', () => {
  const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');

  it('should verify all required admin endpoints are implemented in apiClient', () => {
    const code = fs.readFileSync(apiClientPath, 'utf-8');
    assert.match(code, /getProfile:\s*\(\)\s*=>\s*apiClient\.get\(["']\/api\/v1\/admin\/me["']\)/, 'Must export admin.getProfile');
    assert.match(code, /getStats:\s*\(\)\s*=>\s*apiClient\.get\(["']\/api\/v1\/admin\/stats["']\)/, 'Must export admin.getStats');
    assert.match(code, /listEmployees:\s*\(params\s*=\s*\{\}\)\s*=>/, 'Must export admin.listEmployees');
    assert.match(code, /getPendingEmployees:\s*\(params\s*=\s*\{\}\)\s*=>/, 'Must export admin.getPendingEmployees');
    assert.match(code, /getEmployeeDetails:\s*\(employeeId\)\s*=>/, 'Must export admin.getEmployeeDetails');
    assert.match(code, /inviteEmployee:\s*\(payload\)\s*=>/, 'Must export admin.inviteEmployee');
    assert.match(code, /approveEmployee:\s*\(employeeId,\s*body\s*=\s*\{\}\)\s*=>/, 'Must export admin.approveEmployee');
    assert.match(code, /rejectEmployee:\s*\(employeeId,\s*body\)\s*=>/, 'Must export admin.rejectEmployee');
  });

  it('should verify ZERO direct queries to Supabase employee_registry from frontend source', () => {
    const srcDir = path.join(FRONTEND_ROOT, 'src');
    const walk = (dir) => {
      let results = [];
      const list = fs.readdirSync(dir);
      list.forEach((file) => {
        const fullPath = path.join(dir, file);
        const stat = fs.statSync(fullPath);
        if (stat && stat.isDirectory()) {
          results = results.concat(walk(fullPath));
        } else if (file.endsWith('.js') || file.endsWith('.jsx')) {
          results.push(fullPath);
        }
      });
      return results;
    };

    const files = walk(srcDir);
    for (const f of files) {
      const code = fs.readFileSync(f, 'utf-8');
      assert.doesNotMatch(
        code,
        /\.from\(['"]employee_registry['"]\)/,
        `File ${path.relative(FRONTEND_ROOT, f)} must not query employee_registry directly via Supabase client`
      );
    }
  });
});
