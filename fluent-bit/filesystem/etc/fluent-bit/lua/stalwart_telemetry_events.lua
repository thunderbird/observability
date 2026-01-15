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

This script requires the presence of the following environment variables:

  - POSTHOG_API_KEY (required)
  - ENV (optional, defaults to "dev")

]]--


--[[  Main callback function that fluent-bit will call.  ]]--
function stalwart_telemetry_callback(tag, timestamp, record)
    -- Sanitize all events in the record
    sanitized_events = {}
    for idx, event in ipairs(record.events)
    do
        sanitized_events[idx] = sanitize_event(event)
    end

    -- Normalize all events in the record
    for idx, event in ipairs(sanitized_events)
    do
        sanitized_events[idx] = normalize_event(event)
    end

    -- Reformat the events as a Posthog batch API payload
    record = format_events_as_posthog_batch(sanitized_events)

    return 2, timestamp, record
end

--[[  Removes unwanted content from events. Returns a table with keys `event_id` (a unique
      identifier for the event), `event_type` (its classifier), and `event` (the actual record
      with some content removed).  ]]--
function sanitize_event(event)
    -- Extract the ID and type from the event
    event_id = event.id
    event_type = event.type

    -- If there's no type, then we don't know how to deal with it. We just return it.
    if (not event_type)
    then
        print('Stalwart telemetry record contains no event type. Returning the record unmodified.')
        return {
            event_id = event_id,
            event_type = nil,
            event = event
        }
    end

    -- There's an event type? We might know how to process it.
    sanitized_event = nil
    
    -- delivery.delivered emits when an email is successfully delivered to an inbox.
    if (event_type == 'delivery.delivered')
    then
        sanitized_event = sanitize_delivery_delivered_event(event.data)
    end

    -- If we don't recognize the event type, log a message so we can review later.
    if (not sanitized_event)
    then
        print('Unknown Stalwart telemetry event type:', event_type, '. Returning the record unmodified.')
        return {
            event_id = event_id,
            event_type = event_type,
            event = event
        }
    else
        -- Ideally, we get here and return a sanitized event.
        return {
            event_id = event_id,
            event_type = event_type,
            event = sanitized_event,
        }
    end
end

--[[  Sanitize delivery.delivered events  ]]--
function sanitize_delivery_delivered_event(event)
    event.to = nil
    event.details = nil
    return event
end

--[[  Add common fields to events  ]]--
function normalize_event(sanitized_event)
    os_env = os.getenv('ENV') or 'dev'
    sanitized_event.event.service = 'thundermail'
    sanitized_event.event.environment = os_env
    return sanitized_event
end

--[[  Convert sanitized Stalwart telemetry events into a format the Posthog API can read.  ]]--
function format_events_as_posthog_batch(sanitized_events)
    -- This will be the new record format
    payload = {
        api_key = os.getenv('POSTHOG_API_KEY'),
        historical_migration = false,
    }
    
    -- Convert "event" entries into "batch" entries
    batch = {}
    for idx, event in ipairs(sanitized_events)
    do
        batch[idx] = {
            -- Prefix the event types from Stalwart with the "thundermail" term
            event = 'thundermail.' .. event.event_type,
            properties = event.event,
        }
        batch[idx].properties.distinct_id = event.event_id
    end
    payload.batch = batch

    return payload
end
