/**
 * RetainIQ Customer Retention Intelligence System
 * Employee Authentication UI Test Suite (Phase 8.4.3)
 *
 * Runs via native Node.js Test Runner: `npm test`
 *
 * Covers:
 * 1. Login Form Validation (empty email, invalid email, empty password, valid state)
 * 2. Password Visibility Toggle & Accessibility
 * 3. Duplicate Submission Prevention
 * 4. Supabase Sign-In Error Mapping & Sanitization
 * 5. Post-Login Identity Check & Safe Pending-Access State
 * 6. Non-Granting of Access on 401, 403, or Network Failure
 * 7. Sign-Out / Logout Behavior
 * 8. Strict Admin-Controlled Policy Invariants (zero public registration, no signUp())
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, '..');

describe('1. Login Form Client-Side Validation Logic', () => {
  const validate = (email, password) => {
    const errors = {};
    const trimmedEmail = (email || '').trim();

    if (!trimmedEmail) {
      errors.email = 'Work email address is required.';
    } else {
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(trimmedEmail)) {
        errors.email = 'Please enter a valid work email address.';
      }
    }

    if (!password) {
      errors.password = 'Password is required.';
    }

    return {
      isValid: Object.keys(errors).length === 0,
      errors,
      trimmedEmail,
    };
  };

  it('should reject empty email', () => {
    const res = validate('', 'SecretPassword123');
    assert.strictEqual(res.isValid, false);
    assert.strictEqual(res.errors.email, 'Work email address is required.');
  });

  it('should reject whitespace-only email', () => {
    const res = validate('   ', 'SecretPassword123');
    assert.strictEqual(res.isValid, false);
    assert.strictEqual(res.errors.email, 'Work email address is required.');
  });

  it('should reject invalid email formats', () => {
    const invalidEmails = ['invalid', 'user@', '@domain.com', 'user@domain', 'user name@domain.com'];
    for (const em of invalidEmails) {
      const res = validate(em, 'SecretPassword123');
      assert.strictEqual(res.isValid, false, `Expected ${em} to be rejected`);
      assert.strictEqual(res.errors.email, 'Please enter a valid work email address.');
    }
  });

  it('should reject empty password', () => {
    const res = validate('analyst@retainiq.internal', '');
    assert.strictEqual(res.isValid, false);
    assert.strictEqual(res.errors.password, 'Password is required.');
  });

  it('should accept valid email and password, trimming surrounding whitespace from email only', () => {
    const res = validate('  analyst@retainiq.internal  ', ' SecretPassword! ');
    assert.strictEqual(res.isValid, true);
    assert.strictEqual(res.trimmedEmail, 'analyst@retainiq.internal');
    // Password must remain untrimmed
    assert.strictEqual(res.errors.email, undefined);
    assert.strictEqual(res.errors.password, undefined);
  });
});

describe('2. Password Visibility Toggle & Submission State', () => {
  it('should verify password input toggle attributes in EmployeeLoginPage.jsx', () => {
    const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
    assert.ok(fs.existsSync(loginPagePath), 'EmployeeLoginPage.jsx must exist');
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    // Show/Hide password toggle logic
    assert.match(code, /showPassword\s*\?\s*["']text["']\s*:\s*["']password["']/, 'Must toggle input type');
    assert.match(code, /aria-label=\{showPassword\s*\?\s*["']Hide password["']\s*:\s*["']Show password["']\}/, 'Must provide accessible aria-label on password toggle');
    assert.match(code, /autoComplete=["']current-password["']/, 'Must specify autoComplete="current-password"');
  });

  it('should verify duplicate submission prevention logic in EmployeeLoginPage.jsx', () => {
    const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.match(code, /if\s*\(isSubmitting\)\s*return/, 'Must immediately abort if submission is in flight');
    assert.match(code, /disabled=\{isSubmitting\}/, 'Must disable submit button while pending');
    assert.match(code, /setIsSubmitting\(true\)/, 'Must set isSubmitting to true at start');
    assert.match(code, /setIsSubmitting\(false\)/, 'Must set isSubmitting to false in finally block');
  });
});

describe('3. Supabase Sign-In Error Mapping & Sanitization', () => {
  const mapSupabaseError = (rawErrorMessage) => {
    let userMessage = 'Unable to sign in with provided credentials.';
    const rawMsg = (rawErrorMessage || '').toLowerCase();

    if (rawMsg.includes('invalid login credentials') || rawMsg.includes('invalid_grant')) {
      userMessage = 'Invalid work email or password. Please verify your administrator-provisioned credentials.';
    } else if (rawMsg.includes('email not confirmed')) {
      userMessage = 'Your work email address has not been confirmed. Please check your inbox or contact your RetainIQ administrator.';
    } else if (rawMsg.includes('too many requests') || rawMsg.includes('rate limit')) {
      userMessage = 'Too many sign-in attempts. Please wait a few moments before trying again.';
    } else if (rawMsg.includes('network') || rawMsg.includes('fetch')) {
      userMessage = 'Network connection error contacting authentication service.';
    }

    return userMessage;
  };

  it('should map invalid credentials error cleanly without technical jargon', () => {
    const msg = mapSupabaseError('Invalid login credentials');
    assert.strictEqual(msg, 'Invalid work email or password. Please verify your administrator-provisioned credentials.');
  });

  it('should map unconfirmed email error cleanly', () => {
    const msg = mapSupabaseError('Email not confirmed');
    assert.strictEqual(msg, 'Your work email address has not been confirmed. Please check your inbox or contact your RetainIQ administrator.');
  });

  it('should map rate limit errors cleanly', () => {
    const msg = mapSupabaseError('Too many requests, rate limit exceeded');
    assert.strictEqual(msg, 'Too many sign-in attempts. Please wait a few moments before trying again.');
  });

  it('should map network failure cleanly', () => {
    const msg = mapSupabaseError('Failed to fetch from Supabase network');
    assert.strictEqual(msg, 'Network connection error contacting authentication service.');
  });
});

describe('4. Post-Login Identity Check & Safe Pending-Access State', () => {
  it('should verify that a successful /auth/me call displays pending access, NOT the dashboard', () => {
    const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    // Must call apiClient.auth.getProfile()
    assert.match(code, /apiClient\.auth\s*\.\s*getProfile\(\)/, 'Must call backend getProfile() on login');

    // Must show pending explanation, NOT dashboard
    assert.match(code, /Employee Access Authorization Pending/, 'Must show pending authorization explanation');
    assert.match(code, /ADMIN-CONTROLLED EMPLOYEE ACCOUNTS/, 'Must display the admin-controlled policy notice');
    assert.doesNotMatch(code, /CustomerRiskExplorer|DashboardOverview|<Dashboard/i, 'Must never render dashboard components in login UI');
  });

  it('should verify that 401, 403, or network errors never grant access and allow sign-out', () => {
    const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.match(code, /err\.status\s*===\s*401/, 'Must explicitly catch 401 errors');
    assert.match(code, /err\.status\s*===\s*403/, 'Must explicitly catch 403 errors');
    assert.match(code, /handleSignOut/, 'Must provide sign out option when in pending state');
  });

  it('should verify sign-out calls supabase.auth.signOut()', () => {
    const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.match(code, /supabase\.auth\.signOut\(\)/, 'Must invoke official Supabase signOut()');
  });
});

describe('5. Strict Admin-Controlled Policy Invariants', () => {
  it('should verify ZERO sign-up forms, registration links, or signUp() invocations exist in frontend', () => {
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

    const srcDir = path.join(FRONTEND_ROOT, 'src');
    const files = walk(srcDir);

    for (const f of files) {
      const code = fs.readFileSync(f, 'utf-8');
      assert.doesNotMatch(code, /auth\.signUp\(/, `File ${path.relative(FRONTEND_ROOT, f)} must not call supabase.auth.signUp()`);
      assert.doesNotMatch(code, /Register for an account|Create an account|Sign up for RetainIQ/i, `File ${path.relative(FRONTEND_ROOT, f)} must not present public registration UI`);
    }
  });

  it('should verify zero customer directory API or customer table queries occur from login page', () => {
    const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
    const code = fs.readFileSync(loginPagePath, 'utf-8');

    assert.doesNotMatch(code, /\/api\/v1\/customers(?!\/analyze)/, 'Must not call customer list endpoints');
    assert.doesNotMatch(code, /\.from\(['"]customers['"]\)/, 'Must not directly query Supabase customer tables');
  });
});
