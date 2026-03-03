# Application Logging at Thunderbird Pro Services

Thunderbird Pro Services produce application logs describing their moment-to-moment operations. These logs are generally
useful for diagnosing service level problems, but may contain personally identifying information (PII) in some cases.
This document defines the scope and limitations of application logging at TB Pro.


## Logging Purposes

We should produce and store logs for the following purposes:

- Development and debugging
- Incident response

We should **not** produce or store logs for purposes such as:

- Data collection
- Analytics
- Any kind of user tracking purpose

Generally, if the logs contain information that can identify a user, we should be very scrutinous about whether those
logs actually need to be produced. Logs should serve a purpose, and PII in logs needs to be fully justified. Staging and
other pre-prod environments should not contain PII in the first place.


## Log Storage and Access

Application logs should always:

- be stored in AWS CloudWatch Logs,
- be encrypted at rest and in transit, and
- have access restricted according to the principle of least privilege.


## Log Retention

Log files should only be stored as long as they are useful for the purposes described above. In production environments,
logs should be preserved no longer than 3 days. In staging environments, logs should be preserved no longer than 7 days.
After this point, log files should be fully deleted.