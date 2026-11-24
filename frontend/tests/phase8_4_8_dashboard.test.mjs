/**
 * RetainIQ Customer Retention Intelligence System
 * Phase 8.4.8 Frontend Verification Suite
 * (Customer Retention Explorer & Advanced Analytics)
 *
 * Runs via native Node.js Test Runner: `node --test tests/phase8_4_8_dashboard.test.mjs`
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const FRONTEND_ROOT = path.resolve(__dirname, '..');

describe('1. Phase 8.4.8 Dashboard Components Architecture & Modular Structure', () => {
  it('should verify all 6 modular dashboard components exist in frontend/src/components/dashboard/', () => {
    const dashboardDir = path.join(FRONTEND_ROOT, 'src', 'components', 'dashboard');
    assert.ok(fs.existsSync(dashboardDir), 'src/components/dashboard directory must exist');

    const expectedFiles = [
      'OverviewDashboard.jsx',
      'CustomerExplorer.jsx',
      'PredictionExplorer.jsx',
      'SegmentationExplorer.jsx',
      'RecommendationCenter.jsx',
      'AnalyticsPerformance.jsx',
    ];

    for (const file of expectedFiles) {
      const filePath = path.join(dashboardDir, file);
      assert.ok(fs.existsSync(filePath), `${file} must exist`);
    }
  });

  it('should verify EmployeeDashboardPage imports and renders all 6 dashboard modules', () => {
    const pagePath = path.join(FRONTEND_ROOT, 'src', 'pages', 'EmployeeDashboardPage.jsx');
    const content = fs.readFileSync(pagePath, 'utf-8');

    assert.match(content, /import\s*\{\s*OverviewDashboard\s*\}\s*from/, 'Must import OverviewDashboard');
    assert.match(content, /import\s*\{\s*CustomerExplorer\s*\}\s*from/, 'Must import CustomerExplorer');
    assert.match(content, /import\s*\{\s*PredictionExplorer\s*\}\s*from/, 'Must import PredictionExplorer');
    assert.match(content, /import\s*\{\s*SegmentationExplorer\s*\}\s*from/, 'Must import SegmentationExplorer');
    assert.match(content, /import\s*\{\s*RecommendationCenter\s*\}\s*from/, 'Must import RecommendationCenter');
    assert.match(content, /import\s*\{\s*AnalyticsPerformance\s*\}\s*from/, 'Must import AnalyticsPerformance');

    assert.match(content, /<OverviewDashboard/, 'Must render OverviewDashboard component');
    assert.match(content, /<CustomerExplorer/, 'Must render CustomerExplorer component');
    assert.match(content, /<PredictionExplorer/, 'Must render PredictionExplorer component');
    assert.match(content, /<SegmentationExplorer/, 'Must render SegmentationExplorer component');
    assert.match(content, /<RecommendationCenter/, 'Must render RecommendationCenter component');
    assert.match(content, /<AnalyticsPerformance/, 'Must render AnalyticsPerformance component');
  });
});

describe('2. Module 1: Overview Dashboard Contract & KPIs', () => {
  const filePath = path.join(FRONTEND_ROOT, 'src', 'components', 'dashboard', 'OverviewDashboard.jsx');

  it('should verify OverviewDashboard calls apiClient.analytics.getOverview', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /apiClient\.analytics\.getOverview\(\)/, 'Must fetch overview analytics');
  });

  it('should verify KPI rendering for 7,000 customers, observed churn, and predicted at-risk', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /Customer Population/, 'Must display customer population KPI');
    assert.match(code, /Observed Ground Truth Churn/, 'Must display observed ground truth churn KPI');
    assert.match(code, /Model Predicted At-Risk/, 'Must display model predicted at-risk KPI');
    assert.match(code, /Critical Interventions/, 'Must display critical high-risk interventions KPI');
  });

  it('should verify risk tier breakdown, snapshot metadata, and model checksum display', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /predicted_risk_distribution/, 'Must render predicted risk tiers');
    assert.match(code, /31 Dec 2025/, 'Must display observation snapshot cutoff date');
    assert.match(code, /model_sha256/, 'Must display locked model SHA-256');
  });
});

describe('3. Module 2: Customer Explorer Filtering, Sorting & Detail Drawer', () => {
  const filePath = path.join(FRONTEND_ROOT, 'src', 'components', 'dashboard', 'CustomerExplorer.jsx');

  it('should verify CustomerExplorer calls apiClient.customers.list with multidimensional params', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /apiClient\.customers\.list\(params\)/, 'Must fetch paginated filtered customer list');
    assert.match(code, /params\.segment/, 'Must support segment filtering');
    assert.match(code, /params\.risk_tier/, 'Must support risk tier filtering');
    assert.match(code, /sort_by:\s*sortBy/, 'Must support sort by field');
    assert.match(code, /sort_dir:\s*sortDir/, 'Must support sort direction');
  });

  it('should verify customer detail profile drawer and live inference trigger', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /apiClient\.customers\.getById/, 'Must fetch customer detail by ID');
    assert.match(code, /apiClient\.customers\.predict/, 'Must execute live prediction from drawer');
    assert.match(code, /selectedCustomer\.features/, 'Must render 43 behavioral features table');
  });
});

describe('4. Module 3: Churn Prediction Explorer & Decision Threshold Spectrum', () => {
  const filePath = path.join(FRONTEND_ROOT, 'src', 'components', 'dashboard', 'PredictionExplorer.jsx');

  it('should verify live model inference execution via apiClient.customers.predict', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /apiClient\.customers\.predict/, 'Must call backend predict endpoint');
    assert.match(code, /predictionData\.churn_probability/, 'Must display churn probability');
    assert.match(code, /predictionData\.retention_probability/, 'Must display retention probability');
  });

  it('should verify locked decision boundary τ = 0.50 visual indicator and risk tiers', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /τ\s*=\s*0\.50/, 'Must visually display locked decision threshold τ = 0.50');
    assert.match(code, /RISK TIER/, 'Must display evaluated risk tier');
    assert.match(code, /40 Numerical \+ 3 Categorical/, 'Must note 43 features configuration');
  });
});

describe('5. Module 4: Customer Segmentation Explorer & 5 Personas', () => {
  const filePath = path.join(FRONTEND_ROOT, 'src', 'components', 'dashboard', 'SegmentationExplorer.jsx');

  it('should verify SegmentationExplorer calls apiClient.analytics.getSegments', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /apiClient\.analytics\.getSegments\(\)/, 'Must fetch 5 persona profiles');
  });

  it('should verify cross-persona comparison diagnostics and customer inspection hook', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /onFilterSegmentInCustomerExplorer/, 'Must support filtering segment in customer explorer');
    assert.match(code, /recommended_strategy/, 'Must display recommended operational strategy');
    assert.match(code, /persona_description/, 'Must display persona description');
  });
});

describe('6. Module 5: Retention Recommendation Center', () => {
  const filePath = path.join(FRONTEND_ROOT, 'src', 'components', 'dashboard', 'RecommendationCenter.jsx');

  it('should verify RecommendationCenter calls apiClient.recommendations.list with filters', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /apiClient\.recommendations\.list\(params\)/, 'Must fetch recommendations list');
    assert.match(code, /params\.priority/, 'Must support priority filtering');
    assert.match(code, /params\.segment/, 'Must support segment filtering');
  });

  it('should verify channel mappings and customer inspection navigation', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /rec\.suggested_channel/, 'Must display suggested communication channel');
    assert.match(code, /rec\.evidence/, 'Must display underlying evidence');
    assert.match(code, /onSelectCustomer/, 'Must provide navigation link to inspect customer');
  });
});

describe('7. Module 6: Analytics & Model Performance Scorecard', () => {
  const filePath = path.join(FRONTEND_ROOT, 'src', 'components', 'dashboard', 'AnalyticsPerformance.jsx');

  it('should verify AnalyticsPerformance calls apiClient.analytics.getModelPerformance', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /apiClient\.analytics\.getModelPerformance\(\)/, 'Must fetch model performance metrics');
  });

  it('should verify confusion matrix (TN, FP, FN, TP) and independent test cohort metrics (N = 1,500)', () => {
    const code = fs.readFileSync(filePath, 'utf-8');
    assert.match(code, /confusion_matrix\.true_negatives/, 'Must render True Negatives');
    assert.match(code, /confusion_matrix\.false_positives/, 'Must render False Positives');
    assert.match(code, /confusion_matrix\.false_negatives/, 'Must render False Negatives');
    assert.match(code, /confusion_matrix\.true_positives/, 'Must render True Positives');
    assert.match(code, /metrics\.accuracy/, 'Must display accuracy');
    assert.match(code, /metrics\.recall/, 'Must display recall');
    assert.match(code, /metrics\.roc_auc/, 'Must display ROC-AUC');
    assert.match(code, /metrics\.f1_score/, 'Must display F1-Score');
  });
});

describe('8. Phase 8.4.8 API Client Extensions & Security Invariants', () => {
  const apiClientPath = path.join(FRONTEND_ROOT, 'src', 'lib', 'apiClient.js');

  it('should verify apiClient defines analytics, recommendations, and customer predict methods', () => {
    const code = fs.readFileSync(apiClientPath, 'utf-8');
    assert.match(code, /analytics:\s*\{/, 'Must define analytics namespace');
    assert.match(code, /getOverview:\s*\(\)\s*=>/, 'Must define getOverview');
    assert.match(code, /getModelPerformance:\s*\(\)\s*=>/, 'Must define getModelPerformance');
    assert.match(code, /getSegments:\s*\(\)\s*=>/, 'Must define getSegments');
    assert.match(code, /recommendations:\s*\{/, 'Must define recommendations namespace');
    assert.match(code, /predict:\s*\(customerId\)\s*=>/, 'Must define customers.predict');
  });

  it('should verify ZERO direct Supabase queries to customer or prediction tables across entire frontend/src', () => {
    const srcDir = path.join(FRONTEND_ROOT, 'src');
    const checkDir = (dir) => {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) {
          checkDir(fullPath);
        } else if (entry.isFile() && (entry.name.endsWith('.js') || entry.name.endsWith('.jsx'))) {
          const content = fs.readFileSync(fullPath, 'utf-8');
          assert.doesNotMatch(content, /supabase\.from\(['"]customers['"]\)/, `${fullPath} must not query customers directly from Supabase`);
          assert.doesNotMatch(content, /supabase\.from\(['"]customer_predictions['"]\)/, `${fullPath} must not query customer_predictions directly from Supabase`);
          assert.doesNotMatch(content, /supabase\.from\(['"]customer_segments['"]\)/, `${fullPath} must not query customer_segments directly from Supabase`);
          assert.doesNotMatch(content, /supabase\.from\(['"]retention_recommendations['"]\)/, `${fullPath} must not query retention_recommendations directly from Supabase`);
        }
      }
    };
    checkDir(srcDir);
  });
});
