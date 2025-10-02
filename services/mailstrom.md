# Infrastructure Monitoring Service Onboarding Form

## Basic Information

| Field | Description | Value |
|-------|-------------|-------|
| **Service Name** | Mailstrom | |
| **Service Owner** | Services / Infrastructure |
| **Service Description** | Mail server for Thundermail |
| **Business Impact** | Impact if service is unavailable | [x] Critical (revenue/customer impact)<br>[ ] High (major function unavailable)<br>[ ] Medium (degraded experience)<br>[ ] Low (minimal impact) |

## Service Classification

| Field | Options | Selection |
|-------|---------|-----------|
| **Service Tier** | [ ] Tier 0 (Critical Infrastructure)<br>[x] Tier 1 (Business-Critical)<br>[ ] Tier 2 (Essential Business)<br>[ ] Tier 3 (Non-Critical) | |
| **Environments** | [x] Production<br>[x] Staging<br>[ ] Development<br>|
| **Regions** | eu-central-1 |
| **Data Sensitivity** | [ ] Public<br>[ ] Internal<br>[x] Confidential<br>[ ] Restricted | |

## Infrastructure Details

| Field | Description | Value |
|-------|-------------|-------|
| **Compute Type** | [x] Virtual Machines<br>[ ] Containers<br>[ ] Serverless<br>[ ] Other: ________ | |
| **Database Type** | [ ] Neon<br> [ ] RDS<br>|
| **Storage Type** | [ ] Block Storage<br>[x] Object Storage (S3)<br>[ ] CloudFront (CDN)<br>[x] File Storage<br>[x] Elasticache <br>[ ] None<br>[ ] Other: Backblaze for Customer Emails.| |
| **Load Balancer** | [x] Yes<br>[ ] No | |
| **Services to Monitor** | http: caldav carddav jmap <br> protocols: https, imap, imaps, lmtp, managesieve, smtp, smtps, submission<br> Autoconfig Static Site (Cloudfront + S3)|

## Key Dependencies

| Dependency Type | Service Names |
|-----------------|--------------|
| **Upstream Services** | Services this service depends on:<br>1. Cloudflare (DNS)<br>2. Backblaze (Customer Email Storage)<br>3. Keycloak (For Autoconfig Site)|
| **Downstream Services** | Services that depend on this service:<br>1.<br>2.<br>3. |
| **External Services** | Third-party services required:<br>1. CloudFlare (DNS)<br>2. Backblaze (Email Storage)<br>3. |

## Monitoring Requirements

### Availability Monitoring

# SLO Formulas for Network Protocols (Measured at Load Balancer)

## HTTPS (Port 443)
### Endpoints
 - https://autoconfig.thundermail.com/
 - http://mail.thundermail.com/.well-known/jmap
```
Availability SLO = (Total HTTPS requests - Failed HTTPS requests) / Total HTTPS requests * 100%
Latency SLO = Percentage of HTTPS requests completed within 300ms ≥ 99.9%
Error Rate SLO = Number of 5xx responses / Total HTTPS requests ≤ 0.1%
```

## IMAP (Port 143)
```
Availability SLO = (Total IMAP connections - Failed IMAP connections) / Total IMAP connections * 100% ≥ 99.9%
Latency SLO = Percentage of IMAP command responses within 500ms ≥ 99.5%
Connection Error SLO = Number of connection errors / Total IMAP connection attempts ≤ 0.1%
```

## IMAPS (Port 993)
```
Availability SLO = (Total IMAPS connections - Failed IMAPS connections) / Total IMAPS connections * 100% ≥ 99.95%
Latency SLO = Percentage of IMAPS command responses within 500ms ≥ 99.5%
TLS Handshake SLO = Percentage of successful TLS handshakes ≥ 99.9%
```

## LMTP (Port 24)
```
Availability SLO = (Total LMTP transactions - Failed LMTP transactions) / Total LMTP transactions * 100% ≥ 99.9%
Latency SLO = Percentage of mail delivery attempts completed within 3s ≥ 99.5%
Delivery Error SLO = Number of permanent delivery failures / Total delivery attempts ≤ 0.5%
```

## ManageSieve (Port 4190)
```
Availability SLO = (Total ManageSieve connections - Failed ManageSieve connections) / Total ManageSieve connections * 100% ≥ 99.5%
Latency SLO = Percentage of script operations completed within 1s ≥ 99.0%
Script Error SLO = Number of script validation errors / Total script operations ≤ 1.0%
```

## SMTP (Port 25)
```
Availability SLO = (Total SMTP sessions - Failed SMTP sessions) / Total SMTP sessions * 100% ≥ 99.9%
Latency SLO = Percentage of mail acceptance operations completed within 5s ≥ 99.5%
Rejection SLO = Number of non-spam/policy rejections / Total SMTP sessions ≤ 0.1%
```

## SMTPS (Port 465)
```
Availability SLO = (Total SMTPS sessions - Failed SMTPS sessions) / Total SMTPS sessions * 100% ≥ 99.95%
Latency SLO = Percentage of mail acceptance operations completed within 5s ≥ 99.5%
TLS Handshake SLO = Percentage of successful TLS handshakes ≥ 99.9%
```

## Submission (Port 587)
```
Availability SLO = (Total Submission connections - Failed Submission connections) / Total Submission connections * 100% ≥ 99.9%
Latency SLO = Percentage of message submission operations completed within 3s ≥ 99.5%
Authentication SLO = Percentage of successful authentications (excluding invalid credentials) ≥ 99.9%
```

### Resource Monitoring

We currently have several methods available, but they should be accesible from betterstack.com. 
Cloudwatch alerts, OTEL metrics collector.

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