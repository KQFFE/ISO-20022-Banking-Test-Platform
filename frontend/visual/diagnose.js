const crypto = require('node:crypto');
const fs = require('node:fs');
const path = require('node:path');

const outputDir = path.resolve(__dirname, '../test-results/visual-benchmark');

function readVerifiedImage(directory, filename, expectedHash) {
  const image = fs.readFileSync(path.join(directory, filename));
  const hash = crypto.createHash('sha256').update(image).digest('hex');
  if (hash !== expectedHash) throw new Error(`Image changed since the benchmark: ${filename}. Rerun and review it.`);
  return `data:image/png;base64,${image.toString('base64')}`;
}

async function diagnose(args, env = process.env, fetchImpl = fetch, directory = outputDir) {
  if (args.length !== 2 || args[1] !== '--confirm-reviewed-synthetic') {
    throw new Error('Usage: node visual/diagnose.js <case-id> --confirm-reviewed-synthetic');
  }
  if (!env.OPENAI_API_KEY) throw new Error('Set OPENAI_API_KEY before running diagnostics.');
  const manifest = JSON.parse(fs.readFileSync(path.join(directory, 'results.json'), 'utf8'));
  const item = manifest.results.find(result => result.id === args[0]);
  if (!item || !/^[a-z-]+$/.test(item.id)) throw new Error('Unknown benchmark case. Run the benchmark and choose a case from results.json.');
  const baseline = readVerifiedImage(directory, 'baseline.png', manifest.baselineSha256);
  const actual = readVerifiedImage(directory, `${item.id}.png`, item.imageSha256);
  const model = env.OPENAI_VISION_MODEL || 'gpt-4o';
  const response = await fetchImpl('https://api.openai.com/v1/chat/completions', {
    method: 'POST',
    headers: { 'content-type': 'application/json', authorization: `Bearer ${env.OPENAI_API_KEY}` },
    signal: AbortSignal.timeout(60000),
    body: JSON.stringify({
      model,
      max_tokens: 500,
      messages: [{
        role: 'user',
        content: [
          { type: 'text', text: 'Compare the first image (reference) with the second (current). Describe visible differences and their location, or say no visible difference. Note uncertainty. Do not infer hidden behavior, compliance, or approve changes.' },
          { type: 'image_url', image_url: { url: baseline, detail: 'high' } },
          { type: 'image_url', image_url: { url: actual, detail: 'high' } },
        ],
      }],
    }),
  });
  if (!response.ok) throw new Error(`OpenAI request failed (HTTP ${response.status}): ${(await response.text()).slice(0, 1000)}`);
  const payload = await response.json();
  const text = payload.choices?.[0]?.message?.content;
  if (typeof text !== 'string' || !text.trim()) throw new Error('OpenAI returned no diagnostic text.');
  const result = { caseId: item.id, model, baselineSha256: manifest.baselineSha256, imageSha256: item.imageSha256, diagnostic: text };
  fs.writeFileSync(path.join(directory, `${item.id}-diagnostic.json`), JSON.stringify(result, null, 2));
  return result;
}

if (require.main === module) {
  diagnose(process.argv.slice(2)).then(result => console.log(result.diagnostic)).catch(error => {
    console.error(error.message);
    process.exitCode = 1;
  });
}

module.exports = { diagnose };
