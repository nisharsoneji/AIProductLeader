set linesize 220
set pagesize 100
column SIDE format a8
column STATUS_CODE format a12
column STATUS_TEXT format a18
column SESSION_EDITION format a24
column INSTALL_RUN_ID format a14
column UPDATED_BY format a18

select 'SOURCE' as SIDE,
       ORDER_ID,
       STATUS_CODE,
       STATUS_TEXT,
       SESSION_EDITION,
       INSTALL_RUN_ID,
       UPDATED_BY,
       UPDATED_AT
from SRC_OCIGGLL.EBR_ORDER_DEMO
union all
select 'TARGET' as SIDE,
       ORDER_ID,
       STATUS_CODE,
       STATUS_TEXT,
       SESSION_EDITION,
       INSTALL_RUN_ID,
       UPDATED_BY,
       UPDATED_AT
from SRCMIRROR_OCIGGLL.EBR_ORDER_DEMO
order by SIDE, ORDER_ID;

