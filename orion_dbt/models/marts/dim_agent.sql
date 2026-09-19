with zoho as (select * from {{ source('raw', 'raw_zoho_agents') }})
select
    zoho_employee_id   as agent_key,
    full_name          as agent_name,
    zendesk_agent_id,
    intercom_admin_id
from zoho