with days as (
    select generate_series(
        date '2026-01-01',
        date '2026-12-31',
        interval '1 day'
    )::date as date_day
)
select
    date_day,
    extract(year   from date_day)::int              as year,
    extract(quarter from date_day)::int             as quarter,
    'Q' || extract(quarter from date_day)::int      as quarter_name,
    extract(month  from date_day)::int              as month_num,
    to_char(date_day, 'Mon')                        as month_name,
    to_char(date_day, 'YYYY-MM')                     as year_month,
    to_char(date_day, 'Mon YYYY')                    as year_month_label,
    extract(week   from date_day)::int              as week_num,
    extract(isodow from date_day)::int              as week_day_num,
    to_char(date_day, 'Dy')                         as week_day_name,
    extract(day    from date_day)::int              as day_of_month
from days