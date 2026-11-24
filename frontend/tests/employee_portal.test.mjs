/**
 * RetainIQ Customer Retention Intelligence System
 * Frontend Employee Portal Test Suite (Phase 8.4.7)
 *
 * Runs via native Node.js Test Runner: `npm test`
 *
 * Verifies:
 * 1. EmployeeDashboardPage Component Architecture & Route Integration
 * 2. Strict Server-Side Clearance Guard & Dedicated Status Presentation (Pending, Rejected, Suspended, Invited)
 * 3. Verified Employee Identity & System Connectivity Indicators
 * 4. Sidebar Navigation & Honest Phase 8.4.8 Roadmap Placeholder States
 * 5. apiClient.employee Method Contract & Security Invariants
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, '..');

describe('1. EmployeeDashboardPage Component Architecture & Routing', () => {
  const dashboardPath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeDashboardPage.jsx');
  const appPath = path.join(FRONTEND_ROOT, 'src', 'App.jsx');

  it('should verify EmployeeDashboardPage.jsx exists and defines all 6 Phase 8.4.8 navigation modules', () => {
    assert.ok(fs.existsSync(dashboardPath), 'EmployeeDashboardPage.jsx must exist');
    const code = fs.readFileSync(dashboardPath, 'utf-8');

    assert.match(code, /id:\s*["']overview["']/, 'Must include overview navigation module');
    assert.match(code, /id:\s*["']customers["']/, 'Must include customers navigation module');
    assert.match(code, /id:\s*["']predictions["']/, 'Must include predictions navigation module');
    assert.match(code, /id:\s*["']segments["']/, 'Must include segments navigation module');
    assert.match(code, /id:\s*["']recommendations["']/, 'Must include recommendations navigation module');
    assert.match(code, /id:\s*["']analytics["']/, 'Must include analytics navigation module');
  });

  it('should verify App.jsx maps /employee/dashboard to EmployeeDashboardPage', () => {
    assert.ok(fs.existsSync(appPath), 'App.jsx must exist');
    const code = fs.readFileSync(appPath, 'utf-8');

    assert.match(code, /import\s*\{\s*EmployeeDashboardPage\s*\}\s*from\s*["']\.\/pages\/EmployeeDashboardPage["']/, 'Must import EmployeeDashboardPage');
    assert.match(code, /currentPath\s*===\s*["']\/employee\/dashboard["']/, 'Must route /employee/dashboard to EmployeeDashboardPage');
  });

  it('should verify EmployeeLoginPage provides transition to /employee/dashboard for approved accounts', () => {
    const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.match(code, /\/employee\/dashboard/, 'Must contain route target to /employee/dashboard');
    assert.match(code, /apiClient\.employee\s*\.\s*getProfile\(\)/, 'Must verify employee status via apiClient.employee.getProfile');
  });
});

describe('2. Server-Side Clearance Guard & Dedicated Status Presentation', () => {
  const dashboardPath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeDashboardPage.jsx');

  it('should verify server-side getProfile() invocation on mount', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /apiClient\.employee\.getProfile\(\)/, 'Must call backend getProfile() on mount');
    assert.match(code, /isVerifying/, 'Must maintain verification loading state');
  });

  it('should verify unauthenticated state notice with redirection to login', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /Authentication Required/, 'Must display unauthenticated notice when session is absent');
    assert.match(code, /\/employee\/login/, 'Must link to /employee/login');
  });

  it('should verify dedicated PENDING status review view', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /Registration Under Administrator Review/, 'Must present dedicated pending approval view');
    assert.match(code, /REGISTRATION STATUS:\s*PENDING/, 'Must indicate PENDING status badge');
  });

  it('should verify dedicated REJECTED status view', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /Access Not Approved/, 'Must present dedicated rejected view');
    assert.match(code, /REGISTRATION STATUS:\s*REJECTED/, 'Must indicate REJECTED status badge');
  });

  it('should verify dedicated SUSPENDED status view', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /Account Access Suspended/, 'Must present dedicated suspended view');
    assert.match(code, /ACCOUNT STATUS:\s*SUSPENDED/, 'Must indicate SUSPENDED status badge');
  });
});

describe('3. Verified Identity & Workspace Connectivity Display', () => {
  const dashboardPath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeDashboardPage.jsx');

  it('should verify display of verified employee metadata in Topbar and Welcome banner', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /empName/, 'Must render employee full name');
    assert.match(code, /empId/, 'Must render Employee ID');
    assert.match(code, /empDept/, 'Must render department');
    assert.match(code, /APPROVED/, 'Must display APPROVED status badge');
  });

  it('should verify system connectivity indicators (FastAPI, ES256, Config D, K-Means)', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /FastAPI REST/, 'Must indicate FastAPI REST status');
    assert.match(code, /ES256 JWKS/, 'Must indicate ES256 token verification');
    assert.match(code, /Config D/, 'Must indicate Config D Random Forest inference engine');
    assert.match(code, /K-Means RFM/, 'Must indicate K-Means persona clustering');
  });

  it('should verify secure sign-out implementation', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /supabase\.auth\.signOut\(\)/, 'Must call supabase.auth.signOut');
    assert.match(code, /handleSignOut/, 'Must handle sign out and clear session state');
  });
});

describe('4. Sidebar Navigation & Honest Phase 8.4.8 Roadmap Placeholders', () => {
  const dashboardPath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeDashboardPage.jsx');

  it('should verify honest SCHEDULED FOR PHASE 8.4.8 presentation for non-overview tabs', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /SCHEDULED FOR PHASE 8\.4\.8/, 'Must clearly label placeholder modules with Phase 8.4.8');
    assert.match(code, /Return to Workstation Overview/, 'Must provide return button to overview workstation');
  });

  it('should verify responsive drawer support for mobile and desktop layouts', () => {
    const code = fs.readFileSync(dashboardPath, 'utf-8');
    assert.match(code, /mobileMenuOpen/, 'Must support mobile navigation menu state');
    assert.match(code, /md:flex/, 'Must provide responsive desktop sidebar');
  });
});

describe('5. apiClient.employee Contract & Security Invariants', () => {
  const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');

  it('should verify apiClient.employee.getProfile is defined and targets /api/v1/employee/me', () => {
    const code = fs.readFileSync(apiClientPath, 'utf-8');
    assert.match(code, /employee:\s*\{/, 'Must define employee namespace in apiClient');
    assert.match(code, /getProfile:\s*\(\)\s*=>\s*apiClient\.get\(["']\/api\/v1\/employee\/me["']\)/, 'getProfile must target /api/v1/employee/me');
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
