# Security and retention

Review queries are always scoped to `request.user`. Uploaded files use Django media storage and are not linked from public static directories. Before production rollout, add private object storage, signed short-lived downloads, configurable retention, complete deletion, access logging, malware scanning, and a documented subprocesser/no-training policy.
