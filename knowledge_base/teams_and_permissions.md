# Teams and Permissions

## 4.1 Role-Based Access Control (RBAC)

AcmeCloud uses a role-based access control system with five pre-defined roles, plus the ability to create custom roles on Enterprise plans. Roles are assigned per project; a user can have different roles in different projects.

### 4.1.1 Pre-defined Roles

| Role         | Capabilities                                                                 |
|--------------|------------------------------------------------------------------------------|
| **Owner**    | Full access, including billing, SSO config, project deletion, role management. Limited to 1 per project, assigned to the creator by default. |
| **Admin**    | All Owner capabilities except project deletion and billing tier changes.     |
| **Developer**| Create/edit/delete resources, deployments, environment variables. Cannot manage team members or billing. |
| **Viewer**   | Read-only access to all resources. Cannot make changes.                      |
| **Billing**  | Access to billing, invoices, and payment methods only. No resource access.  |

### 4.1.2 Custom Roles (Enterprise Only)

Enterprise customers can define custom roles with granular permissions across 40+ capabilities grouped by resource type (Projects, Deployments, Secrets, Logs, Billing, etc.). For example, you could create a "DevOps Engineer" role that can manage deployments and view logs but cannot modify project settings or access billing. Custom roles can be cloned from existing roles as a starting point.

## 4.2 Inviting and Managing Team Members

Admins and Owners can invite team members from **Team → Members** by entering the invitee's email address and selecting a role. Invited users receive an email with a 7-day-expiration link. If the invite expires, you can resend it from the same page.

When a user accepts an invite, they are added to the project. If they do not have an AcmeCloud account yet, they will be prompted to create one during the acceptance flow. SSO-enforced organizations bypass the invite-email flow: users added to the connected identity provider group are granted access automatically on their next login.

### 4.2.1 Offboarding Team Members

To remove a team member, go to **Team → Members → [User] → Remove**. You will be prompted to transfer their API keys to another user or revoke them. We recommend always transferring keys to avoid service disruption. Removed users lose access immediately; any active sessions are terminated within 5 minutes.

An audit log of team changes (invites, accepts, removals, role changes) is available in **Settings → Audit Log** for Pro and Enterprise customers, with 90-day and 1-year retention respectively.

## 4.3 Organizations and Project Groups (Enterprise)

Enterprise plans support Organizations, which are containers for multiple projects. Organizations enable:
- Centralized SSO enforcement across all projects
- Shared team members and roles (org-level roles cascade to projects)
- Cross-project usage analytics and consolidated billing
- Project Groups for logical grouping (e.g., by department or environment)

Contact your Enterprise account manager to enable Organization features. Existing projects can be migrated into an Organization without downtime.
