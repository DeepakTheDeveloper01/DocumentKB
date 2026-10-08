# Getting Started with AcmeCloud Platform

## 1.1 Creating Your Account

Welcome to AcmeCloud! To create your account, visit https://acmecloud.com/signup and provide your email address, company name, and a secure password. We require passwords to be at least 12 characters long and include a mix of uppercase letters, lowercase letters, numbers, and special symbols. After submitting the form, you will receive a verification email with a link to confirm your email address. You must click this link within 24 hours or the link will expire.

### 1.1.1 SSO and Enterprise Sign-On

Enterprise customers can configure Single Sign-On (SSO) using SAML 2.0 or OpenID Connect. Navigate to **Settings → Organization → SSO** to set up your identity provider. We support Okta, Azure AD, Ping Identity, and Google Workspace out of the box. Custom SAML providers are also supported but require a manual configuration review by our support team.

## 1.2 Setting Up Your First Project

Once your account is verified, you will be prompted to create your first project. Projects are the top-level organizational unit in AcmeCloud and contain all your resources, environments, and team members. We recommend naming projects after your application or product (e.g., "customer-portal", "mobile-backend"). Each project is assigned a unique project ID that looks like `proj_abc123def456` — you will need this ID for API calls and CLI operations.

After creating a project, the onboarding wizard will guide you through:
- Selecting a cloud region (US East, US West, EU Central, AP Southeast)
- Choosing a pricing tier (Free, Starter, Pro, Enterprise)
- Inviting initial team members
- Connecting a Git repository (GitHub, GitLab, Bitbucket)

## 1.3 Installing the CLI

The AcmeCloud CLI allows you to manage your resources from the terminal. Installation is available via several package managers:

**macOS (Homebrew):**
```bash
brew install acmecloud/tap/acme
```

**Windows (PowerShell):**
```powershell
winget install AcmeCloud.AcmeCLI
```

**Linux (curl):**
```bash
curl -fsSL https://get.acmecloud.com | sh
```

After installation, authenticate by running `acme login` and following the browser-based OAuth flow. To verify your installation, run `acme --version`. The CLI supports tab completion for Bash, Zsh, Fish, and PowerShell — run `acme completion --help` for setup instructions.
