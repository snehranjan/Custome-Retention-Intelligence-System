/**
 * RetainIQ Customer Retention Intelligence System
 * Customer API Client & Boundary Verification Suite (Phase 8.4.4)
 *
 * Runs via native Node.js Test Runner: `node --test tests/customer_api_client.test.mjs`
 *
 * Verifies:
 * 1. apiClient.customers Namespace & Interface Contract
 * 2. URL and Query String Construction for Directory & Detail Queries
 * 3. HTTP 401 / 403 Error Handling & Permission Discrimination
 * 4. Architecture & Security Invariants (No Direct Supabase Queries, No Premature Customer UI)
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, '..');

describe('1. apiClient.customers Interface & Method Contract', () => {
  it('should verify apiClient source code defines and exports customers namespace', () => {
    const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');
    assert.ok(fs.existsSync(apiClientPath), 'src/lib/apiClient.js must exist');
    const content = fs.readFileSync(apiClientPath, 'utf-8');

    assert.match(content, /customers:\s*\{/, 'Must define customers object on apiClient');
    assert.match(content, /list:\s*\(params\s*=\s*\{\}\)/, 'Must define customers.list method');
    assert.match(content, /getById:\s*\(customerId\)/, 'Must define customers.getById method');
    assert.match(content, /\/api\/v1\/customers/, 'Must target /api/v1/customers endpoint');
  });

  it('should verify query parameter handling in customers.list', () => {
    const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');
    const content = fs.readFileSync(apiClientPath, 'utf-8');

    assert.match(content, /params\.limit/, 'Must handle limit parameter');
    assert.match(content, /params\.offset/, 'Must handle offset parameter');
    assert.match(content, /params\.search/, 'Must handle search parameter');
  });

  it('should verify customers.getById encodes customer ID', () => {
    const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');
    const content = fs.readFileSync(apiClientPath, 'utf-8');

    assert.match(content, /encodeURIComponent/, 'Must encode customer ID in URL');
  });
});

describe('2. ApiError Discrimination & Authorization Safety', () => {
  it('should verify ApiError exposes isAuthError and isForbiddenError getters', () => {
    const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');
    const content = fs.readFileSync(apiClientPath, 'utf-8');

    assert.match(content, /this\.isAuthError\s*=\s*status\s*===\s*401/, 'Must tag 401 as isAuthError');
    assert.match(content, /this\.isForbiddenError\s*=\s*status\s*===\s*403/, 'Must tag 403 as isForbiddenError');
  });

  it('should verify that non-2xx responses raise ApiError with correct error envelope parsing', () => {
    const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');
    const content = fs.readFileSync(apiClientPath, 'utf-8');

    assert.match(content, /responseData\.error/, 'Must parse standardized error envelope');
    assert.match(content, /throw new ApiError/, 'Must throw ApiError on non-ok status');
  });
});

describe('3. Architecture & Security Invariants (Phase 8.4.4 Scope Enforcement)', () => {
  it('should verify ZERO direct Supabase queries for customer data in frontend/src', () => {
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
        /supabase\s*\.\s*from\(\s*['"]customers['"]\s*\)/i,
        `File ${path.relative(FRONTEND_ROOT, f)} must not query Supabase customers table directly`
      );
      assert.doesNotMatch(
        code,
        /supabase\s*\.\s*from\(\s*['"]customer_predictions['"]\s*\)/i,
        `File ${path.relative(FRONTEND_ROOT, f)} must not query customer_predictions directly`
      );
    }
  });

  it('should verify NO customer management or explorer UI is prematurely rendered on login or landing pages', () => {
    const loginPagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
    const loginContent = fs.readFileSync(loginPagePath, 'utf-8');

    assert.doesNotMatch(
      loginContent,
      /apiClient\.customers/i,
      'EmployeeLoginPage must not call apiClient.customers'
    );
    assert.doesNotMatch(
      loginContent,
      /CustomerTable|CustomerExplorer|RiskExplorer/i,
      'EmployeeLoginPage must not import or render customer explorer components'
    );
  });
});
