#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 Rose Davidson <rose@metaclassical.com>
#
# SPDX-License-Identifier: MIT

import pathlib
import zipfile
import logging

from fontTools.ttLib import TTFont

logger = logging.getLogger()


VERSION_ID = 5


def get_version():
    font = TTFont("TabulaQuattro-Regular.ttf")
    table = font["name"]
    for rec in table.names:
        if rec.nameID == VERSION_ID:
            version = rec.toUnicode()
            if version.lower().startswith("version "):
                version = version.split()[1]
            return version


# Could probably extract this from the .license files, but eh.
USAGE_TERMS = """
This font is licensed under the OFL-1.1 with Reserved Font Names. See OFL-1.1-RFN.txt or http://scripts.sil.org/OFL for details.

Copyright © 2021 Rose Davidson with Reserved Font Name "Tabula Quattro"

Copyright © 2018 Information Architects Inc. with Reserved Font Name "iA Writer"
Copyright © 2017 IBM Corp. with Reserved Font Name "Plex"
""".strip().encode(
    "utf-8"
)


def main():
    logging.basicConfig(level="INFO", format="%(message)s")

    font_version = get_version()

    logging.info(f"Making releases for Tabula Quattro {font_version}")

    cwd = pathlib.Path(".")
    font_files = sorted(cwd.glob("*.ttf"))
    ancillary_files = [cwd / "README.md", cwd / "LICENSES" / "OFL-1.1-RFN.txt"]

    with zipfile.ZipFile(f"tabula-quattro-{font_version}.zip", "w") as outzip:
        for included_file in font_files + ancillary_files:
            outzip.writestr(included_file.name, included_file.read_bytes())

        outzip.writestr("USAGE_TERMS.md", USAGE_TERMS)

    logger.info("Done!")


if __name__ == "__main__":
    main()
