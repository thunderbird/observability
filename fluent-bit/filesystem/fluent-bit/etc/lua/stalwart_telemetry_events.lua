-- Docs: https://docs.fluentbit.io/manual/data-pipeline/filters/lua

function stalwart_telemetry_callback(tag, timestamp, record)
    sanitized_events = {}
    for idx, event in ipairs(record.events)
    do
        sanitized_events[idx] = sanitize_event(event)
    end

    for idx, event in ipairs(sanitized_events)
    do
        sanitized_events[idx] = normalize_event(event)
    end

    record = format_events_as_posthog_batch(sanitized_events)

    return 2, timestamp, record
end

function sanitize_event(event)
    -- Returns event_id, event_type, event
    event_id = event.id
    event_type = event.type

    if (not event_type)
    then
        print('Stalwart telemetry record contains no event type. Returning the record unmodified.')
        return {
            event_id = event_id,
            event_type = nil,
            event = event
        }
    end

    sanitized_event = nil
    if (event_type == 'delivery.delivered')
    then
        sanitized_event = sanitize_delivery_delivered_event(event.data)
    end

    if (not sanitized_event)
    then
        print('Unknown Stalwart telemetry event type:', event_type, '. Returning the record unmodified.')
        return {
            event_id = event_id,
            event_type = event_type,
            event = event
        }
    else
        return {
            event_id = event_id,
            event_type = event_type,
            event = sanitized_event,
        }
    end
end

function sanitize_delivery_delivered_event(event)
    event.to = nil
    event.details = nil
    return event
end

function normalize_event(sanitized_event)
    os_env = os.getenv('ENV') or 'dev'
    sanitized_event.event.service = 'thundermail'
    sanitized_event.event.environment = os_env
    return sanitized_event
end

function get_posthog_api_key()
    return os.getenv('POSTHOG_API_KEY')
end

function format_events_as_posthog_batch(sanitized_events)
    payload = {
        api_key = get_posthog_api_key(),
        historical_migration = false,
    }
    batch = {}
    for idx, event in ipairs(sanitized_events)
    do
        batch[idx] = {
            event = 'thundermail.' .. event.event_type,
            properties = event.event,
        }
        batch[idx].properties.distinct_id = event.event_id
    end
    payload.batch = batch

    return payload
end
