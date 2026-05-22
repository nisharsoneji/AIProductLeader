import argparse

from ogg_rest import dump, getenv, request


def set_replicat_status(status):
    replicat = getenv("INSTALL_REPLICAT_NAME", "EBRINSR")
    return request("PATCH", f"/services/v2/replicats/{replicat}", {"status": status})


def rollback_skip():
    # In production this is where you either purge the installer trail or
    # reposition/recreate the installer Replicat after the aborted run.
    return {
        getenv("INSTALL_REPLICAT_NAME", "EBRINSR"): set_replicat_status("stopped"),
        "operator_action": (
            "Do not start EBRINSR for the aborted install. Purge the installer "
            "trail or recreate the installer Replicat from the current end before "
            "the next install run."
        ),
    }


def main():
    parser = argparse.ArgumentParser(
        description="Apply the installer-path outcome for the EBR GoldenGate demo."
    )
    parser.add_argument("outcome", choices=["complete", "rollback"])
    args = parser.parse_args()

    if args.outcome == "complete":
        replicat = getenv("INSTALL_REPLICAT_NAME", "EBRINSR")
        result = {replicat: set_replicat_status("running")}
    else:
        result = rollback_skip()

    dump(result)


if __name__ == "__main__":
    main()
