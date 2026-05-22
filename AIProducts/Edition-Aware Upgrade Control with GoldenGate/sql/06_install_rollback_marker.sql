set echo on
set serveroutput on
whenever sqlerror exit failure rollback

prompt == Run this while connected as EBR_INSTALL_USER ==

alter session set edition = EBR_INSTALL_EDITION;

merge into SRC_OCIGGLL.EBR_ORDER_DEMO t
using (
  select -1003 as ORDER_ID from dual
) s
on (t.ORDER_ID = s.ORDER_ID)
when matched then update set
  STATUS_CODE = null,
  STATUS_TEXT = 'INSTALL_ROLLBACK',
  SESSION_EDITION = sys_context('USERENV', 'CURRENT_EDITION_NAME'),
  INSTALL_RUN_ID = 'RUN_001',
  UPDATED_BY = sys_context('USERENV', 'SESSION_USER'),
  UPDATED_AT = systimestamp
when not matched then insert
(
  ORDER_ID,
  STATUS_CODE,
  STATUS_TEXT,
  SESSION_EDITION,
  INSTALL_RUN_ID,
  UPDATED_BY,
  UPDATED_AT
)
values
(
  -1003,
  null,
  'INSTALL_ROLLBACK',
  sys_context('USERENV', 'CURRENT_EDITION_NAME'),
  'RUN_001',
  sys_context('USERENV', 'SESSION_USER'),
  systimestamp
);

commit;

prompt == Install-rollback marker committed ==

