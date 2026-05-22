# Edition-Aware Upgrade Control with GoldenGate

This test demonstrates the customer-safe pattern for Oracle EBR installs:

- App changes replicate continuously.
- Installer-edition changes are captured into a separate trail.
- Installer changes are applied only if the install succeeds.
- If the install aborts, the installer trail/Replicat can be discarded without affecting app replication.

## Blog and Runbook

- `docs/edition-aware-upgrade-control-with-goldengate.md`
- `docs/edition-aware-upgrade-control-with-goldengate.docx`

The blog explains GoldenGate EBR support and limitations, the airline-customer business use case, the solution pattern, and both successful-installation and rollback-installation test cases.

## Names

Database: `SOURCE_DB`

GoldenGate deployment: `OGG_DEPLOYMENT`

Source schema: `SRC_OCIGGLL`

Target schema: `SRCMIRROR_OCIGGLL`

Table: `EBR_ORDER_DEMO`

Editions:

- `EBR_APP_EDITION`
- `EBR_INSTALL_EDITION`

DML users:

- `EBR_APP_USER`
- `EBR_INSTALL_USER`

GoldenGate processes:

- `EBRAPPX` extract, trail `ea`
- `EBRAPPR` nonintegrated replicat, checkpoint table `SRCMIRROR_OCIGGLL.GGCHKPT`
- `EBRINSX` extract, trail `ei`
- `EBRINSR` nonintegrated replicat, checkpoint table `SRCMIRROR_OCIGGLL.GGCHKPT`

ATP note: integrated Extract works for capture, but integrated Replicat requires XStream In, which is not supported on Autonomous Database. Use nonintegrated Replicat for this same-ATP demo.

## Core Idea

GoldenGate cannot identify the Oracle edition from redo. The redo contains table-level DML, not the session edition. The solution tested here is to isolate installer DML by database user:

- App Extract excludes `EBR_INSTALL_USER`.
- Installer Extract captures only transactions where `@GETENV('TRANSACTION','USERNAME') = 'EBR_INSTALL_USER'`.
- Installer Replicat stays stopped during the install.
- EMS/event markers notify the installer path controller when the install starts and when it ends.

The table includes `SESSION_EDITION` only as proof that the DML came from the expected edition. It is not used for GoldenGate routing.

## EMS-Controlled Install Outcomes

Use marker rows in the same demo table to model GoldenGate EMS notifications:

- `INSTALL_START`: installer work has started; keep `EBRINSR` stopped.
- `INSTALL_COMPLETE`: install succeeded; start `EBRINSR` so captured installer transactions apply.
- `INSTALL_ROLLBACK`: install failed or was aborted; do not start `EBRINSR`; skip or purge the installer trail and recreate the installer apply path from the current end.

Important: a stopped Replicat cannot see a marker in its own trail and start itself. In production, the marker should be handled by Extract-side EMS/event handling or by an external controller that watches OGG events and calls the Admin API.

## Run Order

1. Run setup as an admin user on `SOURCE_DB`.

```sql
@sql/00_setup_ebr_single_table.sql
```

2. Create the GoldenGate processes using the Admin Service for `OGG_DEPLOYMENT`.

Create the checkpoint table once if it does not already exist:

```text
DBLOGIN USERIDALIAS srcAtp DOMAIN OracleGoldenGate
ADD CHECKPOINTTABLE SRCMIRROR_OCIGGLL.GGCHKPT
```

```sh
source env/ebr.env
python3 -m pip install -r ogg/requirements.txt
python3 ogg/create_ebr_processes.py
```

3. Start only the app path plus installer Extract.

```text
START EXTRACT EBRAPPX
START REPLICAT EBRAPPR
START EXTRACT EBRINSX

Do not start REPLICAT EBRINSR yet.
```

4. Run app DML as `EBR_APP_USER`.

```sql
@sql/01_app_edition_dml.sql
@sql/03_verify_source_target.sql
```

Expected: target receives the app row.

5. Run installer DML as `EBR_INSTALL_USER`.

```sql
@sql/04_install_start_marker.sql
@sql/02_install_edition_dml.sql
@sql/03_verify_source_target.sql
```

Expected: source has `STATUS_TEXT`, but target does not yet have the installer update because `EBRINSR` is stopped.

6. If install succeeds, write an install-complete marker and start installer Replicat.

```sql
@sql/05_install_complete_marker.sql
```

```sh
source env/ebr.env
python3 ogg/install_outcome.py complete
```

Then verify again:

```sql
@sql/03_verify_source_target.sql
```

Expected: target now receives the installer update.

7. If install aborts, write a rollback marker and skip the installer trail.

```sql
@sql/07_app_seed_rollback_row.sql
@sql/08_install_rollback_dml.sql
@sql/06_install_rollback_marker.sql
```

```sh
source env/ebr.env
python3 ogg/install_outcome.py rollback
python3 ogg/reset_install_path_after_rollback.py --new-trail ej
```

The app path remains unaffected.

Expected: target keeps the app-edition state, installer changes from the aborted run are not applied, and the next installer run starts on fresh trail `ej`.
