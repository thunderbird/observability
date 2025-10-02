
# Infrastructure Monitoring Service Onboarding Form  
*(Appointment Service – Production – eu‑central‑1)*  

---  

## 1️⃣ Basic Information
| Field | Description | Value |
|-------|-------------|-------|
| **Service Name** | Human‑readable name | **Appointment** |
| **Service Owner** | Team / primary contact | Thunderbird Team |
| **Service Description** | What the service does | Calendar & scheduling platform that exposes a public HTTPS API, a web frontend (CloudFront + S3) and a Redis cache. Authentication is handled via Firefox Accounts (FxA). |
| **Business Impact** | Impact if the service is unavailable | **High** – loss of appointment booking capability for customers, revenue impact, SLA breach for enterprise customers. |

---

## 2️⃣ Service Classification
| Field | Options | Selected |
|-------|---------|----------|
| **Service Tier** | Tier 0 (critical infra) – Tier 1 (business‑critical) – Tier 2 (essential) – Tier 3 (non‑critical) | **Tier 1** |
| **Environment** | Production / Staging / Development / Other | **Production** |
| **Region** | AWS region(s) | **eu‑central‑1** |
| **Data Sensitivity** | Public / Internal / Confidential / Restricted | **Confidential** (PII in appointments, OAuth tokens, etc.) |

---

## 3️⃣ Infrastructure Details
| Component | Details |
|-----------|---------|
| **VPC** | `appointment` – CIDR `10.20.0.0/16` with two /17 subnets (`10.20.0.0/17` in eu‑central‑1a, `10.20.128.0/17` in eu‑central‑1b). Internet gateway enabled, DNS hostnames enabled. |
| **Security Groups** | • `backend` (LB) – inbound 443 TCP from 0.0.0.0/0, outbound all.<br>• `backend` (container) – inbound 5000 TCP **only** from LB SG, outbound all.<br>• `backend_cache` (Redis) – inbound 6379 / 6380 TCP from the container SGs (primary/replica), outbound all. |
| **Load Balancer** | Application Load Balancer (HTTPS) on port 443, ACM cert `arn:aws:acm:eu-central-1:...:certificate/249fcf3e‑0cf2‑48ea‑b6dc‑17239799b3f4`. |
| **ECS / Fargate** | Single Fargate service `appointment-backend-prod` (desired 1, min 2, max 4 via autoscaler). CPU 0.5 vCPU, 2 GiB RAM. Container port 5000 → LB 443. |
| **Redis Cache** | ElastiCache Serverless (Redis 7) – endpoint `cache.appointment.tb.pro`. Primary port 6379, replica port 6380, cluster mode & SSL enabled. |
| **Frontend** | CloudFront distribution (aliases `appointment.tb.pro`) backed by S3 bucket `tb-appointment-prod-frontend`. |
| **Secrets Management** | Pulumi Secrets Manager holds ~30 secrets (DB creds, FxA creds, Google OAuth, Zoom, JWT, SMTP, etc.). |
| **Autoscaling** | CPU ≥ 80 % or RAM ≥ 80 % → scale out to max 4 tasks, min 2 tasks, cooldown 180 s. |
| **Monitoring Group** | `tb:cloudwatch:CloudWatchMonitoringGroup` – email notifications to `thunderbird-services-monitoring@thunderbird.net`. |

---

## 4️⃣ Dependencies (External / Internal)
| Dependency | Type | Notes |
|-----------|------|-------|
| **PostgreSQL** | RDS (prod) – accessed via Secrets (`DATABASE_HOST`, `DATABASE_USER`, …). |
| **Redis Cache** | ElastiCache Serverless (Redis 7) – endpoint `cache.appointment.tb.pro`. |
| **FxA (Firefox Accounts)** | OAuth provider – client id/secret stored in Secrets Manager. |
| **Google OAuth** | Used for “Sign‑in with Google”. |
| **Zoom API** | Calendar integration – client id/secret stored in Secrets Manager. |
| **Sentry** | Error aggregation – DSN injected as env var. |
| **PostHog** | Analytics – host `https://us.i.posthog.com`. |
| **SMTP (SocketLabs)** | Email delivery for notifications. |
| **CloudFront + S3** | Public web UI (`https://appointment.tb.pro`). |

---

## 4️⃣ Monitoring Requirements & SLO Formulas  

### 4.1️⃣ Public HTTPS API (Load Balancer) – Port 443  
| Metric | SLO Formula | Target |
|--------|-------------|--------|
| **Availability** (LB health‑check success) | `Availability = (Successful LB health‑checks) / (Total LB health‑checks) × 100` | **≥ 99.9 %** per month |
| **Latency** (p95) | `p95_latency = 95th percentile of request‑latency (ms) measured at the ALB` | **≤ 300 ms** |
| **TLS Certificate Validity** | `DaysUntilExpiry = (certificate_not_after – now) / (1 day)` | **≥ 30 days** (alarm when < 30 days) |

