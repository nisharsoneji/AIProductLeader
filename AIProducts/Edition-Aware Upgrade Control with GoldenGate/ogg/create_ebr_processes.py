from ogg_rest import dump, enc, getenv, request


domain = getenv("OGG_DOMAIN", "OracleGoldenGate")
source_alias = getenv("OGG_SOURCE_ALIAS", "srcAtp")
target_alias = getenv("OGG_TARGET_ALIAS", source_alias)
checkpoint_table = getenv("OGG_CHECKPOINT_TABLE", "SRCMIRROR_OCIGGLL.GGCHKPT")
src_schema = getenv("SRC_SCHEMA", "SRC_OCIGGLL")
tgt_schema = getenv("TGT_SCHEMA", "SRCMIRROR_OCIGGLL")
table = getenv("EBR_TABLE", "EBR_ORDER_DEMO")
install_user = getenv("INSTALL_USER", "EBR_INSTALL_USER")
managed_settings = "ogg:managedProcessSettings:Default"

app_extract = getenv("APP_EXTRACT_NAME", "EBRAPPX")
app_replicat = getenv("APP_REPLICAT_NAME", "EBRAPPR")
app_trail = getenv("APP_TRAIL_NAME", "ea")

install_extract = getenv("INSTALL_EXTRACT_NAME", "EBRINSX")
install_replicat = getenv("INSTALL_REPLICAT_NAME", "EBRINSR")
install_trail = getenv("INSTALL_TRAIL_NAME", "ei")


def extract_payload(name, trail, config):
    return {
        "config": config,
        "source": {"tranlogs": "integrated"},
        "credentials": {"domain": domain, "alias": source_alias},
        "managedProcessSettings": managed_settings,
        "registration": {"optimized": False},
        "begin": "now",
        "status": "stopped",
        "targets": [{"name": trail}],
    }


def replicat_payload(name, trail, config):
    return {
        "config": config,
        "credentials": {"domain": domain, "alias": target_alias},
        "checkpoint": {"table": checkpoint_table},
        "managedProcessSettings": managed_settings,
        "mode": {"type": "nonintegrated"},
        "registration": "none",
        "status": "stopped",
        "begin": "now",
        "source": {"name": trail},
    }


app_extract_config = [
    f"EXTRACT {app_extract}",
    f"EXTTRAIL {app_trail}",
    f"USERIDALIAS {source_alias} DOMAIN {domain}",
    f"TRANLOGOPTIONS EXCLUDEUSER {install_user}",
    f"TABLE {src_schema}.{table};",
]

app_replicat_config = [
    f"REPLICAT {app_replicat}",
    f"USERIDALIAS {target_alias} DOMAIN {domain}",
    f"MAP {src_schema}.{table}, TARGET {tgt_schema}.{table};",
]

install_extract_config = [
    f"EXTRACT {install_extract}",
    f"EXTTRAIL {install_trail}",
    f"USERIDALIAS {source_alias} DOMAIN {domain}",
    (
        f"TABLE {src_schema}.{table}, "
        f"FILTER (@STREQ (@GETENV ('TRANSACTION', 'USERNAME'), '{install_user}'));"
    ),
]

install_replicat_config = [
    f"REPLICAT {install_replicat}",
    f"USERIDALIAS {target_alias} DOMAIN {domain}",
    f"MAP {src_schema}.{table}, TARGET {tgt_schema}.{table};",
]

result = {
    "app_extract": request(
        "POST",
        f"/services/v2/extracts/{enc(app_extract)}",
        extract_payload(app_extract, app_trail, app_extract_config),
    ),
    "app_replicat": request(
        "POST",
        f"/services/v2/replicats/{enc(app_replicat)}",
        replicat_payload(app_replicat, app_trail, app_replicat_config),
    ),
    "install_extract": request(
        "POST",
        f"/services/v2/extracts/{enc(install_extract)}",
        extract_payload(install_extract, install_trail, install_extract_config),
    ),
    "install_replicat": request(
        "POST",
        f"/services/v2/replicats/{enc(install_replicat)}",
        replicat_payload(install_replicat, install_trail, install_replicat_config),
    ),
}

dump(result)
