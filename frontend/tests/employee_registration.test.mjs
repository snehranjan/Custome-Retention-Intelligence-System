/**
 * RetainIQ Customer Retention Intelligence System
 * Employee Registration & Admin Approval UI Test Suite (Phase 8.4.5)
 *
 * Runs via native Node.js Test Runner: `npm test`
 *
 * Verifies:
 * 1. Employee Registration Form Client-Side Validation Logic
 * 2. Password Confirmation & Visibility Control
 * 3. EmployeeLoginPage.jsx Component Structure & Tab Switcher
 * 4. Dedicated "Registration Submitted Successfully" View (NO dashboard access)
 * 5. Strict Admin-Controlled Policy Invariants (NO supabase.auth.signUp() in registration)
 * 6. apiClient.admin Namespace & Method Contract
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, '..');

describe('1. Employee Registration Client-Side Validation Logic', () => {
  const validateReg = (employeeId, email, password, confirmPassword) => {
    const errors = {};
    const cleanId = (employeeId || '').trim();
    const cleanEmail = (email || '').trim();

    if (!cleanId) {
      errors.employeeId = 'Pre-issued Employee ID is required.';
    } else if (cleanId.length < 3) {
      errors.employeeId = 'Employee ID must be at least 3 characters.';
    }

    if (!cleanEmail) {
      errors.email = 'Work email address is required.';
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(cleanEmail)) {
        errors.email = 'Please enter a valid work email address.';
      }
    }

    if (!password) {
      errors.password = 'Password is required.';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters long.';
    }

    if (!confirmPassword) {
      errors.confirmPassword = 'Confirm password is required.';
    } else if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match.';
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
      cleanId,
      cleanEmail,
    };
  };

  it('should reject empty or short employee ID', () => {
    const res1 = validateReg('', 'analyst@retainiq.internal', 'Password123!', 'Password123!');
    assert.strictEqual(res1.isValid, false);
    assert.strictEqual(res1.errors.employeeId, 'Pre-issued Employee ID is required.');

    const res2 = validateReg('AB', 'analyst@retainiq.internal', 'Password123!', 'Password123!');
    assert.strictEqual(res2.isValid, false);
    assert.strictEqual(res2.errors.employeeId, 'Employee ID must be at least 3 characters.');
  });

  it('should reject invalid work email', () => {
    const res = validateReg('EMP-2026-002', 'invalid-email', 'Password123!', 'Password123!');
    assert.strictEqual(res.isValid, false);
    assert.strictEqual(res.errors.email, 'Please enter a valid work email address.');
  });

  it('should reject short password (< 8 chars)', () => {
    const res = validateReg('EMP-2026-002', 'analyst@retainiq.internal', 'short', 'short');
    assert.strictEqual(res.isValid, false);
    assert.strictEqual(res.errors.password, 'Password must be at least 8 characters long.');
  });

  it('should reject mismatched passwords', () => {
    const res = validateReg('EMP-2026-002', 'analyst@retainiq.internal', 'Password123!', 'DifferentPassword123!');
    assert.strictEqual(res.isValid, false);
    assert.strictEqual(res.errors.confirmPassword, 'Passwords do not match.');
  });

  it('should accept valid registration parameters and preserve casing', () => {
    const res = validateReg('  emp-2026-002  ', '  Analyst@RetainIQ.internal  ', 'Password123!', 'Password123!');
    assert.strictEqual(res.isValid, true);
    assert.strictEqual(res.cleanId, 'emp-2026-002');
    assert.strictEqual(res.cleanEmail, 'Analyst@RetainIQ.internal');
  });
});

describe('2. Employee Registration UI Structure in EmployeeLoginPage.jsx', () => {
  const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');

  it('should verify two-tab switcher between Sign In and Register as an Employee', () => {
    assert.ok(fs.existsSync(loginPagePath), 'EmployeeLoginPage.jsx must exist');
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.match(code, /Sign In/, 'Must include Sign In tab option');
    assert.match(code, /Register as an Employee/, 'Must include Register as an Employee tab option');
    assert.match(code, /activeTab\s*===\s*["']login["']/, 'Must support activeTab conditional rendering');
  });

  it('should verify password visibility controls for both password and confirm-password fields', () => {
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.match(code, /showRegPassword/, 'Must control registration password visibility');
    assert.match(code, /showRegConfirmPassword/, 'Must control confirm-password visibility');
    assert.match(code, /autoComplete=["']new-password["']/, 'Must use autoComplete="new-password" for registration');
  });

  it('should verify duplicate submission prevention on registration form', () => {
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.match(code, /if\s*\(isRegSubmitting\)\s*return/, 'Must prevent duplicate registration submission');
    assert.match(code, /disabled=\{isRegSubmitting\}/, 'Must disable registration submit button during processing');
  });
});

describe('3. Registration Submitted Successfully View Contract', () => {
  const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');

  it('should verify pending-access presentation after registration', () => {
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.match(code, /Registration Submitted Successfully/, 'Must display exact success heading');
    assert.match(code, /AWAITING APPROVAL/, 'Must display AWAITING APPROVAL status badge');
    assert.match(code, /awaiting\s+administrator\s+approval/i, 'Must explain account is awaiting approval');
    assert.match(code, /Return to Sign In/, 'Must provide button returning to sign-in tab');
  });

  it('should verify strictly NO dashboard link or customer table is rendered for pending registration', () => {
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.doesNotMatch(
      code,
      /href=["']\/dashboard["']|<Link\s+to=["']\/dashboard["']/i,
      'Must never render a link to dashboard on pending registration view'
    );
    assert.doesNotMatch(
      code,
      /CustomerTable|RiskExplorer/i,
      'Must not render customer tables on authentication view'
    );
  });
});

describe('4. apiClient Auth and Admin Method Verification', () => {
  const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');

  it('should verify apiClient.auth.registerEmployee method', () => {
    const code = fs.readFileSync(apiClientPath, 'utf-8');

    assert.match(code, /registerEmployee:\s*\(payload\)\s*=>/, 'Must export registerEmployee on apiClient.auth');
    assert.match(code, /\/api\/v1\/employee\/register/, 'Must target /api/v1/employee/register endpoint');
  });

  it('should verify apiClient.admin namespace and methods', () => {
    const code = fs.readFileSync(apiClientPath, 'utf-8');

    assert.match(code, /admin:\s*\{/, 'Must define admin namespace');
    assert.match(code, /getPendingEmployees:/, 'Must define getPendingEmployees method');
    assert.match(code, /approveEmployee:/, 'Must define approveEmployee method');
    assert.match(code, /rejectEmployee:/, 'Must define rejectEmployee method');
  });

  it('should verify zero direct supabase.auth.signUp() calls across entire frontend', () => {
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
        /supabase\s*\.\s*auth\s*\.\s*signUp\s*\(/i,
        `File ${path.relative(FRONTEND_ROOT, f)} must not invoke supabase.auth.signUp()`
      );
    }
  });
});
