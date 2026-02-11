# Dead Letter Queue

This directory stores events that fluent-bit tried to output but which were rejected by their
target. See `service.storage.backlog.keep.rejected` and `service.storage.backlog.rejected.path` for
configuration details.