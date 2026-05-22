set echo on
set serveroutput on
whenever sqlerror exit failure rollback

prompt == Run this while connected as EBR_INSTALL_USER ==

alter session set edition = EBR_INSTALL_EDITION;

update SRC_OCIGGLL.EBR_ORDER_DEMO
set STATUS_TEXT = 'NEW_STATUS_VALUE',
    SESSION_EDITION = sys_context('USERENV', 'CURRENT_EDITION_NAME'),
    INSTALL_RUN_ID = 'RUN_001',
    UPDATED_BY = sys_context('USERENV', 'SESSION_USER'),
    UPDATED_AT = systimestamp
where ORDER_ID = 1;

commit;

prompt == Installer-edition DML committed ==

