#!/bin/env python3
#
# Copyright (c) 2020 Jim Ramsay <i.am@jimramsay.com>
# Copyright (c) 2020 Hans Ulrich Niedermann <hun@n-dimensional.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


"""\
contrib-to-about.py - convert CONTRIBUTORS.md to python module

Usage:
   path/to/contrib-to-about.py

This reads `../CONTRIBUTORS.md` and writes a new python module
`../soundcraft/contributors.py` if necessary and requested. The file
locations are determined relative to the location of
`contrib-to-about.py`.

Options:
    --check
        Only check whether the file would change; never actually change it.
        The exit code will be non-0 if the file would be changed.
    --diff
        Only show the changes which would be done to the python module as
        a `diff -u` patch; never actually change it.
        The exit code will be non-0 if the file would be changed.
    --help
        Show this message and exit.

The --check and --diff options mimick the behaviour of the `black`
source code formatting tool.
"""


import hashlib
import os
import re
import subprocess
import sys


# parse command line (--check and --diff just like the `black` command)
args = sys.argv[1:]
flag_check = False
flag_diff = False
for arg in args:
    if arg == "--check":
        flag_check = True
    elif arg == "--diff":
        flag_diff = True
    elif arg == "--help":
        sys.stdout.write(__doc__)
        sys.exit(0)
    else:
        raise ValueError("Invalid command line argument")


author_format = re.compile(
    r"^- \[(?P<name>[^]]+)]\(mailto:(?P<email>[^)]+)\)(?P<description>.*)"
)
link_format = re.compile(r"\[(?P<name>[^]]+)]\((?P<url>[^)]+)\)")


# Change to the top of the source tree before reading or writing any
# files, so that we always read and write files in the correct place.
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parseMarkdown(line):
    author_match = author_format.match(line)
    if author_match is not None:
        author = author_match.groupdict()
        return f"{author['name']} <{author['email']}>{author['description']}"
    link_match = link_format.search(line)
    if link_match is not None:
        link = link_match.groupdict()
        return f"{link['name']} {link['url']}"
    return line.lstrip("- ")


contributors = {}
section = None
with open("CONTRIBUTORS.md") as contrib:
    for line in contrib:
        line = line.rstrip("\n")
        if line.startswith("- "):
            contributors[section].append(parseMarkdown(line))
        elif line.startswith("--") or len(line) == 0:
            next
        else:
            section = line
            contributors[section] = []


# print(f"authors={contributors['Contributors']}")
# print(f"artists={contributors['Artwork']}")


def write_people(file, people_group, people_list):
    if len(people_list) == 0:
        file.write(f"{people_group} = []\n")
    elif len(people_list) == 1:
        person = people_list[0]
        file.write(f'{people_group} = ["{person}"]\n')
    else:
        file.write(f"{people_group} = [\n")
        for person in people_list:
            file.write(f'    "{person}",\n')
        file.write(f"]\n")


target_fname = "soundcraft/contributors.py"
new_fname = f"{target_fname}.new"
with open(new_fname, "w") as dst:
    tool_filebase = os.path.basename(__file__)
    dst.write(
        f'''\
"""\\
{target_fname} - autogenerated from CONTRIBUTORS.md

DO NOT EDIT THIS FILE. EDIT `CONTRIBUTORS.md` INSTEAD
and update this file by re-running {tool_filebase}.
"""

'''
    )
    write_people(dst, "authors", contributors["Contributors"])
    write_people(dst, "artists", contributors["Artwork"])


def file_hash(filename):
    try:
        with open(filename, "rb") as file:
            m = hashlib.sha256()
            m.update(file.read())
            d = m.digest()
            return d
    except FileNotFoundError:
        # This return string differs from all hash digests, and also
        # differs for different filenames.
        return "file not found ({filename})"


hash_new = file_hash(new_fname)
hash_target = file_hash(target_fname)

if hash_new == hash_target:
    print(f"Not updating {target_fname} (no changes)")
    os.unlink(new_fname)
    sys.exit(0)
else:
    if flag_diff:
        subprocess.run(["diff", "-u", target_fname, new_fname], check=False)
        os.unlink(new_fname)
        sys.exit(1)
    if flag_check:
        print(f"File {target_fname} would be updated from {new_fname}.")
        os.unlink(new_fname)
        sys.exit(1)
    else:
        print(f"Update {target_fname} from {new_fname} (changes detected)")
        os.rename(new_fname, target_fname)
        sys.exit(0)
