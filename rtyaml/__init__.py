import sys, re, io
from collections import OrderedDict

import yaml
try:
    # Use the native code backends, if available.	
    from yaml import CSafeLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import SafeLoader as Loader, Dumper

# In order to preserve the order of attributes, YAML must be
# hooked to load mappings as OrderedDicts. Adapted from:
# https://gist.github.com/317164

def construct_odict(load, node):
    omap = OrderedDict()
    yield omap
    if not isinstance(node, yaml.MappingNode):
        raise yaml.constructor.ConstructorError(
            "while constructing an ordered map",
            node.start_mark,
            "expected a map, but found %s" % node.id, node.start_mark
        )
    for key, value in node.value:
        key = load.construct_object(key)
        value = load.construct_object(value)
        omap[key] = value

Loader.add_constructor(u'tag:yaml.org,2002:map', construct_odict)
def ordered_dict_serializer(self, data):
    return self.represent_mapping('tag:yaml.org,2002:map', data.items())
Dumper.add_representer(OrderedDict, ordered_dict_serializer)

# Likewise, when we store unicode objects make sure we don't write
# them with weird YAML tags indicating the Python data type. str-typed
# strings come out fine, but unicode strings come out with unnecessary
# type tags in Python 2. The easy solution is this:
#
#   Dumper.add_representer(unicode, lambda dumper, value:
#        dumper.represent_scalar(u'tag:yaml.org,2002:str', value))
#
# However, the standard PyYAML representer for strings does something
# weird: if a value cannot be parsed as an integer quotes are omitted.
#
# This is incredibly odd when the value is an integer with a leading
# zero. These values are typically parsed as octal integers, meaning
# quotes would normally be required (that's good). But when the value
# has an '8' or '9' in it, this would make it an invalid octal number
# and so quotes would no longer be required (that's confusing).
# We will override str and unicode output to choose the quotation
# style with our own logic. (According to PyYAML, style can be one of
# the empty string, ', ", |, or >, or None to, presumably, choose
# automatically and use no quoting where possible.
def our_string_representer(dumper, value):
	# let PyYAML choose by default, using no quoting where possible
	style = None

	# If it looks like an octal number, force '-quote style.
	if re.match(r"^0\d*$", value): style = "'"

	# If it has newlines, request a block style.
	if "\n" in value:
		# If the average length of a line is very long, then use the folded
		# style so that in our output the lines get folded. The drawback when
		# this is used on shortlines is that newlines get doubled. So when
		# the lines are short, use the literal block style.
		lines = value.split("\n")
		avg_line_length = sum(len(line) for line in lines) / float(len(lines))
		if avg_line_length > 70:
			style = ">" # folded
		else:
			style = "|"

	return dumper.represent_scalar(u'tag:yaml.org,2002:str', value, style=style)

if sys.version < '3':
    # python 2 'str' and 'unicode'
    Dumper.add_representer(str, our_string_representer)
    Dumper.add_representer(unicode, our_string_representer)
else:
    # python 3 'str' only -- bytes should only hold binary data
    # and be serialized as such.
    Dumper.add_representer(str, our_string_representer)

# Add a representer for nulls too. YAML accepts "~" for None, but the
# default output converts that to "null". Override to always use "~".
Dumper.add_representer(type(None), lambda dumper, value : \
	dumper.represent_scalar(u'tag:yaml.org,2002:null', u"~"))

# Use a subclss of list when trying to hold onto a block comment at the
# start of a stream. Make sure it serializes back to a plain YAML list.
class RtYamlList(list):
    pass
def RtYamlList_serializer(self, data):
    return self.represent_sequence('tag:yaml.org,2002:seq', data)
Dumper.add_representer(RtYamlList, RtYamlList_serializer)

# Provide some wrapper methods that apply typical settings.

def load(stream):
    # Read any comment block at the start. We can only do this if we can
    # seek the stream so we can simulate a peek(). Peek isn't provided
    # on the io.TextIOWrapper so we can't use it on text streams.
    initial_comment_block = ""
    if sys.version < '3' and isinstance(stream, file):
        stream = io.open(stream.fileno(), mode="rb", closefd=False)
    if hasattr(stream, "seek") and hasattr(stream, "tell") and hasattr(stream, "readline"):
        while True:
            p = stream.tell()
            line = stream.readline()
            if line[0] != "#":
                stream.seek(p)
                break
            initial_comment_block += line

    # Read the object from the stream.
    obj = yaml.load(stream, Loader=Loader)

    # Attach our initial comment to the object so we can save it later (assuming
    # this object is written back out).
    if initial_comment_block:
        if isinstance(obj, list):
            # The list class can't be assigned any custom attributes, but we can make a subclass that can.
            # Clone the list object into a RtYamlList instance.
            obj = RtYamlList(obj)
        obj.__initial_comment_block = initial_comment_block

    return obj

def dump(data, stream=None):
    # If we pulled in an initial comment block when reading the stream, write
    # it back out at the start of the stream.
    if hasattr(data, '__initial_comment_block'):
        stream.write(data.__initial_comment_block)

    # Write the object to the stream.
    return yaml.dump(data, stream, default_flow_style=False, allow_unicode=True, Dumper=Dumper)

def pprint(data):
    yaml.dump(data, sys.stdout, default_flow_style=False, allow_unicode=True)

