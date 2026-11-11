const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { score } = require('./score');
const { diagnose } = require('./diagnose');

test('human scoring counts ratings and rejects invalid or duplicate reviews', () => {
  const review = { caseId: 'missing-action', detected: true, correct: true, actionable: true, falseClaim: false, notes: 'Correctly located the missing action.' };
  assert.deepEqual(score([review]), { reviewed: 1, truePositive: 1, falseNegative: 0, trueNegative: 0, falsePositive: 0, correct: 1, actionable: 1, falseClaims: 0 });
  assert.deepEqual(score([
    { ...review, detected: false },
    { ...review, caseId: 'unchanged', detected: true, correct: false, falseClaim: true },
  ]), { reviewed: 2, truePositive: 0, falseNegative: 1, trueNegative: 0, falsePositive: 1, correct: 1, actionable: 2, falseClaims: 1 });
  assert.throws(() => score([review, review]), /unique benchmark case/);
  assert.throws(() => score([{ ...review, correct: 'yes' }]), /boolean/);
  assert.throws(() => score([{ ...review, caseId: 'unknown' }]), /benchmark case/);
  assert.throws(() => score([]), /non-empty/);
});

test('diagnostics refuse to contact a provider without explicit confirmation or key', async () => {
  let requests = 0;
  const mockFetch = async () => { requests++; };
  await assert.rejects(diagnose(['unchanged'], { OPENAI_API_KEY: 'test' }, mockFetch), /confirm-reviewed-synthetic/);
  await assert.rejects(diagnose(['unchanged', '--confirm-reviewed-synthetic'], {}, mockFetch), /OPENAI_API_KEY/);
  assert.equal(requests, 0);
});

test('diagnostics send only verified images, preserve results, and reject tampering', async t => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'visual-tools-'));
  t.after(() => fs.rmSync(directory, { recursive: true, force: true }));
  const hash = data => crypto.createHash('sha256').update(data).digest('hex');
  const baseline = Buffer.from('synthetic reference');
  const actual = Buffer.from('synthetic current');
  fs.writeFileSync(path.join(directory, 'baseline.png'), baseline);
  fs.writeFileSync(path.join(directory, 'unchanged.png'), actual);
  fs.writeFileSync(path.join(directory, 'results.json'), JSON.stringify({
    baselineSha256: hash(baseline),
    results: [{ id: 'unchanged', imageSha256: hash(actual) }],
  }));
  let requests = 0;
  const mockFetch = async (url, options) => {
    requests++;
    assert.equal(url, 'https://api.openai.com/v1/chat/completions');
    const body = JSON.parse(options.body);
    assert.equal(body.model, 'gpt-4o');
    assert.equal(body.messages[0].content[1].image_url.url, `data:image/png;base64,${baseline.toString('base64')}`);
    assert.equal(body.messages[0].content[2].image_url.url, `data:image/png;base64,${actual.toString('base64')}`);
    return { ok: true, json: async () => ({ choices: [{ message: { content: 'No visible change.' } }] }) };
  };
  const args = ['unchanged', '--confirm-reviewed-synthetic'];
  const result = await diagnose(args, { OPENAI_API_KEY: 'test' }, mockFetch, directory);
  assert.equal(result.diagnostic, 'No visible change.');
  assert.deepEqual(JSON.parse(fs.readFileSync(path.join(directory, 'unchanged-diagnostic.json'), 'utf8')), result);
  fs.writeFileSync(path.join(directory, 'unchanged.png'), 'tampered');
  await assert.rejects(diagnose(args, { OPENAI_API_KEY: 'test' }, mockFetch, directory), /Image changed/);
  assert.equal(requests, 1);
});
