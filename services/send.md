# Infrastructure Monitoring Service Onboarding Form

## Basic Information
| Field | Description | Value |
|-------|-------------|-------|
| **Service Name** | Name of the service to be monitored | Send Suite |
| **Service Owner** | Team or individual responsible | Thunderbird Team |
| **Service Description** | Brief description of functionality | Secure file sharing service with authentication and storage capabilities |
| **Business Impact** | Impact if service is unavailable | [x] Critical (revenue/customer impact)<br>[ ] High (major function unavailable)<br>[ ] Medium (degraded experience)<br>[ ] Low (minimal impact) |

## Service Classification
| Field | Options | Selection |
|-------|---------|-----------|
| **Service Tier** | [ ] Tier 0 (Critical Infrastructure)<br>[x] Tier 1 (Business-Critical)<br>[ ] Tier 2 (Essential Business)<br>[ ] Tier 3 (Non-Critical) | Tier 1 |
| **Environments** | [x] Production<br>[ ] Staging<br>[ ] Development<br>[ ] Other: ________ | Production |
| **Regions** | | us-east-1 |
| **Data Sensitivity** | [ ] Public<br>[ ] Internal<br>[x] Confidential<br>[ ] Restricted | Confidential |

## Infrastructure Details
| Field | Description | Value |
|-------|-------------|-------|
| **Compute Type** | [ ] Virtual Machines<br>[x] Containers<br>[ ] Serverless<br>[ ] Physical Servers<br>[ ] Other: ________ | Containers (AWS Fargate) |
| **Database Type** | [ ] None<br>[ ] Neon<br>[x] RDS<br>[ ] NoSQL<br>[ ] In-Memory<br>[ ] Other: ________ | RDS (PostgreSQL) |
| **Storage Type** | [ ] Block Storage<br>[x] Object Storage (S3)<br>[x] CloudFront (CDN)<br>[ ] File Storage<br>[ ] Elasticache<br>[ ] None<br>[x] Other: Backblaze B2 | S3, CloudFront, Backblaze B2 |
| **Load Balancer** | [x] Yes<br>[ ] No | Yes (Application Load Balancer) |
| **Services to Monitor** | List specific endpoints, ports, protocols, or services | - Backend API: https://send-backend.tb.pro/ (port 443)<br>- Frontend: https://send.tb.pro (port 443)<br>- Container health check (port 8080)<br>- Prisma service (port 5555) |

## Key Dependencies
| Dependency Type | Service Names |
|-----------------|--------------|
| **Upstream Services** | Services this service depends on:<br>1. Backblaze B2 Storage<br>2. PostgreSQL Database<br>3. AWS Secrets Manager |
| **Downstream Services** | Services that depend on this service:<br>1. N/A |
| **External Services** | Third-party services required:<br>1. Firefox Accounts (FxA)<br>2. Sentry<br>3. PostHog |

## Monitoring Requirements
### Availability Monitoring
```
# SLO Formulas for Service Endpoints

## Backend API (https://send-backend.tb.pro/ - port 443)
Availability SLO = (Total requests - Failed requests) / Total requests * 100% ≥ 99.9%
Latency SLO = Percentage of requests completed within 500ms ≥ 95%
Error Rate SLO = Number of 5xx responses / Total requests ≤ 0.1%

## Frontend (https://send.tb.pro - port 443)
Availability SLO = (Total requests - Failed requests) / Total requests * 100% ≥ 99.95%
Latency SLO = Percentage of requests completed within 300ms ≥ 98%
Error Rate SLO = Number of 5xx responses / Total requests ≤ 0.05%

## Container Health Check (port 8080)
Availability SLO = (Total health checks - Failed health checks) / Total health checks * 100% ≥ 99.99%
Latency SLO = Percentage of health checks completed within 100ms ≥ 99%
Health Check Success Rate = Successful health checks / Total health checks * 100% ≥ 99.9%

## Prisma Service (port 5555)
Availability SLO = (Total requests - Failed requests) / Total requests * 100% ≥ 99.5%
Latency SLO = Percentage of requests completed within 1000ms ≥ 95%
Error Rate SLO = Number of errors / Total requests ≤ 0.5%

## Database Connection
Connection Success Rate = Successful connections / Total connection attempts * 100% ≥ 99.9%
Query Latency SLO = Percentage of queries completed within 200ms ≥ 95%

## B2 Storage Integration
Operation Success Rate = Successful operations / Total operations * 100% ≥ 99.8%
Operation Latency SLO = Percentage of operations completed within 2000ms ≥ 95%
```

### Resource Monitoring
We currently have several methods available, but they should be accessible from our monitoring platform.
| Resource | Alert Threshold |
|----------|----------------|
| CPU Utilization | [x] Above 80% for 5 minutes |
| Memory Utilization | [x] Above 80% for 5 minutes |
| Disk Utilization | [x] Above 85% for 10 minutes |
| Network Utilization | [x] Above 500 Mbps for 5 minutes |

## Alert Configuration
| Alert Severity | Notification Channel | Responders |
|----------------|----------------------|------------|
| Critical | [ ] Email<br>[ ] SMS<br>[x] Slack<br>[x] PagerDuty<br>[ ] Other: ________ | Thunderbird On-Call Team |
| Warning | [x] Email<br>[ ] SMS<br>[x] Slack<br>[ ] PagerDuty<br>[ ] Other: ________ | rjung+cloudwatch@thunderbird.net |

## Operational Information
| Field | Description | Value |
|-------|-------------|-------|
| **Maintenance Window** | Preferred time for maintenance | Day: Sunday<br>Time: 02:00-04:00 UTC |
| **Escalation Path** | Who to contact and in what order | 1. Primary On-Call Engineer<br>2. Secondary On-Call Engineer<br>3. Engineering Manager |
| **Runbook Location** | Link to service documentation/runbook | https://github.com/thunderbird/send-suite/docs/runbook.md |

## Additional Notes
```
- Service is deployed using AWS Fargate with autoscaling (min 2, max 4 instances)
- Frontend is served via CloudFront CDN with S3 origin
- Service uses external authentication via Firefox Accounts
- Error tracking is done via Sentry
- Analytics are captured via PostHog
- The service handles user file uploads which may contain sensitive data
- The Prisma service on port 5555 is primarily used for database management and should only be accessible internally
```

## Approval
| Role | Name | Date |
|------|------|------|
| Requested By | Thunderbird Team | |
| Approved By | | |
| Implementation Date | | |