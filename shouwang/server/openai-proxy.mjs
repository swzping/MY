import http from 'node:http';
import { URL } from 'node:url';

const DEFAULT_PORT = 8787;
const DEFAULT_UPSTREAM_BASE_URL = 'https://api.openai.com';
const MAX_BODY_BYTES = 10 * 1024 * 1024;
const HOP_BY_HOP_HEADERS = new Set([
  'connection',
  'content-length',
  'host',
  'keep-alive',
  'proxy-authenticate',
  'proxy-authorization',
  'te',
  'trailer',
  'transfer-encoding',
  'upgrade',
]);

function json(res, statusCode, body, extraHeaders = {}) {
  res.writeHead(statusCode, {
    'access-control-allow-origin': '*',
    'access-control-allow-methods': 'GET,POST,OPTIONS',
    'access-control-allow-headers': 'authorization,content-type',
    'content-type': 'application/json; charset=utf-8',
    ...extraHeaders,
  });
  res.end(JSON.stringify(body));
}

function parseProxyTokens(value) {
  return String(value || '')
    .split(',')
    .map((token) => token.trim())
    .filter(Boolean);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    const chunks = [];
    let total = 0;

    req.on('data', (chunk) => {
      total += chunk.length;
      if (total > MAX_BODY_BYTES) {
        reject(new Error('REQUEST_BODY_TOO_LARGE'));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => resolve(Buffer.concat(chunks)));
    req.on('error', reject);
  });
}

function hasValidProxyToken(req, proxyTokens) {
  const header = req.headers.authorization || '';
  const token = header.startsWith('Bearer ') ? header.slice('Bearer '.length).trim() : '';
  return proxyTokens.includes(token);
}

function buildUpstreamHeaders(req, openaiApiKey) {
  const headers = {};
  for (const [name, value] of Object.entries(req.headers)) {
    if (!HOP_BY_HOP_HEADERS.has(name) && name !== 'authorization') {
      headers[name] = value;
    }
  }
  headers.authorization = `Bearer ${openaiApiKey}`;
  return headers;
}

function isAllowedPath(pathname) {
  return pathname === '/v1/responses' || pathname === '/v1/chat/completions';
}

export function createProxyServer({
  openaiApiKey,
  proxyTokens,
  upstreamBaseUrl = DEFAULT_UPSTREAM_BASE_URL,
} = {}) {
  if (!openaiApiKey) {
    throw new Error('OPENAI_API_KEY is required.');
  }
  if (!Array.isArray(proxyTokens) || proxyTokens.length === 0) {
    throw new Error('At least one proxy access token is required.');
  }

  return http.createServer(async (req, res) => {
    try {
      if (req.method === 'OPTIONS') {
        json(res, 204, {});
        return;
      }

      const requestUrl = new URL(req.url || '/', 'http://localhost');

      if (req.method === 'GET' && requestUrl.pathname === '/health') {
        json(res, 200, { ok: true });
        return;
      }

      if (req.method !== 'POST' || !isAllowedPath(requestUrl.pathname)) {
        json(res, 404, {
          error: {
            message: 'Only POST /v1/responses and POST /v1/chat/completions are supported.',
            type: 'not_found',
          },
        });
        return;
      }

      if (!hasValidProxyToken(req, proxyTokens)) {
        json(res, 401, {
          error: {
            message: 'Missing or invalid proxy access token.',
            type: 'unauthorized',
          },
        });
        return;
      }

      const body = await readBody(req);
      const upstreamUrl = new URL(`${requestUrl.pathname}${requestUrl.search}`, upstreamBaseUrl);
      const upstreamResponse = await fetch(upstreamUrl, {
        method: 'POST',
        headers: buildUpstreamHeaders(req, openaiApiKey),
        body,
      });

      res.writeHead(upstreamResponse.status, {
        'access-control-allow-origin': '*',
        'content-type': upstreamResponse.headers.get('content-type') || 'application/json',
      });

      if (upstreamResponse.body) {
        for await (const chunk of upstreamResponse.body) {
          res.write(chunk);
        }
      }
      res.end();
    } catch (error) {
      if (error.message === 'REQUEST_BODY_TOO_LARGE') {
        json(res, 413, {
          error: {
            message: 'Request body is too large.',
            type: 'request_too_large',
          },
        });
        return;
      }

      json(res, 502, {
        error: {
          message: 'Proxy failed to contact the upstream OpenAI API.',
          type: 'bad_gateway',
        },
      });
    }
  });
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const openaiApiKey = process.env.OPENAI_API_KEY;
  const proxyTokens = parseProxyTokens(process.env.PROXY_ACCESS_TOKENS);
  const port = Number(process.env.PORT || DEFAULT_PORT);

  const server = createProxyServer({ openaiApiKey, proxyTokens });
  server.listen(port, () => {
    console.log(`OpenAI proxy listening on http://127.0.0.1:${port}`);
  });
}
