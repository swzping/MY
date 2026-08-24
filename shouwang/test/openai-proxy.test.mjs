import assert from 'node:assert/strict';
import { once } from 'node:events';
import http from 'node:http';
import test from 'node:test';

import { createProxyServer } from '../server/openai-proxy.mjs';

function listen(server) {
  return new Promise((resolve) => {
    server.listen(0, '127.0.0.1', () => {
      const address = server.address();
      resolve(`http://127.0.0.1:${address.port}`);
    });
  });
}

async function close(server) {
  if (!server.listening) {
    return;
  }
  server.closeAllConnections?.();
  server.close();
  await once(server, 'close');
}

test('rejects requests without a valid proxy token', async () => {
  const upstream = http.createServer((req, res) => {
    res.writeHead(500).end('should not reach upstream');
  });
  const upstreamBaseUrl = await listen(upstream);
  const proxy = createProxyServer({
    openaiApiKey: 'sk-test',
    proxyTokens: ['friend-token'],
    upstreamBaseUrl,
  });
  const proxyBaseUrl = await listen(proxy);

  try {
    const response = await fetch(`${proxyBaseUrl}/v1/responses`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ model: 'gpt-5-mini', input: 'hi' }),
    });

    assert.equal(response.status, 401);
    assert.deepEqual(await response.json(), {
      error: {
        message: 'Missing or invalid proxy access token.',
        type: 'unauthorized',
      },
    });
  } finally {
    await close(proxy);
    await close(upstream);
  }
});

test('forwards authorized OpenAI-compatible requests to the upstream API', async () => {
  let receivedRequest;
  const upstream = http.createServer((req, res) => {
    let body = '';
    req.setEncoding('utf8');
    req.on('data', (chunk) => {
      body += chunk;
    });
    req.on('end', () => {
      receivedRequest = {
        method: req.method,
        url: req.url,
        authorization: req.headers.authorization,
        contentType: req.headers['content-type'],
        body: JSON.parse(body),
      };
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ id: 'resp_test', output_text: 'hello' }));
    });
  });
  const upstreamBaseUrl = await listen(upstream);
  const proxy = createProxyServer({
    openaiApiKey: 'sk-real-token',
    proxyTokens: ['friend-token'],
    upstreamBaseUrl,
  });
  const proxyBaseUrl = await listen(proxy);

  try {
    const response = await fetch(`${proxyBaseUrl}/v1/responses`, {
      method: 'POST',
      headers: {
        authorization: 'Bearer friend-token',
        'content-type': 'application/json',
      },
      body: JSON.stringify({ model: 'gpt-5-mini', input: 'hi' }),
    });

    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
      id: 'resp_test',
      output_text: 'hello',
    });
    assert.deepEqual(receivedRequest, {
      method: 'POST',
      url: '/v1/responses',
      authorization: 'Bearer sk-real-token',
      contentType: 'application/json',
      body: { model: 'gpt-5-mini', input: 'hi' },
    });
  } finally {
    await close(proxy);
    await close(upstream);
  }
});
