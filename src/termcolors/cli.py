import argparse
from datetime import datetime
from pathlib import Path
from sys import exit as sysexit
from typing import List, Dict

import pyperclip

from .lib.m_utils.printing import (ARED, ARST,
                                   num_to_fg_ansi,  num_to_bg_ansi,
                                   term_del_line)
from .lib.palette import PALETTE_FOLDER, list_palettes
from .lib.softdev.user_input import get_input
from .lib.softdev.debug import RangeError, cprintd

from . import APPNAME, ROOTPATH
from .__about__ import __version__ as VERSION

FTITLE = __file__.split("/", maxsplit=-1)[-1].split(".", maxsplit=-1)[0]

STATE = {'color': "", 'ansi_code': "", 'rgb': tuple(), 'hexa': "",
         'new': False, 'lines_to_del': 1, 'after_help': False,
         'del_lines_called': [], 'log': [],
         'parser': None}
HELP_LINES = 11  # 9
COPYCOMMAND = ["fg", "bg"]

cprint = print


def decm(value: str) -> int:
    result = int(value, 10)
    return range_check(result)


def hexa(value: str) -> int:
    result = int(value, 16)
    return range_check(result)


def prct(value: str) -> int:
    result = int(float(value) * 255)
    return range_check(result)


def range_check(value: int | float) -> int:
    if not 0 <= value <= 255:
        err = f"Value {value!r} is out of range <0-255>"
        raise RangeError(err)
    return int(value)


def color_hex_to_rgb(color: str) -> tuple:
    # cprintd(f"{color = }", location=f"{APPNAME}::{FTITLE}.color_hex_to_rgb")
    return tuple(int(color.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4))


def del_lines(source: str = "?") -> None:
    if STATE['after_help']:
        term_del_line(HELP_LINES)
        STATE['after_help'] = False
        STATE['del_lines_called'].append((source, HELP_LINES))
        return
    term_del_line(STATE['lines_to_del'])
    STATE['lines_to_del'] = 1
    STATE['del_lines_called'].append((source, 1))


METHOD = {'current': "decm"}
CONVERSIONS = {"decm": decm,
               "hexa": hexa,
               "prct": prct}


def change_method(shortcut: str) -> None:
    METHOD['current'] = shortcut
    del_lines("change_method")


def quit() -> None:
    del_lines(source="quit") if not STATE['parser'].parse_args().file else None
    # del_lines(source="quit")
    print("quiting...")
    cprintd(f"{STATE['del_lines_called'] = }",
            location=f"{APPNAME}::{FTITLE}.quit")
    cprintd(f"{STATE['log'] = }", location=f"{APPNAME}::{FTITLE}.quit")
    sysexit(0)


COMMANDS = {'decm':    lambda: change_method('decm'),
            'hexa':    lambda: change_method('hexa'),
            'prct':    lambda: change_method('prct'),
            'help':    lambda: usage(quit=False),
            'palette': lambda: palette(),
            'quit':    lambda: quit(),
            'q':       lambda: quit()}

NAMES = {'decm': {'method': "decimal",
                  'desc': "sets conversion from decimal format"},
         'hexa': {'method': "hexadecimal",
                  'desc': "sets conversion from hexadecimal format"},
         'prct': {'method': "perentage",
                  'desc': "sets conversion from percentage format"},
         'help': {'method': "", 'desc': "prints this message"},
         'palette': {'method': "", 'desc': "generates a named palette"},
         'quit': {'method': "", 'desc': "quits the application"}}


def ask_for_color() -> str:
    method = METHOD['current']
    ans = get_input(f"Enter a colour code (R;G;B, {NAMES[method]['method']})"
                    ", command or help")
    color = ""
    try:
        if ans.lower() in COMMANDS:
            return ans
        if ans.lower() in COPYCOMMAND:
            return ans

        r, g, b = map(CONVERSIONS[method], ans.split(";"))
        color = f"#{r:02x}{g:02x}{b:02x}"

        # del_lines("ask_for_color")

    except ValueError as e:
        if ans == "":
            quit()

        cprint(f"{ARED}ERROR: unrecognized value/command {ans!r} - "
               "use 'help' for help{ARST}")
        return ""
    except RangeError as e:
        cprint("ERROR: " + e.args[0])
        STATE['color'] = ""
        STATE['ansi_code'] = ""
    except AttributeError:
        # cprint("…aborting…")
        # cprintd(f"{STATE['del_lines_called'] = }",
        #         location=FTITLE + ".ask_for_color (AttributeInterrupt)")
        sysexit(1)
    except KeyboardInterrupt:
        cprint("…aborting… (KeyboardInterrupt)")
        cprintd(f"{STATE['del_lines_called'] = }",
                location=FTITLE + ".ask_for_color (KeyboardInterrupt)")
        sysexit(1)

    return color


