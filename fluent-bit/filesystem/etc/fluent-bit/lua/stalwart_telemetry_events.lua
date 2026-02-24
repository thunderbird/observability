--[[
    stalwart_telemetry_events.lua

This module acts as a fluent-bit event processor for Stalwart telemetry events. fluent-bit receives
a batch of events from Stalwart in an HTTP message via a webhook setup in Stalwart. Those messages
are not ready to ship to Posthog, so here we put them through a three-stage process:

  - Sanitization: Removal of data from the event which we do not wish to surface to Posthog.
  - Normalization: Addition of common fields to the event.
  - Reformatting: Converting the record into a format that can be shipped to Posthog's API.

Documentation on how this script and fluent-bit interact can be found here:

    https://docs.fluentbit.io/manual/data-pipeline/filters/lua

This script desires the presence of the following environment variables:

  - POSTHOG_API_KEY (required)
  - ENV (optional, defaults to "dev")
  - FLUENTBIT_STALWART_DELETE_KEYS (Optional; Comma-separated keys in the Stalwart event to delete during sanitization)
  - FLUENTBIT_STALWART_HASH_KEYS (Optional, Comma-separated keys in the Stalwart event to replace with md5 hashes)

The last two options refer to key types found in these docs:

    https://stalw.art/docs/telemetry/events#key-types

]]--

local md5 = require('sha2').md5

-- [[ Returns an environment variable or a default value if it's not set ]]
function getenv_or_default(env_var, default)
    var = os.getenv(env_var)
    if (var == nil) then
        return default
    end
    return var
end

-- [[ Splits a single string into a table of its substrings separated by commas ]]
function split_str(str)
    tab = {}
    for s in string.gmatch(str, '[^,]+') do
        table.insert(tab, s)
    end
    return tab
end

-- [[ Returns true if the needle value is found in the haystack array ]]
function value_in_array(haystack, needle)
    for _, item in pairs(haystack) do
        if (item == needle) then
            return true
        end
    end
    return false
end

--[[  Main callback function that fluent-bit will call.  ]]--
function stalwart_telemetry_callback(tag, timestamp, record)
    -- Sanitize all events in the record
    events = {}
    for idx, event in ipairs(record.events) do
        events[idx] = sanitize_event(event)
    end

    -- Normalize all events in the record
    for idx, event in ipairs(events) do
        events[idx] = normalize_event(event)
    end

    -- Reformat the events as a Posthog batch API payload
    record = format_events_as_posthog_batch(events)

    return 2, timestamp, record
end

--[[  Removes unwanted content from an event. Returns the event as presented, with some keys
      removed or hashed for obscurity. ]] --
function sanitize_event(event)
    -- Get delete and hash keys from the environment
    local delete_keys = split_str(getenv_or_default('FLUENTBIT_STALWART_DELETE_KEYS'))
    local hash_keys = split_str(getenv_or_default('FLUENTBIT_STALWART_HASH_KEYS'))

    for key, value in next,event.data do
        if value_in_array(delete_keys, key) then
            -- Delete any keys we want totally gone
            event.data[value] = nil
        elseif value_in_array(hash_keys, key) then
            -- Replace certain other values with hashes, ensuring they're strings first
            if (type(event.data[key]) ~= 'string') then
                event.data[key] = tostring(event.data[key])
            end
            event.data[key] = md5(event.data[key])
        end
    end

    return event
end

--[[  Add common fields to events  ]]--
function normalize_event(event)
    -- distinct_id is used by Posthog to refer to a unique user. Today we use "from" but we would
    -- like this to be the Stalwart account ID (or a hash of it)
    event.data.distinct_id = event.data.from or 'n/a'
    
    -- These are our internally recognized common fields
    os_env = os.getenv('ENV') or 'dev'
    event.data.environment = os_env
    event.data.service = 'thundermail'
    event.data.stalwart_event_id = event.id
    return event
end

--[[  Convert sanitized Stalwart telemetry events into a format the Posthog API can read.  ]]--
function format_events_as_posthog_batch(events)
    -- This will be the new record format
    payload = {
        api_key = os.getenv('POSTHOG_API_KEY'),
        historical_migration = false,
    }
    
    -- Convert "event" entries into "batch" entries
    batch = {}
    for idx, event in ipairs(events) do
        batch[idx] = {
            -- Prefix the event types from Stalwart with the "thundermail" term
            event = 'thundermail.' .. event.type,
            properties = event.data,
        }
    end
    payload.batch = batch

    return payload
end