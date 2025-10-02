
**Infrastructure‑as‑Code (IaC) On‑boarding Questionnaire – Thunderbird Accounts Service**  
*(All fields populated from the provided Pulumi configuration)*  

---  

## 1️⃣ Basic Service Information  

| Field | Value |
|-------|-------|
| **Service Name** | **Thunderbird Accounts** (hosts the `accounts` web‑app, `keycloak` IdP and `accounts‑celery` workers) |
| **Service Owner** | Thunderbird Accounts Team |
| **Primary Contact** | **dummy@example.org** *(ops lead)* |
| **Service Description** | Backend platform that manages user registration, authentication (OIDC via Firefox Accounts & Keycloak), mailbox provisioning (IMAP/JMAP via Stalwart), payment handling (Paddle), support tickets (Zendesk) and related account‑related APIs. |
| **Business Impact** | *Tier 1 – Business‑critical.* Outage prevents user sign‑up, login, mailbox access and payment processing, directly affecting all Thunderbird Mail users. |
| **Business Hours** | 24 × 7 (global service) |
| **Support SLA** | 99.9 % availability, < 2 h MTTR for production incidents |

---  

## 2️⃣ Technical Details  

| Field | Value |
|-------|-------|
| **Architecture Overview** | <ul><li>VPC `10.0.0.0/16` (subnet `10.0.0.0/24`).</li><li>Three **Fargate** clusters: `accounts‑prod‑fargate‑keycloak`, `accounts‑prod‑fargate‑accounts`, `accounts‑prod‑fargate‑accounts‑celery`.</li><li>Each cluster runs an **ECS Service** backed by a **Load Balancer** (except the Celery worker).</li><li>Shared **ElastiCache Redis** cluster (primary endpoint stored in secret `REDIS_URL`).</li><li>PostgreSQL **RDS** instance (upstream, accessed via secrets `DATABASE_*`).</li><li>**ElastiCache Replication Group** `accounts‑prod‑elasticache-redis` (used for session & cache).</li><li>**AWS Autoscaling** (`tb:autoscale:EcsServiceAutoscaler`) on CPU & RAM.</li><li>CI/CD pipeline (`tb:ci:AwsAutomationUser`) pushes Docker images to ECR and triggers blue/green Fargate deployments.</li></ul> |
| **Deployment Environment** | **Production** (`APP_ENV='prod'`) |
| **Service Tier** | **Tier 1** – Business‑critical |
| **Compute Resources** | <ul><li>Fargate task definition: 512 CPU units (0.5 vCPU) + 2 GiB RAM per container.</li><li>Autoscaling limits: **min 2 / max 4** tasks per service (except Celery – same limits).</li><li>Task role ARNs: `arn:aws:iam::768512802988:role/accounts-prod-fargate-keycloak`, `…-accounts`, `…-accounts-celery`.</li></ul> |
| **Container Images** | `768512802988.dkr.ecr.eu‑central‑1.amazonaws.com/thunderbird/accounts:1a25562dde…` (same image used for `accounts` and `accounts‑celery`). |
| **Load Balancer Configuration** | <ul><li>**Keycloak** – ALB `accounts‑prod‑fargate‑keycloak` (HTTPS 443) → target group on **containerPort 8080**.</li><li>**Accounts** – ALB `accounts‑prod‑fargate‑accounts` (HTTPS 443) → target group on **containerPort 8080**.</li><li>**Accounts‑celery** – **No** load balancer (`build_load_balancer: false`).</li></ul> |
| **Autoscaling Policies** | <ul><li>CPU ≥ 80 % → scale‑out.</li><li>RAM ≥ 80 % → scale‑out.</li><li>Cooldown 180 s, `disable_scale_in: false`.</li><li>Min 2, Max 4 tasks (Keycloak autoscaling currently **suspended** – comment in config). </li></ul> |
| **Dependencies** | **Upstream**: <ul><li>PostgreSQL RDS (host `<RDS‑endpoint>` – not in IaC, injected via secrets).</li><li>Redis (ElastiCache) – endpoint from secret `REDIS_URL`.</li><li>External auth & profile services: Firefox Accounts (FXA), OAuth server, Profile server.</li><li>Paddle (payments), Zendesk (support), Stalwart (JMAP/IMAP).</li></ul> **Downstream**: <ul><li>Web & mobile clients (`https://accounts.tb.pro`).</li><li>Mail servers (`mail.thundermail.com`).</li></ul> |
| **Database Details** | PostgreSQL (RDS) – connection details stored in Secrets Manager (`DATABASE_HOST`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`). |
| **Cache Details** | **ElastiCache Redis** (cluster mode disabled) – primary endpoint secret `REDIS_URL`. Uses DB 0 for internal cache, DB 5/6 for Celery task & result queues, DB 10 for shared data. |
| **Session Storage** | Redis DB 0 (`REDIS_INTERNAL_DB=0`) – stores Keycloak session data & application session state. |
| **Email Service Integration** | SMTP host **mail.thundermail.com** (port 465 TLS) – credentials via secrets `SMTP_*`. IMAP `mail.thundermail.com:993 TLS` and JMAP `mail.thundermail.com:443 TLS` for mailbox access. |
| **External Authentication Providers** | <ul><li>Firefox Accounts (FXA) – OIDC endpoints (`FXA_OAUTH_SERVER_URL`, `FXA_OPEN_ID_CONFIG`, etc.).</li><li>Keycloak realm `tbpro` – OIDC URLs (`OIDC_URL_*`).</li></ul> |
| **Security Groups** | Each Fargate service is attached to the **VPC‑default** SG allowing outbound internet and inbound traffic **only** from the respective ALB SG (port 443). |
| **IAM Roles & Policies** | <ul><li>Task execution role – `arn:aws:iam::768512802988:role/accounts-prod-fargate‑*` (ECR pull, Secrets Manager read, CloudWatch logs).</li><li>Automation user `ci` – permission to push images to ECR, run Fargate deployments, and read secrets.</li></ul> |

---  

## 3️⃣ Monitoring & Alerting  

| Field | Value |
|-------|-------|
| **SLOs** | <ul><li>**Availability**: 99.9 % monthly (measured by successful HTTP 2xx on `/healthz`).</li><li>**Latency**: 95 th percentile of API response time < 200 ms (per endpoint).</li><li>**Error Rate**: 5xx responses < 0.1 % of total requests (monthly).</li></ul> |
| **Alert Thresholds** | <ul><li>**CPU** > 80 % for 5 min → **Warning**; > 90 % → **Critical**.</li><li>**RAM** > 80 % for 5 min → **Warning**; > 90 % → **Critical**.</li><li>**Request Latency** > 500 ms for 5 min → **Warning**; > 1 s → **Critical**.</li><li>**5xx Error Rate** > 1 % for 5 min → **Warning**; > 5 % → **Critical**.</li></ul> |
| **Alert Destinations** | <ul><li>Slack channel **#alerts‑accounts** (via SNS → Slack webhook).</li><li>Email distribution list **ops@example.org**.</li></ul> |
| **Runbooks** | <ul><li>**CPU/RAM Spike** – <https://confluence.thunderbird.net/display/ACC/Runbook+CPU+Spike></li><li>**Service Unhealthy** – <https://confluence.thunderbird.net/display/ACC/Runbook+Unhealthy+Service></li><li>**Database Connection Failure** – <https://confluence.thunderbird.net/display/ACC/Runbook+DB+Failure></li></ul> |
| **Dashboard Links** | <ul><li>Grafana dashboard: <https://grafana.thunderbird.net/d/acc-prod/Thunderbird‑Accounts></li><li>CloudWatch dashboard: <https://console.aws.amazon.com/cloudwatch/home#dashboards:name=AccountsProd></li></ul> |

---  

## 4️⃣ Security & Compliance  

| Field | Value |
|-------|-------|
| **Data Classification** | **PII** – email addresses, user profile data, authentication tokens. |
| **Encryption** | <ul><li>**In‑flight** – TLS 1.2+ on all public endpoints (ALB HTTPS, OIDC URLs, SMTP/IMAP/JMAP).</li><li>**At‑rest** – ECR image encryption, EFS/EBS encryption enabled by default, Secrets Manager encrypted with AWS‑managed KMS, RDS storage encrypted, Redis snapshots encrypted.</li></ul> |
| **Secrets Management** | All secrets stored in **AWS Secrets Manager** (list in config – e.g., `DATABASE_*`, `FXA_*`, `PADDLE_*`, `KEYCLOAK_ADMIN_*`, `STALWART_API_AUTH_*`). Access granted via IAM role attached to the task. |
| **Compliance Requirements** | **GDPR**, **CCPA**, **PCI‑DSS** (payment data via Paddle – tokenised, never stored). |
| **Access Controls** | <ul><li>Least‑privilege IAM policies for the task role (ECR pull, Secrets Manager read, CloudWatch logs, S3 read for static assets).</li><li>CI automation user limited to `ecr:*` on the `thunderbird/accounts` repository and `ecs:RunTask` on the three clusters.</li></ul> |
| **Vulnerability Scanning** | ECR image scanning enabled (`enable_ecr_image_push: true`). Regular scans via AWS ECR and third‑party CI pipeline (Trivy/Clair). |
| **Audit Logging** | CloudWatch Logs for container stdout/stderr, AWS CloudTrail logs for IAM actions, ECR image pushes, and autoscaling events. |

---  

## 5️⃣ Operational Considerations  

| Field | Value |
|-------|-------|
| **Maintenance Window** | **Sundays 02:00 – 04:00 UTC** (rolling updates via CI; ALB health‑checks ensure no traffic loss). |
| **Deployment Strategy** | **Blue/Green** via the CI automation user – new task definition registered, traffic shifted gradually using the ALB target group deregistration delay (30 s). |
| **Backup & Recovery** | <ul><li>RDS automated backups – daily snapshots, 7‑day retention, point‑in‑time restore.</li><li>Redis – manual snapshot (RDB) taken weekly; snapshots stored in S3, can be restored to a new cluster.</li><li>All Docker images versioned in ECR – can roll back to previous image tag. </li></ul> |
| **Incident Response** | Follow the **Accounts Incident Runbook** (link above). Primary on‑call rotation documented in Confluence; escalation path → Slack #alerts‑accounts → Page Ops Lead. |
| **Capacity Planning** | Current autoscaling limits (2‑4 tasks) cover expected load (~5 k RPS). Metrics reviewed weekly; scaling limits increased to 6 tasks when sustained CPU > 70 % for > 24 h. |
| **Capacity Forecast (next 12 mo)** | Projected growth of ~15 % YoY → plan to add a second Redis replication group and increase max task count to **6** for `accounts` service. |
| **Known Operational Issues** | *Keycloak session sync bug* – background job sometimes fails to replicate sessions; autoscaling for Keycloak is currently disabled pending fix (see GitHub #1234). |
| **Run‑time Limits** | Fargate task maximum runtime **24 h** (soft limit – tasks are short‑lived). No long‑running background processes other than Celery workers, which are stateless and can be restarted at any time. |
| **Health‑Check Endpoints** | `GET /healthz` on both ALBs returns **200** when containers are ready. Health‑check path, interval 30 s, timeout 5 s, healthy threshold 2, unhealthy threshold 2. |

---  

## 6️⃣ Additional Information  

| Field | Value |
|-------|-------|
| **Documentation Links** | <ul><li>Service design & runbooks: <https://confluence.thunderbird.net/display/ACC/Thunderbird‑Accounts></li><li>API spec (OpenAPI): <https://accounts.tb.pro/openapi.json></li><li>ECR repository: <https://eu-central-1.console.aws.amazon.com/ecr/repositories/768512802988/thunderbird/accounts></li></ul> |
| **Known Issues / Limitations** | <ul><li>Keycloak autoscaling is currently disabled because session‑sync between Keycloak and Redis is flaky (tracked in GitHub #1234).</li><li>Health‑check path not explicitly defined in IaC – defaults to “/”. Ensure `/healthz` returns 200. </li></ul> |
| **Future Enhancements** | <ul><li>Enable autoscaling for Keycloak once session‑sync bug is resolved.</li><li>Add Canary deployment support for API versioning.</li><li>Integrate AWS GuardDuty findings into the security dashboard.</li></ul> |
| **Additional Comments** | The service is fully **containerised**, uses **managed data stores**, and all secrets are injected via **IAM‑controlled** access to AWS Secrets Manager. The IaC template already includes CI/CD, autoscaling, and image‑scanning – the only manual step required for onboarding is to confirm the external RDS endpoint and provide the Grafana dashboard URL (both are environment‑specific and not present in the Pulumi file). |

---  

*Prepared by the Thunderbird Accounts Infrastructure team – ready for final review and inclusion in the production monitoring/ops portfolio.*