### 4.2️⃣ Backend Container Service – Port 5000 (HTTP)  
| Metric | SLO Formula | Target |
|--------|-------------|--------|
| **Endpoint Availability** (`GET https://appointment.tb.pro/`) | `Availability = (Successful HTTP 200 responses) / (Total requests) × 100` | **≥ 99.8 %** per month |
| **Health‑Check Path (`/`)** | `HealthCheckSuccess = (LB health‑check 200 responses) / (Total health‑checks) × 100` | **≥ 99.9 %** |
| **Response Time** (p95) | `p95_response = 95th percentile of response‑time (ms) for `/` endpoint` | **≤ 250 ms** |
| **Error Rate** (5xx) | `ErrorRate = (5xx responses) / (Total responses) × 100` | **≤ 0.5 %** |

### 4.3️⃣ Redis Cache – Primary (6379) & Replica (6380)  
| Metric | SLO Formula | Target |
|--------|-------------|--------|
| **Connection Success** (TCP handshake) | `ConnSuccess = (Successful TCP SYN‑ACKs) / (Total connection attempts) × 100` | **≥ 99.9 %** |
| **Latency (p95)** | `p95_latency = 95th percentile of `PING` round‑trip (ms)` | **≤ 5 ms** |
| **Replication Lag** (for replica port 6380) | `Lag = (Replication offset difference) / (Replication offset) × 100` | **≤ 0.1 %** |
| **Cache Miss Ratio** (optional) | `MissRatio = (Cache misses) / (Cache lookups) × 100` | **≤ 5 %** (tracked via application metrics) |

### 4.4️⃣ CloudFront Distribution (Frontend)  
| Metric | SLO Formula | Target |
|--------|-------------|--------|
| **Edge‑Location Availability** | `CF_Availability = (2xx responses from CloudFront) / (Total requests) × 100` | **≥ 99.9 %** |
| **Cache‑Hit Ratio** | `HitRatio = (Cache hits) / (Cache requests) × 100` | **≥ 85 %** |
| **Viewer Latency (p95)** | `p95_viewer_latency = 95th percentile of `ViewerResponseTime` (ms)` | **≤ 200 ms** (global) |

### 4.5️⃣ Autoscaling & Capacity  
| Metric | SLO Formula | Target |
|--------|-------------|--------|
| **CPU Utilisation** | `CPU_Util = average CPU % over 5 min` | **≤ 70 %** (to keep headroom) |
| **Memory Utilisation** | `RAM_Util = average RAM % over 5 min` | **≤ 70 %** |
| **Task Count** | `TaskCount = current desired count` | **Between 2 and 4** (per autoscaler config) |

---

## 5️⃣ Resource‑Level Monitoring (Alarms)

| Resource | Threshold | Alert Severity |
|----------|-----------|----------------|
| **CPU (Fargate task)** | ≥ 80 % (5‑minute avg) | **Warning → Critical** |
| **Memory (Fargate task)** | ≥ 80 % (5‑minute avg) | **Warning → Critical** |
| **Redis CPU** (Serverless) | ≥ 80 % (if metrics are available) | **Warning** |
| **Redis Memory** (Serverless) | ≥ 80 % | **Warning** |
| **ELB 5xx Errors** | > 0.5 % of requests (5‑minute avg) | **Critical** |
| **ELB 4xx Errors** | > 2 % of requests (5‑minute avg) | **Warning** |
| **Health‑Check Failure Rate** | > 0.1 % (5‑minute avg) | **Critical** |
| **CloudFront 5xx Errors** | > 0.5 % of requests (5‑minute avg) | **Critical** |
| **Redis Connection Errors** | > 0.1 % of attempts (5‑minute avg) | **Critical** |
| **CloudWatch Group – Alarms** | Configured via `tb:cloudwatch:CloudWatchMonitoringGroup` – email notifications to `thunderbird-services-monitoring@thunderbird.net`. | – |

---

## 6️⃣ Alerting & Notification Settings
| Channel | Configured? | Recipients |
|---------|-------------|------------|
| **Email** | ✅ (via CloudWatch group) | `thunderbird-services-monitoring@thunderbird.net` |
| **Slack** | ✅ (integration with the monitoring bot) | `#monitoring‑appointments` |
| **PagerDuty** | ❌ (not required – Slack + email suffice for now) |
| **SMS** | ❌ |
| **Other** | – | – |

### Example Alarm Definitions (JSON‑style snippet)  

