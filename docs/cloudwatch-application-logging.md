# Application Logging to CloudWatch

The [RFC for Application Logging Guidelines](./rfc/application_logging/) describes requirements for implementing
application logging at Thunderbird. This document describes how it has been installed so that you can work with the
logs.

CloudWatch organizes log events into "log groups". These log groups can have any number of streams in them. A log stream
is a time-sorted list of events from any number of sources which are capable of pushing logs into the stream. Variably,
you can use these features to combine logs from different sources or keep them separated however it makes sense.

Logs in prod will only persist for 3 days. In lower environments, logs persist for 7 days. Beyond these durations, logs
will be fully deleted.


## Appointment

Appointment runs as a series of ECS containers on the Fargate platform. ECS task definitions must be configured using
the `log-stream-prefix` option, and that cannot be an empty string. As such, we use the `ecs` prefix, and each container
creates its own log stream made of `ecs`, the container's function and the container ID. You can find these in
`/tb/{env}/appointment`. For example, a log stream called `ecs/backend/fe346bc0ba8f4a09b823b3b76a38e352` is the logging
output of the backend API container with ID `fe346bc0ba8f4a09b823b3b76a38e352`. You can find logs here for all of these
container types:

- backend (The Appointment backend API)
- celery (Works asyncrounous backgrounded tasks)
- flower (Monitors, reports on Celery status)


## Stalwart

Logs for Stalwart can be found in its log group for each environment: `/tb/{env}/stalwart`. Inside, you will find two
log streams matching the two functions we use Stalwart for. That is, we run a mail cluster and a cluster for the
management API. The mail cluster will log to the `mail` log stream, while the management API will log to the `api` log
stream.
