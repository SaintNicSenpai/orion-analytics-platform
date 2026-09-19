with src as (select * from {{ source('raw', 'raw_intercom') }})
select
    conversation_id                        as contact_id,
    campaign                               as campaign_id,
    'intercom'                             as source_system,
    medium                                 as channel,
    trim(admin_id)                         as source_agent_id,
    created_at::timestamp                  as created_at,
    first_reply_at::timestamp              as first_response_at,
    closed_at::timestamp                   as resolved_at,
    state                                  as status_raw,
    case when state = 'closed' then 'resolved' else 'open' end as status,
    round(time_to_first_reply_ms / 1000.0) as answer_seconds,
    conversation_rating                    as csat,
    case when reopened_flag = 'Y' then true else false end as reopened
from src
where time_to_first_reply_ms is null or time_to_first_reply_ms >= 0