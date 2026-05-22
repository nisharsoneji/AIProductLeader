set define off
set echo off
set verify off
set serveroutput on
whenever sqlerror exit failure rollback

set define on
accept EBR_APP_PASSWORD char prompt 'Enter password for EBR_APP_USER: ' hide
accept EBR_INSTALL_PASSWORD char prompt 'Enter password for EBR_INSTALL_USER: ' hide

prompt == Create EBR editions when missing ==

declare
  l_count number;
begin
  select count(*) into l_count from dba_editions where edition_name = 'EBR_APP_EDITION';
  if l_count = 0 then
    execute immediate 'create edition EBR_APP_EDITION';
  end if;

  select count(*) into l_count from dba_editions where edition_name = 'EBR_INSTALL_EDITION';
  if l_count = 0 then
    execute immediate 'create edition EBR_INSTALL_EDITION as child of EBR_APP_EDITION';
  end if;
end;
/

prompt == Create DML users when missing ==

declare
  l_count number;
begin
  select count(*) into l_count from dba_users where username = 'EBR_APP_USER';
  if l_count = 0 then
    execute immediate 'create user EBR_APP_USER identified by "' || replace('&EBR_APP_PASSWORD', '"', '""') || '"';
  end if;

  select count(*) into l_count from dba_users where username = 'EBR_INSTALL_USER';
  if l_count = 0 then
    execute immediate 'create user EBR_INSTALL_USER identified by "' || replace('&EBR_INSTALL_PASSWORD', '"', '""') || '"';
  end if;
end;
/

set echo on

grant create session to EBR_APP_USER;
grant create session to EBR_INSTALL_USER;
grant alter session to EBR_APP_USER;
grant alter session to EBR_INSTALL_USER;
grant use on edition EBR_APP_EDITION to EBR_APP_USER;
grant use on edition EBR_INSTALL_EDITION to EBR_INSTALL_USER;

prompt == Enable editions on source-side users ==

begin
  execute immediate 'alter user SRC_OCIGGLL enable editions';
exception
  when others then
    if sqlcode not in (-38819) then
      raise;
    end if;
end;
/

begin
  execute immediate 'alter user EBR_APP_USER enable editions';
exception
  when others then
    if sqlcode not in (-38819) then
      raise;
    end if;
end;
/

begin
  execute immediate 'alter user EBR_INSTALL_USER enable editions';
exception
  when others then
    if sqlcode not in (-38819) then
      raise;
    end if;
end;
/

prompt == Recreate the one source and target table ==

begin
  execute immediate 'drop table SRC_OCIGGLL.EBR_ORDER_DEMO purge';
exception
  when others then
    if sqlcode != -942 then
      raise;
    end if;
end;
/

begin
  execute immediate 'drop table SRCMIRROR_OCIGGLL.EBR_ORDER_DEMO purge';
exception
  when others then
    if sqlcode != -942 then
      raise;
    end if;
end;
/

create table SRC_OCIGGLL.EBR_ORDER_DEMO
(
  ORDER_ID        number primary key,
  STATUS_CODE     varchar2(10),
  STATUS_TEXT     varchar2(50),
  SESSION_EDITION varchar2(128),
  INSTALL_RUN_ID  varchar2(30),
  UPDATED_BY      varchar2(128),
  UPDATED_AT      timestamp
);

create table SRCMIRROR_OCIGGLL.EBR_ORDER_DEMO
(
  ORDER_ID        number primary key,
  STATUS_CODE     varchar2(10),
  STATUS_TEXT     varchar2(50),
  SESSION_EDITION varchar2(128),
  INSTALL_RUN_ID  varchar2(30),
  UPDATED_BY      varchar2(128),
  UPDATED_AT      timestamp
);

grant select, insert, update, delete on SRC_OCIGGLL.EBR_ORDER_DEMO to EBR_APP_USER;
grant select, insert, update, delete on SRC_OCIGGLL.EBR_ORDER_DEMO to EBR_INSTALL_USER;

alter table SRC_OCIGGLL.EBR_ORDER_DEMO add supplemental log data (primary key) columns;

prompt == Setup complete ==