def palette() -> None:
    """ Generate a named (predefined) palette """

    palettes = list_palettes()
    # cprintd(f"{palettes = }", location=f"{APPNAME}::{FTITLE}.palette")
    # palette = get_input("Enter a palette name", choices=palettes)
    # palette = Path(PALETTE_FOLDER) / palette
    for i, palette in enumerate(palettes):
        print(f"{i + 1}. {palette!r} {palettes[palette]}")
    palette_name = get_input("Enter a palette name", choices=palettes)
    log(f"setting STATE['lines_to_del'] to {i + 2}", "palette")
    STATE['lines_to_del'] = i + 3
    log(f"about to delete {STATE['lines_to_del']} lines", "palette")
    del_lines("palette")
    # cprintd(f"{palette_name = }, {palettes[palette_name] = }, "
    #         f"{palettes[palette_name].exists() = }, "
    #         f"{type(palettes[palette_name]) = }",
    #         location=f"{APPNAME}::{FTITLE}.palette")
    batch_conversion(palettes[palette_name], once=False)


def print_colored_line(nr_chars: int = 10,
                       ansi: str = "", hexa: str = "", ending: str = "") -> None:
    """ Print a line with specified color and ansi code """

    ansi = ansi or STATE['ansi_code']
    hexa = STATE['color'] or hexa
    rgb = color_hex_to_rgb(hexa) if hexa else STATE['rgb']
    print(ansi, end="")
    print(" " * nr_chars, ARST, end="")
    # description next to the line:
    STATE['hexa'] = STATE['color']
    print(f" ← {hexa} = {str(rgb):<15} = "
          f"{ansi!r:<25} {ending}")
    STATE['hexa'] = ""
    STATE['color'] = ""


def num_to_ansi() -> None:
    """ Transforms a color (R;G;B) into ansi code """

    # if STATE['ansi_code'] != "" and not recurrent:
    if STATE['ansi_code'] != "" and STATE['new']:
        print_colored_line(20)
        STATE['new'] = False

    # term_del_line(STATE['lines_to_del'])
    color = ask_for_color()

    # if the input was a command:
    if color.lower() in COMMANDS:
        COMMANDS[color.lower()]()
        # print(AYLW, end="")  # !DBG -- turning line into yellow
        # continue
        return

    # if the input was a copy command:
    if color.lower() in COPYCOMMAND:
        copy_color(color)
        sysexit(0)

    del_lines(source="(trying_num_to_ansi)")
    STATE['color'] = color

    try:
        ansi_code, *rgb_ = num_to_bg_ansi(color, with_rgb_dec=True)
        # cprintd(f"{ansi_code = }, {rgb_ = }",
                  # location=FTITLE + "::trying_num_to_ansi")
        STATE['new'] = True
    except Exception as e:
        cprint(f"{ARED}error: {e}{ARST}")
        # continue
        return
    # print_coloured_line(ansi_code, 20)
    STATE['ansi_code'] = ansi_code
    STATE['rgb'] = rgb_[0] if rgb_ else tuple()


def parse_color_value(value: str, fmt: str):
    """Konwertuje wartość koloru zależnie od formatu"""

    # cprintd(f"parsing {value = }, with {fmt = }",
    #         location=f"{APPNAME}::{FTITLE}.parse_color_value")
    if fmt in CONVERSIONS:
        return CONVERSIONS[fmt](value)
    else:
        raise ValueError(f"Unknown format: {fmt}")


