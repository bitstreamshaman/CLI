"""This module provides the implementation for the retrieving completion results
from bash.

A Special thanks to the xonsh team for their work on the
xonsh shell from which i took this code, go check them out at: https://github.com/xonsh/xonsh.git
"""

# developer note: this file should not perform any action on import.
# This is to allow users who want to use this completionDon't worry, take your time. It was just a way for us to have anything defined more clearly. Tell us what you think and if you want we can have a call to discuss it! file as a standalone CLI tool.
import typing as tp
import functools
import os
import pathlib
import platform
import re
import shlex
import shutil
import subprocess
import sys


__version__ = "0.2.8"

_BASH_COMPLETIONS_PATHS_DEFAULT: tuple[str, ...] = ()
_BASH_PATTERN_NEED_QUOTES: tp.Optional[tp.Pattern] = None
BASH_COMPLETE_SCRIPT = r"""
{source}

# Override some functions in bash-completion, do not quote for readline
quote_readline()
{{
    echo "$1"
}}

_quote_readline_by_ref()
{{
    if [[ $1 == \'* || $1 == \"* ]]; then
        # Leave out first character
        printf -v $2 %s "${{1:1}}"
    else
        printf -v $2 %s "$1"
    fi

    [[ ${{!2}} == \$* ]] && eval $2=${{!2}}
}}


function _get_complete_statement {{
    complete -p {cmd} 2> /dev/null || echo "-F _minimal"
}}

function getarg {{
    find=$1
    shift 1
    prev=""
    for i in $* ; do
        if [ "$prev" = "$find" ] ; then
            echo $i
        fi
        prev=$i
    done
}}

_complete_stmt=$(_get_complete_statement)
if echo "$_complete_stmt" | grep --quiet -e "_minimal"
then
    declare -f _completion_loader > /dev/null && _completion_loader {cmd}
    _complete_stmt=$(_get_complete_statement)
fi

# Is -C (subshell) or -F (function) completion used?
if [[ $_complete_stmt =~ "-C" ]] ; then
    _func=$(eval getarg "-C" $_complete_stmt)
else
    _func=$(eval getarg "-F" $_complete_stmt)
    declare -f "$_func" > /dev/null || exit 1
fi

echo "$_complete_stmt"
export COMP_WORDS=({line})
export COMP_LINE={comp_line}
export COMP_POINT=${{#COMP_LINE}}
export COMP_COUNT={end}
export COMP_CWORD={n}
$_func {cmd} {prefix} {prev}

# print out completions, right-stripped if they contain no internal spaces
shopt -s extglob
for ((i=0;i<${{#COMPREPLY[*]}};i++))
do
    no_spaces="${{COMPREPLY[i]//[[:space:]]}}"
    no_trailing_spaces="${{COMPREPLY[i]%%+([[:space:]])}}"
    if [[ "$no_spaces" == "$no_trailing_spaces" ]]; then
        echo "$no_trailing_spaces"
    else
        echo "${{COMPREPLY[i]}}"
    fi
done
"""


@functools.lru_cache(1)
def _git_for_windows_path():
    """Returns the path to git for windows, if available and None otherwise."""
    import winreg

    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, "SOFTWARE\\GitForWindows")
        gfwp, _ = winreg.QueryValueEx(key, "InstallPath")
    except FileNotFoundError:
        gfwp = None
    return gfwp


