#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2021 Rose Davidson <rose@metaclassical.com>
# SPDX-FileCopyrightText: 2019 Cosimo Lupo <cosimo@anthrotype.com>
#
# SPDX-License-Identifier: MIT

"""Script to fix weights and flags in the iA Writer Quattro S font files and rename the
fonts according with the license requirement.
This is derived from https://github.com/fonttools/fonttools/blob/4.24.4/Snippets/rename-fonts.py
"""
import argparse
import enum
import logging
import os
import pathlib

from fontTools.ttLib import TTFont

# We can't rely on any of the internal flags being correct.
# we should get the style from the names, and then set
# head->macStyle, OS/2->fsSelection, etc correctly

logger = logging.getLogger()


INPUT_FAMILY_NAME = "iA Writer Quattro S"
INPUT_POSTSCRIPT_FAMILY_NAME = "iAWriterQuattroS"

OUTPUT_FAMILY_NAME = "Tabula Quattro"
OUTPUT_POSTSCRIPT_FAMILY_NAME = "TabulaQuattro"


class NameId(enum.IntEnum):
    COPYRIGHT = 0
    FAMILY = 1
    SUBFAMILY = 2
    UNIQUE_ID = 3
    FULL_NAME = 4
    VERSION = 5
    POSTSCRIPT_NAME = 6
    TRADEMARK = 7
    MANUFACTURER = 8
    DESIGNER = 9
    DESCRIPTION = 10
    VENDOR_URL = 11
    DESIGNER_URL = 12
    LICENSE = 13
    LICENSE_URL = 14
    PREFERRED_FAMILY = 16
    PREFERRED_SUBFAMILY = 17
    SAMPLE_TEXT = 19


class Style(enum.Enum):
    REGULAR = "Regular"
    BOLD = "Bold"
    ITALIC = "Italic"
    BOLDITALIC = "Bold Italic"


# useful to see in different case styles
PANGRAM = "Sphinx of black quartz, judge my vow.\nSPHINX OF BLACK QUARTZ, JUDGE MY VOW.\nsphinx of black quartz, judge my vow."

WINDOWS_ENGLISH_IDS = 3, 1, 0x409
MAC_ROMAN_IDS = 1, 0, 0


def detect_style(font):
    return Style(
        font["name"]
        .getName(nameID=NameId.SUBFAMILY, platformID=3, platEncID=1)
        .toUnicode()
    )


def set_bit(value, bit):
    return value | (1 << bit)


def clear_bit(value, bit):
    return value & ~(1 << bit)


def set_flags(font, font_style: Style):
    # https://docs.microsoft.com/en-us/typography/opentype/spec/namesmp

    os2 = font["OS/2"]
    head = font["head"]

    # start by setting base values
    os2.usWeightClass = 400
    fsSelection = os2.fsSelection
    for bit in (0, 1, 2, 3, 4, 5, 6):
        clear_bit(fsSelection, bit)
    os2.fsSelection = fsSelection
    head.macStyle = 0

    if font_style is Style.REGULAR:
        os2.fsSelection = set_bit(os2.fsSelection, 6)
    if font_style in (Style.BOLD, Style.BOLDITALIC):
        os2.usWeightClass = 700
        os2.fsSelection = set_bit(os2.fsSelection, 5)
        head.macStyle = set_bit(head.macStyle, 0)
    if font_style in (Style.ITALIC, Style.BOLDITALIC):
        os2.fsSelection = set_bit(os2.fsSelection, 0)
        head.macStyle = set_bit(head.macStyle, 1)


def replace_names(font):
    table = font["name"]

    for rec in table.names:
        try:
            name_id = NameId(rec.nameID)
        except ValueError:
            continue

        if name_id is NameId.COPYRIGHT:
            rec.string = "Copyright 2021 Rose Davidson, " + rec.toUnicode()
        elif name_id is NameId.FAMILY:
            rec.string = OUTPUT_FAMILY_NAME
        elif name_id is NameId.UNIQUE_ID:
            rec.string = rec.toUnicode().replace(
                INPUT_POSTSCRIPT_FAMILY_NAME, OUTPUT_POSTSCRIPT_FAMILY_NAME
            )
        elif name_id is NameId.FULL_NAME:
            rec.string = rec.toUnicode().replace(INPUT_FAMILY_NAME, OUTPUT_FAMILY_NAME)
        elif name_id is NameId.POSTSCRIPT_NAME:
            rec.string = rec.toUnicode().replace(
                INPUT_POSTSCRIPT_FAMILY_NAME, OUTPUT_POSTSCRIPT_FAMILY_NAME
            )
        elif name_id is NameId.MANUFACTURER:
            rec.string = "Straylight Labs and " + rec.toUnicode()
        elif name_id in {NameId.VENDOR_URL, NameId.DESIGNER_URL}:
            rec.string = "https://metaclassical.com"

    # Now let's add some values
    for plat_id, enc_id, lang_id in (WINDOWS_ENGLISH_IDS, MAC_ROMAN_IDS):
        table.setName("OFL-1.1-RFN", NameId.LICENSE, plat_id, enc_id, lang_id)
        table.setName(
            "http://scripts.sil.org/OFL", NameId.LICENSE_URL, plat_id, enc_id, lang_id
        )
        table.setName(PANGRAM, NameId.SAMPLE_TEXT, plat_id, enc_id, lang_id)


def main(args=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("input_fonts", metavar="FONTFILE", nargs="+")
    parser.add_argument("-d", "--output-dir", type=pathlib.Path, default=os.getcwd())
    parser.add_argument("-v", "--verbose", action="count", default=0)
    options = parser.parse_args(args)

    if not options.verbose:
        level = "WARNING"
    elif options.verbose == 1:
        level = "INFO"
    else:
        level = "DEBUG"
    logging.basicConfig(level=level, format="%(message)s")

    for input_name in options.input_fonts:
        logger.info("Renaming font: '%s'", input_name)

        font = TTFont(input_name)
        font_style = detect_style(font)
        replace_names(font)
        set_flags(font, font_style)

        style_filename_component = font_style.value.replace(" ", "")
        output_path = (
            options.output_dir
            / f"{OUTPUT_POSTSCRIPT_FAMILY_NAME}-{style_filename_component}.ttf"
        )
        output_name = str(output_path)

        font.save(output_name)
        logger.info("Saved font: '%s'", output_name)

        font.close()
        del font

    logger.info("Done!")


if __name__ == "__main__":
    main()
