# Troubleshooting and FAQs

## 5.1 Common Login Issues

**Issue: "Verification link expired" during sign-up**
See Section 1.1 of Getting Started. Verification links expire after 24 hours. Go to the login page, click "Resend verification email," and enter your email address. We will send a new link immediately. Note: each resend invalidates the previous link, so always use the most recent one.

**Issue: SSO redirects are failing**
Check the following:
1. Your SSO configuration in **Settings → Organization → SSO** matches your identity provider's settings exactly (Entity ID, ACS URL, certificates).
2. Clock skew between your IdP and AcmeCloud is less than 5 minutes.
3. The user attempting to log in exists in both your IdP directory and the AcmeCloud project with matching email addresses (case-insensitive).
4. If using custom SAML, confirm the configuration was reviewed by our support team (Section 1.1.1).

**Issue: CLI `acme login` shows browser but no response**
The CLI login flow requires localhost port 8421 to be available for the OAuth callback. If port 8421 is blocked, you can use the device code flow: `acme login --device`. This displays a code and URL; open the URL in any browser, enter the code, and the CLI will authenticate.

## 5.2 Deployment Failures

Deployments can fail for a variety of reasons. Always check the deployment logs in **Projects → [Project] → Deployments → [Deployment] → Logs** first. Common causes include:

**Build Errors (exit code non-zero)**
Your build command failed. Check the build log for compiler/linter errors. Common fixes:
- Ensure all dependencies are listed in `package.json` / `requirements.txt` / `Cargo.toml`
- Verify build scripts use relative paths (the build runs in an isolated `/workspace` directory)
- Check that environment variables referenced at build time are defined in the project's build environment settings

**Runtime Errors (health check failures)**
The deployment succeeded but the health check endpoint returned non-2xx. By default we hit `GET /` every 10 seconds. Configure the health check path and timeout in **Deployments → Settings → Health Checks**. Ensure your application listens on the `PORT` environment variable (we inject this automatically; do not hardcode a port).

**Out of memory during build or runtime**
Free/Starter tiers get 2 GB of build memory and 512 MB of runtime memory per instance. Pro gets 8 GB build / 2 GB runtime. Enterprise is configurable. Upgrade your tier or optimize your build (e.g., split large multi-service monorepos into separate projects).

## 5.3 Billing and Payment Issues

**Issue: Credit card declined but the card works elsewhere**
Our payment processor uses strict anti-fraud rules. Common reasons:
- The card does not support international transactions (our processor is based in the US and Ireland).
- The billing address you entered does not match the card's registered address (check the ZIP/postal code exactly).
- Your bank has flagged the subscription as unusual — contact your bank to approve "AcmeCloud" as a merchant.

If issues persist, add a different payment method or contact billing support. See Section 2.3.1 for what happens after repeated failures.

**Issue: Unexpected overage charges on the bill**
Review the usage breakdown in **Billing → Usage** with CSV export. The most frequent causes of surprise overages:
1. Storage: Large database backups or log files retained longer than expected (default log retention is 30 days; configure in **Settings → Log Retention**).
2. API calls: A misconfigured client looping and retries — check the `X-RateLimit` headers (Section 3.1.1) and implement proper backoff.
3. Add-ons: Advanced Audit Logs or Dedicated IPs enabled during a trial and not disabled (add-ons are listed in **Billing → Add-ons**).

## 5.4 Contacting Support

Support channels by tier (also see Section 2.1):
- **Free / Community:** Post in https://community.acmecloud.com — response from community or team within ~3 business days.
- **Starter:** Email support@acmecloud.com — response within 24-48 business hours.
- **Pro:** In-app chat (bottom-right widget) or email — response within 4 business hours.
- **Enterprise:** 24/7 dedicated Slack/Teams channel, phone hotline, and assigned Customer Success Manager.

When contacting support, always include: your project ID (starting with `proj_`), the approximate timestamp (with timezone) of the issue, relevant deployment/request IDs if applicable, and steps to reproduce. This will significantly reduce resolution time.
