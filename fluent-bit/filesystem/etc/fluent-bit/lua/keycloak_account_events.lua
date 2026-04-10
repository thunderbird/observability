--[[
    keycloak_account_events.lua

This module acts as a fluent-bit event processor for raw Keycloak user events. The Accounts
application's Celery worker periodically polls the Keycloak Admin API for recent events
(logins, token introspections, registrations, etc.) and POSTs the raw event JSON to
fluent-bit's HTTP input at /telemetry/keycloak.

This filter handles all transformation:

  - Event type mapping: Keycloak types are collapsed into PostHog event names
    (e.g. INTROSPECT_TOKEN, REFRESH_TOKEN, CODE_TO_TOKEN → accounts.activity)
  - Identity hashing: userId is SHA-256 hashed for use as PostHog distinct_id
  - Field stripping: Only analytically useful fields are kept (clientId, environment, etc.)
  - PII removal: ipAddress, details map, sessionId, and other sensitive fields are dropped
  - PostHog formatting: Events are reformatted into the PostHog batch API payload

This script needs:

  - POSTHOG_API_KEY (required)
  - ENV (optional, defaults to "dev")

]]--

local sha256 = require('sha2').sha256

-- Keycloak event types mapped to collapsed PostHog event names
local EVENT_MAP = {
    LOGIN = 'accounts.login',
    LOGIN_ERROR = 'accounts.login_error',
    REGISTER = 'accounts.register',
    REGISTER_ERROR = 'accounts.register_error',
    LOGOUT = 'accounts.logout',
    CODE_TO_TOKEN = 'accounts.activity',
    CODE_TO_TOKEN_ERROR = 'accounts.activity',
    INTROSPECT_TOKEN = 'accounts.activity',
    REFRESH_TOKEN = 'accounts.activity',
}

function keycloak_account_callback(tag, timestamp, record)
    local os_env = os.getenv('ENV') or 'dev'
    local batch = {}

    for idx, event in ipairs(record.events) do
        local kc_type = event.type or 'UNKNOWN'
        local user_id = event.userId or ''
        local is_error = string.sub(kc_type, -6) == '_ERROR'

        local distinct_id = 'n/a'
        if user_id ~= '' then
            distinct_id = sha256(user_id)
        end

        batch[idx] = {
            event = EVENT_MAP[kc_type] or 'accounts.activity',
            properties = {
                distinct_id = distinct_id,
                clientId = event.clientId or '',
                environment = os_env,
                service = 'accounts',
                keycloak_event_type = kc_type,
                keycloak_event_id = event.id or '',
                is_error = is_error,
                ['$ip'] = nil,
            },
        }
    end

    local payload = {
        api_key = os.getenv('POSTHOG_API_KEY'),
        historical_migration = false,
        batch = batch,
    }

    return 2, timestamp, payload
end
