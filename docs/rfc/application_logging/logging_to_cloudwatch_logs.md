# RFC: Logging to CloudWatch Logs


## Proposal Overview

We should define a pattern of infrastructure resources that provides a unified experience for
applications sending their logs to CloudWatch Logs. This should come in the form of a
[tb_pulumi](https://github.com/thunderbird/pulumi/) module that can be used to stamp out logging
destinations that are compliant with our [guidelines](./application_logging_guidelines.md) in our
various infrastructure projects. Existing projects which send logs to CloudWatch Logs through
more or less default configurations can be adjusted to use the new pattern, bringing them into
compliance.


## Rationale

CloudWatch Logs can be configured to meet all of our guidelines pertaining to logging targets:

- KMS Keys provide encryption at rest for log data.
- KMS encryption keys can be set to auto-rotate at a custom interval.
- The AWS API provides encryption for log data in transit.
- Log data is passed through a VPC endpoint to the CloudWatch Logs service over a private network.
- Log streams are individually policable resources, allowing granularity in access control.
- Log groups are also access-controllable, increasing flexibility in access control.
- IAM actions related to these groups and streams can be tracked through a CloudTrail event trail and alerted on with
  CloudWatch Alarms.
- Policies granting access to these logs can be crafted around the logical separators of environment and application.
  IAM user groups with these policies applied can be created to control log access to individuals.
- CloudWatch Log Groups can be configured with a retention window, automating the deletion of log data according to our
  guidelines.


## Implementation Details

We should implement this as a tb_pulumi module: `tb:cloudwatch:LoggingDestination`. This module should implement default
values which align with our guidelines.

It should define the following resources:

- A [KMS Key](https://www.pulumi.com/registry/packages/aws/api-docs/kms/key/) to handle encryption at rest for the
  logs. (Example: `mailstrom-logs-stage`)
- A [CloudWatch LogGroup](https://www.pulumi.com/registry/packages/aws/api-docs/cloudwatch/loggroup/) for the
  environment. In implementation, keeping with AWS's log group naming conventions, this might be called something like
  `/tb/mailstrom/stage` for the Mailstrom/Stalwart staging environment.
- A [CloudWatch LogStream](https://www.pulumi.com/registry/packages/aws/api-docs/cloudwatch/logstream/) for each
  application. This is somewhat arbitrary and can be broken up however it makes sense. (i.e.
  `/tb/mailstrom/stage/stalwart/mail` vs `/tb/mailstrom/stage/stalwart/management-api`)
- A set of [IAM Policies](https://www.pulumi.com/registry/packages/aws/api-docs/iam/policy/) allowing various levels of
  access to these streams. Applications will need a write access policy. Users will need read access policies. There
  should be a level of customization here, allowing the engineers to design access in ways that make sense for their
  use case. These policies can be applied to any existing set of permissions to extend access to logs.
- A [CloudTrail Event Trail](https://www.pulumi.com/registry/packages/aws/api-docs/cloudtrail/trail/) set up with an
  appropriate filter for auditing log access.
- A [CloudWatch Alarm](https://www.pulumi.com/registry/packages/aws/api-docs/cloudwatch/metricalarm/) to alert when log
  access is detected.

We have two primary use cases for this in our current system:

1. We need to [aggregate Stalwart logs](https://github.com/thunderbird/mailstrom/issues/196).
2. We need to apply our logging guidelines to existing services that produce logs.

In both cases, we need a target log stream with our retention/encryption/etc rules applied. In the first case, we can
use fluent-bit to ship logs from the Docker containers running Stalwart straight to a log group created with the common
pattern. In the second case, we can create new log destinations with the new pattern, then update the existing
container definitions to use the new log streams.