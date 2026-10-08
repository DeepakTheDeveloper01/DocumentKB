# Billing and Pricing

## 2.1 Pricing Tiers Explained

AcmeCloud offers four pricing tiers to match your needs:

| Tier       | Monthly Price | Storage | API Calls      | Team Members | Support          |
|------------|---------------|---------|----------------|--------------|------------------|
| Free       | $0            | 1 GB    | 10,000/mo      | 2            | Community        |
| Starter    | $29           | 50 GB   | 500,000/mo     | 5            | Email (24-48h)   |
| Pro        | $199          | 500 GB  | 10,000,000/mo  | 25           | Chat + Email (4h)|
| Enterprise | Custom quote  | Unlimited | Unlimited    | Unlimited    | 24/7 Dedicated   |

All paid tiers include a 14-day free trial. You can upgrade or downgrade your tier at any time from the **Billing → Plan** page. Downgrades take effect at the start of your next billing cycle.

## 2.2 Understanding Your Bill

Your bill is generated on the 1st of each month and is based on:
1. **Base plan cost:** The flat fee for your selected tier, prorated if you changed tiers mid-cycle.
2. **Overage charges:** Usage that exceeds your tier's included allowances. Overage rates are: Storage — $0.03/GB, API calls — $0.50 per 10,000 calls.
3. **Add-on services:** Premium features such as Advanced Audit Logs ($49/mo), Dedicated IPs ($99/mo per IP), and Custom Branding ($29/mo).
4. **Taxes:** VAT, GST, or sales tax based on your billing address.

You can view a detailed cost breakdown at any time in **Billing → Usage** with per-resource granularity and CSV export.

## 2.3 Payment Methods and Invoices

We accept credit cards (Visa, Mastercard, American Express), ACH bank transfers (US only for $500+ invoices), and annual wire transfers for Enterprise customers. All payment details are encrypted at rest using AES-256 and processed by PCI DSS Level 1 compliant providers.

### 2.3.1 Managing Multiple Payment Methods

You can add up to five payment methods and designate a primary method. If the primary method fails, we automatically attempt the backup methods in order. Failed payments trigger retries on day 2, day 4, and day 7. After three failed retries, your account enters a grace period of 72 hours before services are suspended.

Invoices are available as PDFs in **Billing → Invoices** within 24 hours of billing. You can add up to 10 email recipients for invoice notifications. EU customers will automatically receive a VAT-compliant invoice; please ensure your VAT number is entered in **Billing → Tax Information**.

## 2.4 Refunds and Credits

Refunds are evaluated on a case-by-case basis. We generally offer full refunds within the first 30 days of your first paid subscription if you are unsatisfied. Contact billing support to request a refund.

Service credits may be issued for documented platform outages that exceed our SLA uptime guarantee (99.9% for Pro, 99.99% for Enterprise). Credits are calculated as 10x the prorated cost of the affected service during the downtime period and are automatically applied to your next bill unless you request a refund instead.
