rtyaml: Round-trippable YAML
============================

Primary author: Joshua Tauberer

https://github.com/unitedstates/rtyaml

This module provides wrappers around ``pyyaml`` to set sane defaults:

* field order in dicts is preserved when writing out objects that were read in by this library
* saner output defaults are set
* any comment block found at the very beginning of the file when loading YAML is preserved when writing it back out

Usage::

   import rtyaml
   stuff = rtyaml.load(open("myfile.yaml"))
   # ...do things to stuf...
   rtyaml.dump(stuff, open("myfile.yaml", "w"))

As in the underlying pyyaml library, ``load`` accepts a byte string containing YAML, a Unicode string containing YAML, an open binary file object, or an open text file object. Also, the second argument to ``dump`` is optional and if omitted the function returns the YAML in a string.

Dependencies
-------------

* pyyaml (in Ubuntu, the python-yaml package)
* libyaml (in Ubuntu, the libyaml-0-2 package)

This package works in both Python 2 and 3.

Details
-------

This library does the following:

* Uses the native libyaml CSafeLoader and CDumper for both speed and trustable operations.
* Parses mappings as OrderedDicts so that the field order remains the same when dumping the file later.
* Writes unicode strings without any weird YAML tag. They just appear as strings. Output is UTF-8 encoded, and non-ASCII characters appear as Unicode without escaping.
* Writes mappings and lists in the expanded (one per line) format, which is nice when the output is going in version control.
* Modifies the string quote rules so that any string made up of digits is serialized with quotes. (The defaults will omit quotes for octal-ish strings like "09" that are invalid octal notation.)
* Serializes null values as the tilde, since "null" might be confused for a string-typed value.
* If a block comment appears at the start of the file (i.e. one or more lines starting with a '#', write back out the commend if the same object is written with rtyaml.dump().)

Public domain dedication
------------------------

This project is dedicated to the public domain, as indicated in the LICENSE file:

	The project is in the public domain within the United States, and copyright and related rights in the work worldwide are waived through the CC0 1.0 Universal public domain dedication. http://creativecommons.org/publicdomain/zero/1.0/

All contributions to this project must be released under the CC0 dedication. By submitting a pull request, you are agreeing to comply with this waiver of copyright interest.
