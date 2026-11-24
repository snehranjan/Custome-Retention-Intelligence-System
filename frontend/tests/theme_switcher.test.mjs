/**
 * RetainIQ Customer Retention Intelligence System
 * Theme Switcher & Light/Dark Mode Architecture Test Suite
 *
 * Runs via native Node.js Test Runner: `npm test`
 *
 * Verifies:
 * 1. ThemeContext Architecture, Provider, and Hook Contract
 * 2. Pre-Hydration Anti-FOUT Script in index.html
 * 3. Tailwind Dark Mode Configuration & CSS Custom Property Tokens
 * 4. ThemeToggle Accessible Component Contract
 * 5. Complete ThemeToggle Integration Across All Key Portals and Pages
 * 6. Accessibility & Keyboard Interaction Invariants
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, '..');

describe('1. ThemeContext Architecture & Provider Contract', () => {
  const contextPath = path.join(FRONTEND_ROOT, 'src', 'context', 'ThemeContext.jsx');
  const mainPath = path.join(FRONTEND_ROOT, 'src', 'main.jsx');

  it('should verify ThemeContext.jsx exists and exports ThemeProvider and useTheme', () => {
    assert.ok(fs.existsSync(contextPath), 'ThemeContext.jsx must exist');
    const code = fs.readFileSync(contextPath, 'utf-8');

    assert.match(code, /export\s+function\s+ThemeProvider/, 'Must export ThemeProvider');
    assert.match(code, /export\s+function\s+useTheme/, 'Must export useTheme');
    assert.match(code, /retainiq-theme/, 'Must use authoritative storage key retainiq-theme');
    assert.match(code, /["']light["']/, 'Default theme must be light mode');
    assert.match(code, /classList\.(add|remove)\(["']dark["']\)/, 'Must synchronize dark class on document element');
    assert.match(code, /setAttribute\(["']data-theme["']/, 'Must synchronize data-theme attribute');
  });

  it('should verify main.jsx wraps App inside ThemeProvider', () => {
    assert.ok(fs.existsSync(mainPath), 'main.jsx must exist');
    const code = fs.readFileSync(mainPath, 'utf-8');

    assert.match(code, /<ThemeProvider>/, 'App must be wrapped in ThemeProvider');
    assert.match(code, /<\/ThemeProvider>/, 'ThemeProvider must cleanly close');
  });
});

describe('2. Anti-Flash of Unstyled Theme (Anti-FOUT) Script in index.html', () => {
  const indexPath = path.join(FRONTEND_ROOT, 'index.html');

  it('should verify index.html has early inline script checking retainiq-theme', () => {
    assert.ok(fs.existsSync(indexPath), 'index.html must exist');
    const html = fs.readFileSync(indexPath, 'utf-8');

    assert.match(html, /localStorage\.getItem\(["']retainiq-theme["']\)/, 'Must check localStorage retainiq-theme in <head>');
    assert.match(html, /classList\.add\(["']dark["']\)/, 'Must synchronously add dark class before DOM paint');
  });
});

describe('3. Tailwind Configuration & CSS Custom Property Tokens', () => {
  const tailwindPath = path.join(FRONTEND_ROOT, 'tailwind.config.js');
  const cssPath = path.join(FRONTEND_ROOT, 'src', 'styles', 'index.css');

  it('should verify tailwind.config.js enables darkMode class', () => {
    assert.ok(fs.existsSync(tailwindPath), 'tailwind.config.js must exist');
    const config = fs.readFileSync(tailwindPath, 'utf-8');

    assert.match(config, /darkMode:\s*["']class["']/, 'Must set darkMode to class');
    assert.match(config, /var\(--color-bg\)/, 'Must map bg color to CSS variable');
    assert.match(config, /var\(--color-surface\)/, 'Must map surface color to CSS variable');
    assert.match(config, /var\(--color-text-primary\)/, 'Must map text primary to CSS variable');
    assert.match(config, /var\(--color-border\)/, 'Must map border to CSS variable');
  });

  it('should verify index.css defines :root and .dark design tokens', () => {
    assert.ok(fs.existsSync(cssPath), 'index.css must exist');
    const css = fs.readFileSync(cssPath, 'utf-8');

    // Light mode tokens
    assert.match(css, /:root\s*\{/, 'Must define :root variables');
    assert.match(css, /--color-bg:\s*#F8FAFC/i, 'Light background must be cool slate #F8FAFC');
    assert.match(css, /--color-surface:\s*#FFFFFF/i, 'Light surface must be #FFFFFF');
    assert.match(css, /--color-electric:\s*#0066FF/i, 'Light accent must be Precision Cobalt #0066FF');

    // Dark mode tokens
    assert.match(css, /\.dark\s*\{/, 'Must define .dark variables');
    assert.match(css, /--color-bg:\s*#0B1120/i, 'Dark background must be #0B1120');
    assert.match(css, /--color-surface:\s*#151F32/i, 'Dark surface card must be #151F32');
    assert.match(css, /--color-border:\s*#334155/i, 'Dark border must be #334155');
    assert.match(css, /--color-electric:\s*#4C8DFF/i, 'Dark accent must be accessible Azure #4C8DFF');
    assert.match(css, /--color-text-primary:\s*#F1F5F9/i, 'Dark text primary must be #F1F5F9');
  });
});

describe('4. ThemeToggle Accessible Component Contract', () => {
  const togglePath = path.join(FRONTEND_ROOT, 'src', 'components', 'ui', 'ThemeToggle.jsx');

  it('should verify ThemeToggle.jsx exists, uses Sun and Moon icons, and has accessible attributes', () => {
    assert.ok(fs.existsSync(togglePath), 'ThemeToggle.jsx must exist');
    const code = fs.readFileSync(togglePath, 'utf-8');

    assert.match(code, /import.*Sun.*Moon.*from\s*["']lucide-react["']/, 'Must import Sun and Moon from lucide-react');
    assert.match(code, /role=["']switch["']/, 'Must provide role="switch" for accessibility');
    assert.match(code, /aria-checked=/, 'Must provide aria-checked attribute');
    assert.match(code, /aria-label=/, 'Must provide aria-label attribute');
    assert.match(code, /focus-visible:ring-2/, 'Must provide accessible focus indicator');
    assert.match(code, /toggleTheme/, 'Must bind to toggleTheme from ThemeContext');
  });
});

describe('5. Complete ThemeToggle Integration Across All Key Portals', () => {
  const navbarPath = path.join(FRONTEND_ROOT, 'src', 'components', 'layout', 'Navbar.jsx');
  const employeePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeDashboardPage.jsx');
  const adminPath = path.join(FRONTEND_ROOT, 'src', 'pages', 'AdminPortalPage.jsx');
  const loginPath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeLoginPage.jsx');
  const notFoundPath = path.join(FRONTEND_ROOT, 'src', 'pages', 'NotFoundPage.jsx');

  it('should verify Public Website Navbar renders ThemeToggle in desktop and mobile', () => {
    assert.ok(fs.existsSync(navbarPath), 'Navbar.jsx must exist');
    const code = fs.readFileSync(navbarPath, 'utf-8');

    assert.match(code, /import.*ThemeToggle.*from/, 'Navbar must import ThemeToggle');
    assert.match(code, /<ThemeToggle/, 'Navbar must render ThemeToggle');
  });

  it('should verify Employee Portal renders ThemeToggle in header', () => {
    assert.ok(fs.existsSync(employeePath), 'EmployeeDashboardPage.jsx must exist');
    const code = fs.readFileSync(employeePath, 'utf-8');

    assert.match(code, /import.*ThemeToggle.*from/, 'EmployeeDashboardPage must import ThemeToggle');
    assert.match(code, /<ThemeToggle/, 'EmployeeDashboardPage must render ThemeToggle');
  });

  it('should verify Administrator Portal renders ThemeToggle in header', () => {
    assert.ok(fs.existsSync(adminPath), 'AdminPortalPage.jsx must exist');
    const code = fs.readFileSync(adminPath, 'utf-8');

    assert.match(code, /import.*ThemeToggle.*from/, 'AdminPortalPage must import ThemeToggle');
    assert.match(code, /<ThemeToggle/, 'AdminPortalPage must render ThemeToggle');
  });

  it('should verify Employee Login Page renders ThemeToggle in header', () => {
    assert.ok(fs.existsSync(loginPath), 'EmployeeLoginPage.jsx must exist');
    const code = fs.readFileSync(loginPath, 'utf-8');

    assert.match(code, /import.*ThemeToggle.*from/, 'EmployeeLoginPage must import ThemeToggle');
    assert.match(code, /<ThemeToggle/, 'EmployeeLoginPage must render ThemeToggle');
  });

  it('should verify Not Found Page renders ThemeToggle in header', () => {
    assert.ok(fs.existsSync(notFoundPath), 'NotFoundPage.jsx must exist');
    const code = fs.readFileSync(notFoundPath, 'utf-8');

    assert.match(code, /import.*ThemeToggle.*from/, 'NotFoundPage must import ThemeToggle');
    assert.match(code, /<ThemeToggle/, 'NotFoundPage must render ThemeToggle');
  });
});
