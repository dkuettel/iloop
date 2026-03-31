from __future__ import annotations

import os
import shlex
import subprocess
import sys
import termios
import tty
from pathlib import Path

import typer


def get_choice() -> str:
    fd = sys.stdin.fileno()
    settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        return sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, settings)


app = typer.Typer(
    no_args_is_help=True,
    pretty_exceptions_enable=False,
    rich_markup_mode=None,
    add_completion=True,
)


@app.command()
def until(
    args: list[str],
    debug_python: bool = False,
    ld: None | str = None,
    errorfile: None | Path = None,
):
    _run(args, True, debug_python, ld, errorfile)


@app.command()
def repeat(
    args: list[str],
    debug_python: bool = False,
    ld: None | str = None,
    errorfile: None | Path = None,
):
    _run(args, False, debug_python, ld, errorfile)


@app.command()
def run(
    args: list[str],
    until: bool = False,
    debug_python: bool = False,
    ld: None | str = None,
    errorfile: None | Path = None,
):
    _run(args, until, debug_python, ld, errorfile)


def _run(
    args: list[str],
    until: bool = False,
    debug_python: bool = False,
    ld: None | str = None,
    errorfile: None | Path = None,
):
    if debug_python:
        env = {**os.environ, "PYTHONBREAKPOINT": "IPython.embed"}
    else:
        env = dict(os.environ)

    env.pop("VIRTUAL_ENV", None)

    if ld is not None:
        env["LD_LIBRARY_PATH"] = ld

    if until:
        mode = "until"
    else:
        mode = "repeat"

    while True:
        subprocess.run(["clear"], check=True)

        print(mode, ">", " ".join(shlex.quote(arg) for arg in args))
        print()
        try:
            result = subprocess.run(args, env=env)
        except KeyboardInterrupt:
            result = None
        print()

        print(mode, ">", " ".join(shlex.quote(arg) for arg in args))
        if result is None:
            print("Interrupted, repeat?", end="", flush=True)
        else:
            if result.returncode == 0:
                if until:
                    return
                print("Success, repeat?", end="", flush=True)
            else:
                print(f"Failed with {result.returncode}, repeat?", end="", flush=True)

        while True:
            match get_choice():
                case "y" | "t" | "\r" | "r":
                    break
                case "n" | "q" | "\x1b":
                    return
                case "e":  # write an error file and exit
                    if errorfile is not None:
                        subprocess.run(
                            [
                                "tmux",
                                "capture-pane",
                                "-b",
                                "error",
                                "-J",
                                "-S",
                                "-",
                                "-E",
                                "-",
                            ],
                            check=True,
                        )
                        subprocess.run(
                            [
                                "tmux",
                                "save-buffer",
                                "-b",
                                "error",
                                str(errorfile),
                            ],
                            check=True,
                        )
                        return
                case _:
                    pass