@functools.lru_cache(1)
def _windows_bash_command(env=None):
    """Determines the command for Bash on windows."""
    wbc = "bash"
    path = None if env is None else env.get("PATH", None)
    bash_on_path = shutil.which("bash", path=path)
    if bash_on_path:
        try:
            out = subprocess.check_output(
                [bash_on_path, "--version"],
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        except subprocess.CalledProcessError:
            bash_works = False
        else:
            # Check if Bash is from the "Windows Subsystem for Linux" (WSL)
            # which can't be used by xonsh foreign-shell/completer
            bash_works = out and "pc-linux-gnu" not in out.splitlines()[0]

        if bash_works:
            wbc = bash_on_path
        else:
            gfwp = _git_for_windows_path()
            if gfwp:
                bashcmd = os.path.join(gfwp, "bin\\bash.exe")
                if os.path.isfile(bashcmd):
                    wbc = bashcmd
    return wbc


def _bash_command(env=None):
    """Determines the command for Bash on the current plaform."""
    if platform.system() == "Windows":
        bc = _windows_bash_command(env=None)
    else:
        bc = "bash"
    return bc


def _bash_completion_paths_default():
    """A possibly empty tuple with default paths to Bash completions known for
    the current platform.
    """
    platform_sys = platform.system()
    if platform_sys == "Linux" or sys.platform == "cygwin":
        bcd = ("/usr/share/bash-completion/bash_completion",)
    elif platform_sys == "Darwin":
        bcd = (
            "/usr/local/share/bash-completion/bash_completion",  # v2.x
            "/usr/local/etc/bash_completion",
        )  # v1.x
    elif platform_sys == "Windows":
        gfwp = _git_for_windows_path()
        if gfwp:
            bcd = (
                os.path.join(gfwp, "usr\\share\\bash-completion\\bash_completion"),
                os.path.join(
                    gfwp, "mingw64\\share\\git\\completion\\git-completion.bash"
                ),
            )
        else:
            bcd = ()
    else:
        bcd = ()
    return bcd


def _get_bash_completions_source(paths=None):
    global _BASH_COMPLETIONS_PATHS_DEFAULT
    if paths is None:
        if not _BASH_COMPLETIONS_PATHS_DEFAULT:
            _BASH_COMPLETIONS_PATHS_DEFAULT = _bash_completion_paths_default()
        paths = _BASH_COMPLETIONS_PATHS_DEFAULT
    for path in map(pathlib.Path, paths):
        if path.is_file():
            return f'source "{path.as_posix()}"'
    return None


def _bash_get_sep():
    """Returns the appropriate filepath separator char depending on OS and
    xonsh options set
    """
    if platform.system() == "Windows":
        return os.altsep
    else:
        return os.sep


def _bash_pattern_need_quotes():
    global _BASH_PATTERN_NEED_QUOTES
    if _BASH_PATTERN_NEED_QUOTES is not None:
        return _BASH_PATTERN_NEED_QUOTES
    pattern = r'\s`\$\{\}\,\*\(\)"\'\?&'
    if platform.system() == "Windows":
        pattern += "%"
    pattern = "[" + pattern + "]" + r"|\band\b|\bor\b"
    _BASH_PATTERN_NEED_QUOTES = re.compile(pattern)
    return _BASH_PATTERN_NEED_QUOTES


def _bash_expand_path(s):
    """Takes a string path and expands ~ to home and environment vars."""
    # expand ~ according to Bash unquoted rules "Each variable assignment is
    # checked for unquoted tilde-prefixes immediately following a ':' or the
    # first '='". See the following for more details.
    # https://www.gnu.org/software/bash/manual/html_node/Tilde-Expansion.html
    pre, char, post = s.partition("=")
    if char:
        s = os.path.expanduser(pre) + char
        s += os.pathsep.join(map(os.path.expanduser, post.split(os.pathsep)))
    else:
        s = os.path.expanduser(s)
    return s


def _bash_quote_to_use(x):
    single = "'"
    double = '"'
    if single in x and double not in x:
        return double
    else:
        return single


def _bash_quote_paths(paths, start, end):
    out = set()
    space = " "
    backslash = "\\"
    double_backslash = "\\\\"
    slash = _bash_get_sep()
    orig_start = start
    orig_end = end
    # quote on all or none, to make readline completes to max prefix
    need_quotes = any(
        re.search(_bash_pattern_need_quotes(), x)
        or (backslash in x and slash != backslash)
        for x in paths
    )

    for s in paths:
        start = orig_start
        end = orig_end
        if start == "" and need_quotes:
            start = end = _bash_quote_to_use(s)
        if os.path.isdir(_bash_expand_path(s)):
            _tail = slash
        elif end == "" and not s.endswith("="):
            _tail = space
        else:
            _tail = ""
        if start != "" and "r" not in start and backslash in s:
            start = f"r{start}"
        s = s + _tail
        if end != "":
            if "r" not in start.lower():
                s = s.replace(backslash, double_backslash)
            if s.endswith(backslash) and not s.endswith(double_backslash):
                s += backslash
        if end in s:
            s = s.replace(end, "".join(f"\\{i}" for i in end))
        out.add(start + s + end)
    return out, need_quotes


def bash_completions(
    prefix,
    line,
    begidx,
    endidx,
    env=None,
    paths=None,
    command=None,
    quote_paths=_bash_quote_paths,
    line_args=None,
    opening_quote="",
    closing_quote="",
    arg_index=None,
    **kwargs,
):
    """Completes based on results from BASH completion - FIXED VERSION"""
    source = _get_bash_completions_source(paths) or ""

    if prefix.startswith("$"):  # do not complete env variables
        return set(), 0

    splt = line_args or line.split()
    cmd = splt[0]
    cmd = os.path.basename(cmd)
    prev = ""
    if arg_index is not None:
        n = arg_index
        if arg_index > 0:
            prev = splt[arg_index - 1]
    else:
        # find `n` and `prev` by ourselves
        idx = n = 0
        for n, tok in enumerate(splt):  # noqa
            if tok == prefix:
                idx = line.find(prefix, idx)
                if idx >= begidx:
                    break
            prev = tok
        if len(prefix) == 0:
            n += 1
    prefix_quoted = shlex.quote(prefix)

    script = BASH_COMPLETE_SCRIPT.format(
        source=source,
        line=" ".join(shlex.quote(p) for p in splt if p),
        comp_line=shlex.quote(line),
        n=n,
        cmd=shlex.quote(cmd),
        end=endidx + 1,
        prefix=prefix_quoted,
        prev=shlex.quote(prev),
    )

    if command is None:
        command = _bash_command(env=env)
    try:
        out = subprocess.check_output(
            [command, "-c", script],
            universal_newlines=True,
            stderr=subprocess.PIPE,
            env=env,
        )
        out = [line for line in out.splitlines() if line.strip()]
        if not out:
            raise ValueError
    except (
        subprocess.CalledProcessError,
        FileNotFoundError,
        UnicodeDecodeError,
        ValueError,
    ):
        return set(), 0

    complete_stmt = out[0]
    out = set(out[1:])

    # Handle empty prefix specially - mimic native bash behavior
    if not prefix:
        # Find the longest common prefix among all completions
        if out:
            # Convert to list for commonprefix
            out_list = list(out)
            commprefix = os.path.commonprefix(out_list)

            # If there's a meaningful common prefix, return just that
            if commprefix and len(commprefix) > 0:
                # Check if all completions start with the same prefix
                if all(completion.startswith(commprefix) for completion in out):
                    # For cases like hostname where all options start with '--'
                    # Return the common prefix so bash can complete it
                    if commprefix.startswith("--"):
                        return {commprefix}, 0
                    elif commprefix.startswith("-"):
                        # If common prefix is just '-', let bash complete step by step
                        return {"-"}, 0

        # If no meaningful common prefix, fall through to normal processing

    # Normal processing for non-empty prefixes
    commprefix = os.path.commonprefix(list(out)) if out else ""

    if prefix.startswith("~") and commprefix and prefix not in commprefix:
        home_ = os.path.expanduser("~")
        out = {f"~/{os.path.relpath(p, home_)}" for p in out}
        commprefix = f"~/{os.path.relpath(commprefix, home_)}"

    # Calculate strip length more carefully
    strip_len = 0
    strip_prefix = prefix.strip("\"'")

    # Handle the case where prefix is shorter than common prefix
    min_len = min(len(strip_prefix), len(commprefix))

    # Find where the prefix diverges from the common prefix
    for i in range(min_len):
        if commprefix[i] != strip_prefix[i]:
            strip_len = i
            break
    else:
        # If we went through the whole loop, the prefix matches the common prefix
        strip_len = min_len

    if "-o noquote" not in complete_stmt:
        out, need_quotes = quote_paths(out, opening_quote, closing_quote)
    if "-o nospace" in complete_stmt:
        out = {x.rstrip() for x in out}

    # Handle special cases for arguments with separators
    if "=" in prefix and "=" not in commprefix:
        strip_len = prefix.index("=") + 1
    elif ":" in prefix and ":" not in commprefix:
        strip_len = prefix.index(":") + 1

    return out, max(len(prefix) - strip_len, 0)


def bash_complete_line(line, return_line=True, **kwargs):
    """Provides the completion from the end of the line.

    Parameters
    ----------
    line : str
        Line to complete
    return_line : bool, optional
        If true (default), will return the entire line, with the completion added.
        If false, this will instead return the strings to append to the original line.
    kwargs : optional
        All other keyword arguments are passed to the bash_completions() function.

    Returns
    -------
    rtn : set of str
        Possible completions of prefix
    """
    # set up for completing from the end of the line
    split = line.split()
    if len(split) > 1 and not line.endswith(" "):
        prefix = split[-1]
        begidx = len(line.rsplit(prefix)[0])
    else:
        prefix = ""
        begidx = len(line)
    endidx = len(line)
    # get completions
    out, lprefix = bash_completions(prefix, line, begidx, endidx, **kwargs)
    # reformat output
    if return_line:
        preline = line[:-lprefix]
        rtn = {preline + o for o in out}
    else:
        rtn = {o[lprefix:] for o in out}
    return rtn


