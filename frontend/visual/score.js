const fs = require('node:fs');
const cases = require('./cases.json');

function score(ratings) {
  if (!Array.isArray(ratings) || ratings.length === 0) throw new Error('Ratings must be a non-empty array.');
  const ids = new Set();
  for (const item of ratings) {
    if (!item || !cases.some(testCase => testCase.id === item.caseId) || ids.has(item.caseId) ||
        typeof item.detected !== 'boolean' ||
        typeof item.correct !== 'boolean' || typeof item.actionable !== 'boolean' ||
        typeof item.falseClaim !== 'boolean' || typeof item.notes !== 'string' || !item.notes.trim()) {
      throw new Error('Each unique benchmark case needs boolean detected/correct/actionable/falseClaim and non-empty notes.');
    }
    ids.add(item.caseId);
  }
  const count = key => ratings.filter(item => item[key]).length;
  const expectedChange = item => cases.find(testCase => testCase.id === item.caseId).changed;
  return {
    reviewed: ratings.length,
    truePositive: ratings.filter(item => expectedChange(item) && item.detected).length,
    falseNegative: ratings.filter(item => expectedChange(item) && !item.detected).length,
    trueNegative: ratings.filter(item => !expectedChange(item) && !item.detected).length,
    falsePositive: ratings.filter(item => !expectedChange(item) && item.detected).length,
    correct: count('correct'),
    actionable: count('actionable'),
    falseClaims: count('falseClaim'),
  };
}

if (require.main === module) {
  try {
    if (process.argv.length !== 3) throw new Error('Usage: node visual/score.js <ratings.json>');
    console.log(JSON.stringify(score(JSON.parse(fs.readFileSync(process.argv[2], 'utf8'))), null, 2));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}

module.exports = { score };