def read_colors_file(filename: str) -> List[Dict]:

    colors = []
    # cprintd(f"the file to open: {filename}",
    #         location=f"{APPNAME}::{FTITLE}.read_colors_file")
    filepath = ROOTPATH / filename
    # cprintd(f"the path to open: {filepath}",
    #         location=f"{APPNAME}::{FTITLE}.read_colors_file")
    cnt = 0  # for netto lines nr
    with open(filepath, "r") as fin:
        for line_no, line in enumerate(fin, start=1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(";")
            if len(parts) < 4:
                print(f"Skipping invalid line {line_no}: {line}")
                continue
            r_s, g_s, b_s, fmt = parts[:4]
            try:
                r = parse_color_value(r_s, fmt)
                g = parse_color_value(g_s, fmt)
                b = parse_color_value(b_s, fmt)
                x = f"#{r:02x}{g:02x}{b:02x}"
                # cprintd(f"{line_no = }",
                #         location=f"{APPNAME}::{FTITLE}.read_colors_file")
                cnt += 1
            except (ValueError, RangeError) as e:
                # print(f"Error on line {line_no}: {e} "
                #       f"[{APPNAME}::{FTITLE}.read_colors_file]")
                continue
            colors.append({"r": r, "g": g, "b": b, "x": x, "format": fmt})
    # cprintd(f"{filename = }, net {cnt = }, {len(colors) = }",
    #         location=f"{APPNAME}::{FTITLE}.read_colors_file")
    return colors


def batch_conversion(filename: str | Path | None = None,
                     once: bool = True) -> None:
    """ Generating colors/ANSI codes from a .ssv file """

    filename = filename if filename is not None else\
            STATE['parser'].parse_args().file
    colors = read_colors_file(filename)
    # cprintd(f"{STATE['parser'].parse_args().file = }, {len(colors) = }",
    #         location=f"{APPNAME}::{FTITLE}.batch_conversion")
    # del_lines("batch_conversion")
    colors_nr = len(colors)
    for i, color in enumerate(colors):
        # print(f"{i}. {color = } ({type(color) = })")
        ending = "\u2502"
        if i == 0:
            ending = "↓"  # ↑ 	→ 	↓
        elif i == colors_nr - 1:
            ending = f"↑ ({colors_nr})"
        ansi = num_to_bg_ansi(color["x"])
        print_colored_line(20, ansi, hexa=color["x"], ending=ending)

    if once:
        quit()


def copy_color(fbg: str) -> None:
    """ Copying the bg/fg colour to clipboard """

    if STATE['color'] == "":
        cprint(f"{ARED}no color to copy{ARST}")
        sysexit(0)

    fgbg = "(background)"
    if fbg.lower() == "fg":
        STATE['ansi_code'] = STATE['ansi_code'].replace("[48", "[38", 1)
        fgbg = "(foreground)"
    pyperclip.copy(STATE['ansi_code'])
    cprint(f"copying {STATE['rgb']} = {STATE['hexa']}: {STATE['ansi_code']!r}"
           f" {fgbg}")


def usage(quit: bool = False) -> None:
    print(f"USAGE: python {APPNAME} [-h | --help]")
    print("Input color as 3 hex numbers, separated by semicolon, "
          "when prompted,")
    print("e.g. 'ff;00;00' for red.")
    print("Commands:")
    print(f"    - {'/'.join(COPYCOMMAND)} to copy the current "
          "color to the clipboard \n      (ANSI foreground/background, "
          "respectively).")
    for key, value in NAMES.items():
        print(f"    - {key}: {value['desc']}")
    sysexit(0) if quit else None
    STATE['after_help'] = True


def log(message: str, source: str = "main") -> None:
    t = datetime.now().strftime("%H:%M:%S")
    STATE['log'].append(f"{message} -- {source}@{t}")



def main() -> int:
    loc = f"{APPNAME}::cli.main"

    parser = argparse.ArgumentParser(
        prog=APPNAME,
        description="Terminal color picker",
        epilog=f"version: {VERSION}",
        add_help=False,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
                        "-f", "--file",
                        metavar="FILE",
                        type=str,
                        help="file to process in batch mode"
                        )
    parser.add_argument("-v", "--version", action="store_true",
                        help="prints application version")
    parser.add_argument("-h", "--help", action="store_true",
                        help="prints help message")
    STATE['parser'] = parser

    args = parser.parse_args()

    mode = f" -- batch mode: {args.file!r}" if args.file\
            else " -- interactive mode"
    if args.help:
        parser.print_help()
        usage(quit=True)
    if args.version:
        print(f"{APPNAME} v. {VERSION}")
        sysexit(0)
    print(f"{APPNAME} v. {VERSION}{mode}")
    if args.file:
        batch_conversion()

    # comemented:
    # if "-h" in argv or "--help" in argv:
    #     usage(quit=True)

    # if "-b" in argv or "--batch" in argv:
    #     batch_conversion()

    # cprintd("debug message try…", location=loc)
    #
    # print()
    # cprintd("Trying num_to_bg_ansi…", location=loc)
    # clolor = "#FF0000"
    # code = num_to_fg_ansi(clolor)
    # print(f"{clolor} → {code}{code!r}{ARST}")
    #
    # print()
    # cprintd("Trying get_input…", location=loc)
    # ans = get_input("get_input test ")
    # cprint(f"{ans = }")
    #
    # print()
    # cprintd("Trying ask_for_color…", location=loc)
    # ans = ask_for_color()
    # cprint(f"{ans = }")
    #
    # print()
    # cprintd("Trying num_to_ansi…", location=loc)
    # num_to_ansi()

    # main loop:
    while True:
        num_to_ansi()

    return 0
