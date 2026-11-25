/**
 * Playwright reporter that captures test failures and sends them to Claude API for analysis.
 *
 * Usage: Add to playwright.config.js reporter array:
 *   reporter: ['html', require('./reporters/llm-failure-reporter.js')],
 */

const fs = require('fs');
const path = require('path');

class LLMFailureReporter {
  constructor(options = {}) {
    this.options = {
      outputDir: options.outputDir || 'test-results/llm-analysis',
      apiEndpoint: options.apiEndpoint || 'http://localhost:8000',
      enableAnalysis: options.enableAnalysis !== false,
      ...options,
    };

    // Ensure output directory exists
    this._ensureOutputDir();

    this.failures = [];
  }

  onBegin(config, suite) {
    // Reset failures at start of test run
    this.failures = [];
  }

  onTestEnd(test, result) {
    // Capture failures
    if (result.status === 'failed') {
      const failure = this._extractFailureInfo(test, result);
      this.failures.push(failure);

      if (this.options.enableAnalysis) {
        this._analyzeFailure(failure).catch((err) => {
          console.error('Error analyzing failure:', err.message);
        });
      }
    }
  }

  async onEnd(result) {
    // Write summary report
    if (this.failures.length > 0) {
      const reportPath = path.join(this.options.outputDir, 'llm-analysis-report.json');
      fs.writeFileSync(reportPath, JSON.stringify(
        {
          timestamp: new Date().toISOString(),
          totalFailures: this.failures.length,
          failures: this.failures,
        },
        null,
        2
      ));

      console.log(`\n📊 LLM Failure Analysis Report: ${reportPath}`);
      console.log(`Found ${this.failures.length} failure(s) with LLM suggestions`);
    }
  }

  /**
   * Extract failure information from test result
   */
  _extractFailureInfo(test, result) {
    const error = result.errors[0] || {};
    const location = test.location || {};

    return {
      timestamp: new Date().toISOString(),
      test_name: test.title || 'Unknown Test',
      file: location.file || 'unknown',
      line: location.line || 0,
      error_message: error.message || 'No error message',
      stack_trace: error.stack || '',
      selector: this._extractSelector(error.message),
      page_url: result.stdout ? this._extractUrl(result.stdout) : 'unknown',
      page_title: 'unknown',
      status: result.status,
      duration: result.duration,
      llm_analysis: null, // Will be populated if analysis is enabled
    };
  }

  /**
   * Extract selector from error message
   */
  _extractSelector(errorMessage) {
    if (!errorMessage) return 'unknown';

    // Common Playwright error patterns:
    // "Locator expected a single element matching ...but found 2"
    // "locator.click: Timeout ... waiting for locator("...")"
    // "locator.fill: element not found inside "..."

    const patterns = [
      /locator\(['"`]([^'"`]+)['"`]\)/i,
      /matching ['"`]([^'"`]+)['"`]/i,
      /waiting for locator\(\s*['"`]([^'"`]+)['"`]\s*\)/i,
      /inside ['"`]([^'"`]+)['"`]/i,
    ];

    for (const pattern of patterns) {
      const match = errorMessage.match(pattern);
      if (match && match[1]) {
        return match[1];
      }
    }

    return 'unknown';
  }

  /**
   * Extract page URL from stdout (if available)
   */
  _extractUrl(stdout) {
    // Look for navigated to URL in test output
    const match = stdout.match(/navigated to|goto.*?['"`](https?:\/\/[^'"`\s]+)/i);
    if (match && match[1]) {
      return match[1];
    }
    return 'unknown';
  }

  /**
   * Send failure to backend for LLM analysis
   */
  async _analyzeFailure(failure) {
    if (!this.options.enableAnalysis) return;

    try {
      const response = await fetch(
        `${this.options.apiEndpoint}/api/test/analyze-failure`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(failure),
        }
      );

      if (response.ok) {
        const analysis = await response.json();
        failure.llm_analysis = analysis;
      } else {
        console.warn(`Analysis API returned ${response.status}`);
      }
    } catch (err) {
      console.warn('Could not reach analysis API:', err.message);
      // Non-fatal; continue without analysis
    }
  }

  /**
   * Ensure output directory exists
   */
  _ensureOutputDir() {
    if (!fs.existsSync(this.options.outputDir)) {
      fs.mkdirSync(this.options.outputDir, { recursive: true });
    }
  }
}

module.exports = LLMFailureReporter;