```yaml
AlarmName: Appointment-API-5xx
MetricName: HTTPCode_ELB_5XX_Count
Namespace: AWS/ApplicationELB
Threshold: 0.5        # 0.5% of total requests
EvaluationPeriods: 2
DatapointsToAlarm: 2
ComparisonOperator: GreaterThanThreshold
TreatMissingData: missing
AlarmActions:
  - arn:aws:sns:eu-central-1:768512802988:monitoring-alerts
```

> *All alarms are created automatically by the `tb:cloudwatch:CloudWatchMonitoringGroup` resource; the table above reflects the **business‑level SLO** we want to enforce.*

---

## 7️⃣ Operational Information
| Field | Description | Value |
|-------|-------------|-------|
| **Maintenance Window** | Preferred time for planned restarts, cache‑invalidation, certificate rotation, etc. | **Wednesday 02:00‑04:00 UTC** (low traffic window) |
| **Escalation Path** | Who to page / contact, in order | 1️⃣ **Service Owner** – `thunderbird-services@thunderbird.net`  <br>2️⃣ **On‑Call Engineer** – rotation managed in PagerDuty (Slack alerts also go to the on‑call channel) <br>3️⃣ **Engineering Manager** – `john.doe@thunderbird.net` |
| **Run‑book Location** | Link to the operational run‑book (step‑by‑step for incidents) | <https://github.com/thunderbird/appointment/blob/main/docs/runbook.md> |
| **Run‑book Highlights** | Quick‑look at the most important sections | • **Health‑Check Failure** – how to force a new task rollout.<br>• **Redis Cache Failure** – fail‑over to replica, clear SSL session cache.<br>• **Certificate Renewal** – CloudFront cert in us‑east‑1 and ALB cert in eu‑central‑1.<br>• **Database Credential Rotation** – update Secrets Manager and restart tasks. |

---

## 8️⃣ Additional Notes & Special Considerations
```
- **Production** environment – all traffic is public (HTTPS 443) and must meet the SLA of 99.9 % availability.
- **Redis Cache** is server‑less (ElastiCache) and accessed over TLS (`REDIS_USE_SSL=True`). The cache is configured in **cluster mode**, so both primary (6379) and replica (6380) ports are exposed inside the VPC only.
- **Security Groups** for Redis (`backend_cache`) allow traffic **only** from the backend container SG (set in code). No inbound from the internet.
- **Frontend** is a static site served from an S3 bucket behind CloudFront. The distribution uses a wildcard ACM cert in us‑east‑1 (CloudFront requirement).  
  - We will monitor the **CloudFront “5xx Error Rate”** and **Cache‑Hit Ratio** as part of the overall SLO.
- **Secrets**: >30 secrets are stored in Secrets Manager (DB credentials, OAuth client‑ids/secrets, JWT secret, session secret, Zoom API keys, etc.). Rotation is performed via CI pipeline; alarms are in place for any **Secrets‑Manager rotation events** (recovery window 0 days means immediate deletion on removal – ensure CI does not delete by mistake).
- **Autoscaling**: CPU ≥ 80 % or RAM ≥ 80 % for 2 consecutive evaluation periods triggers scale‑out; scale‑in is allowed. Minimum 2 tasks, maximum 4.
- **Bastion Host**: The `tb:ec2:SshableInstance` resource is defined but currently empty – a bastion can be added later if needed.
- **CI/CD**: Automated deployments are performed by an AWS Automation User (`tb:ci:AwsAutomationUser`). The user has permission to push images to ECR, invalidate CloudFront cache, and upload the static frontend assets.
- **Compliance**: All PII (appointment details, user email addresses, OAuth tokens) is encrypted at rest (DB, Redis, signed URLs) and in transit (TLS/HTTPS, Redis‑SSL).  
  - Ensure **Data‑Loss‑Prevention** (DLP) scanning is enabled on S3 bucket `tb-appointment-prod-frontend` if required by policy.
```

---

## 9️⃣ Approval
| Role | Name | Date |
|------|------|------|
| **Requested By** | Thunderbird Team |  |
| **Approved By** |  |  |
| **Implementation Date** |  |  |

---  

**Next steps:**  
1. Create the CloudWatch alarms (availability, latency, error‑rate, Redis connection health, CloudFront metrics).  
2. Wire the SLO dashboards (Grafana / CloudWatch dashboards) using the formulas above.  
3. Add the notification targets (Slack channel + monitoring‑team email).  
4. Perform a “dry‑run” health‑check during the upcoming maintenance window to verify that all alarms fire correctly.  

*Once the form is signed off, the monitoring team will provision the alarms and dashboards automatically via the `tb:cloudwatch:CloudWatchMonitoringGroup` resource.*