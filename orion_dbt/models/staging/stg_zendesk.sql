with src as (select * from {{ source('raw', 'raw_zendesk') }})
select
    ticket_id                    as contact_id,
    campaign                     as campaign_id,
    'zendesk'                    as source_system,
    channel                      as channel,
    trim(assignee_id)            as source_agent_id,
    created_at::timestamp        as created_at,
    first_response_at::timestamp as first_response_at,
    solved_at::timestamp         as resolved_at,
    status                       as status_raw,
    case when status in ('solved','closed') then 'resolved' else 'open' end as status,
    wait_seconds                 as answer_seconds,
    satisfaction_score           as csat,
    reopened                     as reopened
from src
where wait_seconds is null or wait_seconds >= 0