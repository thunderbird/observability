# Guidelines for Developing Application Logging Solutions

An *application log* or *service log* is the textual data produced by a piece of software for the purpose of recording
its activity. It may come in many forms, such as output from a Docker container, Lambda function, or load balancer. This
information is often useful for development and debugging purposes, but may contain information that identifies
specific users or behaviors within our systems. This Personally Identifying Information (PII) and other sensitive data
must be carefully handled to respect our users' privacy.

This document defines the scope and limitations of application logging at TB Pro. It lays out guidelines for handling
logging and considerations for selecting specific logging tools and their configurations.


## Configuration

This section contains general guidelines for how logs should be produced and handled so as to protect user data. Any
specific logging solution (or a component thereof) should be built in accordance with these guidelines. If a logging
solution is already implemented that does not comply with these guidelines, issues should be created and prioritized to
resolve those discrepancies.


### Log Production

Application logs are often less useful for debugging if they do not contain information which identifies specific users.
Effort must be taken to reduce the amount of this information that gets recorded in the first place. We should only ever
log this information when it is necessary to identify a problem in our systems or respond to an incident. We should
never produce logs with the goal of collecting or analyzing user data, or to track user behavior.

Most application logging facilities include a "log level" feature where log messages of differing levels of detail are
associated with an appropriate verbosity level in the software's logging tool. For most purposes, we should only log
sensitive data at the "debug" level (or a more verbose level like "trace"), and only if it is absolutely necessary.

Production environments should always use the default log level (typically "info") to suppress this output.
Staging and development environments should never contain any real user PII, and therefore more verbose logging should
not pose a hazard. Where possible, debug logging of this sort should also be removed prior to deploying code to
production.


### Data Protection

Logs are always stored somewhere, at least temporarily. That might be the local disk of a server you control, a remote
service of some kind (CloudWatch, Splunk, Kibana, etc), or a developer's local machine. In development and staging
environments, there should be no sensitive data present, but when we do produce PII in logs, we need to protect it.

When logs are stored on a disk, that disk should be encrypted. This includes originating servers and aggregation targets
as well as engineer working machines. Encryption must be enabled at rest on all systems where logs potentially
containing PII will persist. Where possible, those encryption keys should be automatically rotated on a recurring
basis.

When logs are stored on another host, or they pass through an intermediary (such as fluentd/fluent-bit), the data
must be encrypted at all stages of transit using TLS or equivalent protection. Log aggregation systems should be
configured to limit access. This can be done by placing the system on a private network and controlling access to that
service. A password-based system where services sending logs must authenticate to do so is also recommended.

Data must be exfiltrated from these protected systems as infrequently as possible. For example, an engineer responding
to an incident may be tempted to copy some logged events locally for reference. We should resist this temptation when
possible. Where we cannot resist we must make an effort to avoid copying private data, ensure the machine's storage is
fully encrypted as per company policy, and delete the data as soon as possible.

We may have to report on the contents of these logs as part of a postmortem investigation or similar document. In these
cases, we must make sure to scrub any private information from logs before including them in such a report.


### Data Access

Access to stored log data must be protected from unauthorized access. Different tools use different auth schemes, but
some good guidelines include:

- Create logical separation between log types. Logs should be separated by environment (stage, prod, etc) and purpose
  (service log, load balancer access log, and so on).
- Provide access through individual user accounts, not shared credentials.
- Authorize each individual according to their needs, following the principle of least privilege. Incident response
  teams may require production access while developers may only need access to staging and development environments.
  They may only need access to a single application's logs.
- Accessing logs should produce auditable events where possible. For example, when a user accesses a CloudWatch log
  stream, AWS emits a `GetLogEvents` event, which can be discovered using CloudTrail.


### Data Retention

We do not need to store logs for a long period of time. Incident response should be able to grab (and sanitize) the
necessary logs during the initial response period or during the post-mortem investigation in the days following.
Developers investigating service issues in lower environments should be able to reproduce their test scenario to
generate new log text. The longer we retain our logs, the longer that information is at risk, the greater our burden of
protection.

Service logs should be retained no longer than 3 days in production environments and no longer than 7 days in other
environments. Logs exceeding these ages should be fully destroyed, not moved to another location or storage tier, nor
backed up for later retrieval. This should happen through an automated process, such as a lifecycle rule on an S3 bucket
or similar mechanism, not left to an engineer to tidy up manually.

Logs should not be exfiltrated from these systems under most circumstances. In the rare occasion when it is necessary to
offload logs, such as when preparing a postmortem incident report, that data should be scrubbed of private information
where possible and any data that remains un-anonymized should be destroyed as soon as feasible.


## Auditing

Ideally, we want as much of these processes to be auditable. That means that we should be able to look at our systems
and answer specific questions about the data such as:

- When did the data get created? How old is it? Does it exist outside of our data retention policy?
- Who has accessed this data?
- Has a particular user taken any other actions with the data?

To accomplish this, attention should be paid when designing logging systems to maximize our ability to do this. This may
include:

- Choosing system components which allow for detailed auditing (such as the way CloudWatch Logs produces CloudTrail
  events).
- Choose write-once, unmodifiable systems of record.
- Design components with repeatable code patterns, such as a tb_pulumi module, to ensure all installations of these
  logging patterns are configured the same and benefit from code and design improvements over time. Provide these
  patterns to developers as the logging solution to use and provide support for the configurations to encourage their
  use.
- Use automated tools like AWS GuardDuty and AWS Config to report on unsecure configurations.
- Use automated tools like AWS CloudTrail and CloudWatch Alarms to alert when sensitive data is accessed.


## Implementations

We currently have no implementations of these guidelines.

- An [implementation for CloudWatch Logs](./logging_to_cloudwatch_logs.md) has been proposed.