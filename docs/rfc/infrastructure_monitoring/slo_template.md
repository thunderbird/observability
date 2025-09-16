# Infrastructure Monitoring Service Onboarding Form

## Basic Information
| Field | Description | Value |
|-------|-------------|-------|
| **Service Name** | Name of the service to be monitored | |
| **Service Owner** | Team or individual responsible | |
| **Service Description** | Brief description of functionality | |
| **Business Impact** | Impact if service is unavailable | [ ] Critical (revenue/customer impact)<br>[ ] High (major function unavailable)<br>[ ] Medium (degraded experience)<br>[ ] Low (minimal impact) |

## Service Classification
| Field | Options | Selection |
|-------|---------|-----------|
| **Service Tier** | [ ] Tier 0 (Critical Infrastructure)<br>[ ] Tier 1 (Business-Critical)<br>[ ] Tier 2 (Essential Business)<br>[ ] Tier 3 (Non-Critical) | |
| **Environments** | [ ] Production<br>[ ] Staging<br>[ ] Development<br>[ ] Other: ________ | |
| **Regions** | | |
| **Data Sensitivity** | [ ] Public<br>[ ] Internal<br>[ ] Confidential<br>[ ] Restricted | |

## Infrastructure Details
| Field | Description | Value |
|-------|-------------|-------|
| **Compute Type** | [ ] Virtual Machines<br>[ ] Containers<br>[ ] Serverless<br>[ ] Physical Servers<br>[ ] Other: ________ | |
| **Database Type** | [ ] None<br>[ ] Neon<br>[ ] RDS<br>[ ] NoSQL<br>[ ] In-Memory<br>[ ] Other: ________ | |
| **Storage Type** | [ ] Block Storage<br>[ ] Object Storage (S3)<br>[ ] CloudFront (CDN)<br>[ ] File Storage<br>[ ] Elasticache<br>[ ] None<br>[ ] Other: ________ | |
| **Load Balancer** | [ ] Yes<br>[ ] No | |
| **Services to Monitor** | List specific endpoints, ports, protocols, or services | |

## Key Dependencies
| Dependency Type | Service Names |
|-----------------|--------------|
| **Upstream Services** | Services this service depends on:<br>1.<br>2.<br>3. |
| **Downstream Services** | Services that depend on this service:<br>1.<br>2.<br>3. |
| **External Services** | Third-party services required:<br>1.<br>2.<br>3. |

## Monitoring Requirements

### Availability Monitoring
```
# SLO Formulas for Service Endpoints
## API/Web Service
Availability SLO = (Total requests - Failed requests) / Total requests * 100% ≥ ____%
Latency SLO = Percentage of requests completed within ___ms ≥ ____%
Error Rate SLO = Number of 5xx responses / Total requests ≤ ____%
```

### Resource Monitoring
We currently have several methods available, but they should be accessible from our monitoring platform.
| Resource | Alert Threshold |
|----------|----------------|
| CPU Utilization | [ ] Above _____% for _____ minutes |
| Memory Utilization | [ ] Above _____% for _____ minutes |
| Disk Utilization | [ ] Above _____% for _____ minutes |
| Network Utilization | [ ] Above _____ Mbps for _____ minutes |

## Alert Configuration
| Alert Severity | Notification Channel | Responders |
|----------------|----------------------|------------|
| Critical | [ ] Email<br>[ ] SMS<br>[ ] Slack<br>[ ] PagerDuty<br>[ ] Other: ________ | |
| Warning | [ ] Email<br>[ ] SMS<br>[ ] Slack<br>[ ] PagerDuty<br>[ ] Other: ________ | |

## Operational Information
| Field | Description | Value |
|-------|-------------|-------|
| **Maintenance Window** | Preferred time for maintenance | Day: ________<br>Time: ________ |
| **Escalation Path** | Who to contact and in what order | 1.<br>2.<br>3. |
| **Runbook Location** | Link to service documentation/runbook | |

## Additional Notes
```
[Any additional monitoring requirements or special considerations]
```

## Approval
| Role | Name | Date |
|------|------|------|
| Requested By | | |
| Approved By | | |
| Implementation Date | | |