# API and Authentication

## 3.1 API Overview

The AcmeCloud REST API is organized around resource-oriented URLs, returns JSON-encoded responses, and uses standard HTTP response codes and verbs. The base URL for all API requests is:

```
https://api.acmecloud.com/v1
```

All requests must include:
- A valid `Authorization` header (see Section 3.2)
- `Content-Type: application/json` header for POST/PUT/PATCH requests
- An `Idempotency-Key` header (recommended) for POST requests to prevent duplicate operations

### 3.1.1 Rate Limiting

Rate limits depend on your plan tier:
- Free: 60 requests/minute per API key
- Starter: 300 requests/minute per API key
- Pro: 2,000 requests/minute per API key
- Enterprise: Custom (configured per agreement)

We return rate limit information in every response header:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Requests remaining in current window
- `X-RateLimit-Reset`: Unix timestamp when the window resets
- `Retry-After`: (on 429 responses) Seconds to wait before retrying

## 3.2 Authentication Methods

AcmeCloud supports three authentication methods for API access:

### 3.2.1 API Keys (Server-to-Server)

API keys are long-lived credentials intended for server-side applications. Create and manage them in **Developer → API Keys**. Keys are prefixed with `sk_live_` (production) or `sk_test_` (sandbox). The full key is only shown once at creation time — store it securely, as we cannot recover it. Rotate keys regularly and revoke them immediately if compromised.

**Example:**
```bash
curl https://api.acmecloud.com/v1/projects \
  -H "Authorization: Bearer sk_live_abc123..."
```

### 3.2.2 OAuth 2.0 (Third-Party Integrations)

Use OAuth 2.0 when building integrations that need to access a user's AcmeCloud account on their behalf. We support Authorization Code flow with PKCE for public clients and Client Credentials flow for machine-to-machine use. Register your OAuth app in **Developer → OAuth Apps**. Authorization scopes include `read`, `write`, `admin`, and `billing:read`.

### 3.2.3 Session Tokens (Frontend/CLI)

Short-lived session tokens (15-minute TTL, renewable via refresh token) are issued for browser and CLI sessions after user login. Do not use session tokens for server-side code; they are tied to a specific user agent and IP address for security.

## 3.3 Webhooks

Webhooks allow you to receive real-time notifications when events occur in your account. Configure webhook endpoints in **Developer → Webhooks**. We support HMAC-SHA256 signatures (signed with your webhook secret) so you can verify that events were sent by AcmeCloud. Always check the signature and timestamp before processing a webhook payload.

Available event types include (full list in **Developer → Webhook Events**):
- `project.created`, `project.deleted`
- `invoice.paid`, `invoice.payment_failed`
- `deployment.started`, `deployment.succeeded`, `deployment.failed`
- `user.invited`, `user.removed`

We retry failed webhook deliveries with exponential backoff (up to 24 hours). Use the **Test Endpoint** button to send example events during development.
