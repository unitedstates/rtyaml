rtyaml: Round-trippable YAML
============================

Primary author: Joshua Tauberer <https://razor.occams.info>

-   GitHub: <https://github.com/unitedstates/rtyaml>
-   PyPi: <https://pypi.python.org/pypi/rtyaml>

This module provides wrappers around `pyyaml` to set sane defaults:

-   round-tripping YAML files is possible by preserving field order
-   saner output defaults are set for strings
-   a comment block found at the very beginning of a stream when loading YAML is preserved when writing it back out

Install:

    pip install rtyaml
    (or pip3 --- this module works in both Python 2 and Python 3)

Usage:

    import rtyaml
    stuff = rtyaml.load(open("myfile.yaml"))
    # ...do things to stuf...
    rtyaml.dump(stuff, open("myfile.yaml", "w"))

As in the underlying pyyaml library, `load` accepts a byte string containing YAML, a Unicode string containing YAML, an open binary file object, or an open text file object. Also, the second argument to `dump` is optional and if omitted the function returns the YAML in a string.

`load_all` and `dump_all` are also supported, which load and save lists of documents using YAML's `---` document separator.

Dependencies
------------

-   pyyaml (in Ubuntu, the `python-yaml` or `python3-yaml` package)
-   libyaml (in Ubuntu, the `libyaml-0-2` package plus, at install time only, `libyaml-dev`)

Details
-------

This library does the following:

-   Uses the native libyaml CSafeLoader and CDumper for both speed and trustable operations.
-   Parses mappings as OrderedDicts so that the field order remains the same when dumping the file later.
-   Writes unicode strings without any weird YAML tag. They just appear as strings. Output is UTF-8 encoded, and non-ASCII characters appear as Unicode without escaping.
-   Writes multi-line strings in block mode rather than quoted with embedded "n"'s, choosing between the literal or folded mode depending on what looks better for the length of the lines in the string.
-   Writes mappings and lists in the expanded (one per line) format, which is nice when the output is going in version control.
-   Modifies the string quote rules so that any string made up of digits is serialized with quotes. (The default settings serialize the string "01" with quotes but the string "09" without quotes! (Can you figure out why?))
-   Serializes null values as the tilde rather than as "null" (without quotes), which I think is less confusing.
-   If a block comment appears at the start of the file (i.e. one or more lines starting with a '\#'), write it back out if the same object is written with rtyaml.dump().

With-Block Helper for Editing Files In-Place
--------------------------------------------

The rtyaml.edit class is a utility class that can be used with with blocks that makes it easier to edit YAML files in-place. For example:

> with rtyaml.edit("path/to/data.yaml", default={}) as data:  
> data\["hello"\] = "world"
>
The file is opened for editing ("r+" mode, or "w+" mode if it doesn't exist and a default value is given) and its contents is parsed and returned as the data with-block variable. The file is kept open while the with-block is executing. When the with-block exits, the with-block variable is written back to the file as YAML, and then the file is closed.

This will, of course, only work if the file contains an array or object (dict), and you cannot assign a new value to the with-block variable (that's just how Python with blocks work). You can only call its methods, i.e., you can edit the list (append, pop, sort, etc.) and dict (get/set keys), but you can't replace the value with an entirely new list or dict.

If the default parameter is not given, or is None, the file must exist. Otherwise, if the file doesn't exist, it's created and the with-block variable will start you off with the default value.

You can also pass a stream as the first argument if you want to open the file yourself. The stream must support seek, truncate, and close. If you open a file, you should use the "r+" or "w+" mode.

Public domain dedication
------------------------

This project is dedicated to the public domain, as indicated in the LICENSE file:

> The project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the CC0 1.0 Universal public domain dedication. <http://creativecommons.org/publicdomain/zero/1.0/>

All contributions to this project must be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
