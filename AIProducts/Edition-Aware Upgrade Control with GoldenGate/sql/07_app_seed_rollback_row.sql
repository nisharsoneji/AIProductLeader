set echo on
set serveroutput on
whenever sqlerror exit failure rollback

prompt == Run this while connected as EBR_APP_USER ==

alter session set edition = EBR_APP_EDITION;

insert into SRC_OCIGGLL.EBR_ORDER_DEMO
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
  2,
  'N',
  null,
  sys_context('USERENV', 'CURRENT_EDITION_NAME'),
  null,
  sys_context('USERENV', 'SESSION_USER'),
  systimestamp
);

commit;

prompt == App rollback-test seed row committed ==
