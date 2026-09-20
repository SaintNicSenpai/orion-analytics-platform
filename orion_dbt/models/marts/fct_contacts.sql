with unioned as (
    select contact_id, campaign_id, source_system, channel, source_agent_id,
           created_at, first_response_at, resolved_at, status, answer_seconds, csat, reopened
    from {{ ref('stg_zendesk') }}
    union all
    select contact_id, campaign_id, source_system, channel, source_agent_id,
           created_at, first_response_at, resolved_at, status, answer_seconds, csat, reopened
    from {{ ref('stg_intercom') }}
),
targets as (
    select campaign as campaign_id, target_value::numeric as answer_target_sec
    from {{ source('raw', 'raw_sla_targets') }}
    where metric = 'answer_seconds'
),
agents as (
    select agent_key, agent_name, zendesk_agent_id, intercom_admin_id
    from {{ ref('dim_agent') }}
),
dates as (
    select * from {{ ref('dim_date') }}
)
select
    u.contact_id,
    u.campaign_id,
    u.source_system,
    u.channel,
    u.created_at,
    u.created_at::date              as contact_date,
    d.year,
    d.quarter_name,
    d.month_num,
    d.month_name,
    d.year_month,
    d.year_month_label,
    d.week_num,
    d.week_day_name,
    u.status,
    u.answer_seconds,
    t.answer_target_sec,
    case when u.answer_seconds is not null
         then u.answer_seconds <= t.answer_target_sec end as within_sla,
    coalesce(a.agent_key, 'UNMAPPED') as agent_key,
    coalesce(a.agent_name, 'Unmapped agent') as agent_name,
    u.csat,
    u.reopened,
    case when u.resolved_at is not null
         then extract(epoch from (u.resolved_at - u.created_at))/60.0 end as resolution_minutes
from unioned u
left join targets t on u.campaign_id = t.campaign_id
left join agents a
    on (u.source_system = 'zendesk'  and u.source_agent_id = a.zendesk_agent_id)
    or (u.source_system = 'intercom' and u.source_agent_id = a.intercom_admin_id)
left join dates d on u.created_at::date = d.date_day