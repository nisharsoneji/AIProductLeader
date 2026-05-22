import argparse

from ogg_rest import dump, enc, getenv, request


domain = getenv("OGG_DOMAIN", "OracleGoldenGate")
source_alias = getenv("OGG_SOURCE_ALIAS", "srcAtp")
target_alias = getenv("OGG_TARGET_ALIAS", source_alias)
checkpoint_table = getenv("OGG_CHECKPOINT_TABLE", "SRCMIRROR_OCIGGLL.GGCHKPT")
src_schema = getenv("SRC_SCHEMA", "SRC_OCIGGLL")
tgt_schema = getenv("TGT_SCHEMA", "SRCMIRROR_OCIGGLL")
table = getenv("EBR_TABLE", "EBR_ORDER_DEMO")
install_user = getenv("INSTALL_USER", "EBR_INSTALL_USER")
install_extract = getenv("INSTALL_EXTRACT_NAME", "EBRINSX")
install_replicat = getenv("INSTALL_REPLICAT_NAME", "EBRINSR")
managed_settings = "ogg:managedProcessSettings:Default"


def set_status(kind, name, status):
    return request("PATCH", f"/services/v2/{kind}/{enc(name)}", {"status": status})


def delete(kind, name):
    return request("DELETE", f"/services/v2/{kind}/{enc(name)}")


def extract_payload(trail):
    return {
        "config": [
            f"EXTRACT {install_extract}",
            f"EXTTRAIL {trail}",
            f"USERIDALIAS {source_alias} DOMAIN {domain}",
            (
                f"TABLE {src_schema}.{table}, "
                f"FILTER (@STREQ (@GETENV ('TRANSACTION', 'USERNAME'), '{install_user}'));"
            ),
        ],
        "source": {"tranlogs": "integrated"},
        "credentials": {"domain": domain, "alias": source_alias},
        "managedProcessSettings": managed_settings,
        "registration": {"optimized": False},
        "begin": "now",
        "status": "stopped",
        "targets": [{"name": trail}],
    }


def replicat_payload(trail):
    return {
        "config": [
            f"REPLICAT {install_replicat}",
            f"USERIDALIAS {target_alias} DOMAIN {domain}",
            f"MAP {src_schema}.{table}, TARGET {tgt_schema}.{table};",
        ],
        "credentials": {"domain": domain, "alias": target_alias},
        "checkpoint": {"table": checkpoint_table},
        "managedProcessSettings": managed_settings,
        "mode": {"type": "nonintegrated"},
        "registration": "none",
        "status": "stopped",
        "begin": "now",
        "source": {"name": trail},
    }


def main():
    parser = argparse.ArgumentParser(
        description="Recreate the installer OGG path after an aborted EBR install."
    )
    parser.add_argument(
        "--new-trail",
        default=getenv("NEXT_INSTALL_TRAIL_NAME", "ej"),
        help="Fresh two-character local trail name for the next installer run.",
    )
    args = parser.parse_args()

    result = {
        "stop_replicat": set_status("replicats", install_replicat, "stopped"),
        "stop_extract": set_status("extracts", install_extract, "stopped"),
        "delete_replicat": delete("replicats", install_replicat),
        "delete_extract": delete("extracts", install_extract),
        "create_extract": request(
            "POST",
            f"/services/v2/extracts/{enc(install_extract)}",
            extract_payload(args.new_trail),
        ),
        "create_replicat": request(
            "POST",
            f"/services/v2/replicats/{enc(install_replicat)}",
            replicat_payload(args.new_trail),
        ),
        "start_extract": set_status("extracts", install_extract, "running"),
        "held_replicat": install_replicat,
        "new_trail": args.new_trail,
    }
    dump(result)


if __name__ == "__main__":
    main()
