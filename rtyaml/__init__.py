import sys, re, io

# Import YAML's SafeLoader.
import yaml
try:
    # Use the native code backends, if available.   
    from yaml import CSafeLoader as Loader, CDumper as Dumper
except ImportError:
    from yaml import SafeLoader as Loader, Dumper

# Before Python 3.7 when dicts began to preserver the insertion
# order of elements, in order to preserve the order of mappings,
# YAML must be hooked to load mappings as OrderedDicts. Adapted from:
# https://gist.github.com/317164
from collections import OrderedDict
if sys.version_info < (3,7):
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

else:
    # Starting with Pyhon 3.7, dicts preserve order. But PyYAML by default
    # sorts the keys of any mapping it gets when that mapping has an 'items'
    # attribute. We override that by adding an explicit representer for 'dict'
    # that passes the items directly (so that the value it seems does not have
    # an 'items' attribute itself). See https://github.com/yaml/pyyaml/blob/e471e86bf6dabdad45a1438c20a4a5c033eb9034/lib/yaml/representer.py#L119.
    # See below for similar code for OrderedDicts.
    Dumper.add_representer(dict, lambda self, data: self.represent_mapping('tag:yaml.org,2002:map', data.items()))

# Tell YAML to serialize OrderedDicts as mappings. Prior to Python 3.7, this
# was the data type that must be used to specify key order, and, per the block
# above, we would deserialize to OrderedDicts. In Python >=3.7, we don't deserialize
# to OrderedDicts anymore but we still allow OrderedDicts to be used in data passed
# to dump. See the block above for why we also add an explicit serializer for dicts.
def ordered_dict_serializer(self, data):
    return self.represent_mapping('tag:yaml.org,2002:map', data.items())
Dumper.add_representer(OrderedDict, ordered_dict_serializer)

# The standard PyYAML representer for strings does something weird:
# If a value cannot be parsed as another data type, quotes are omitted.
#
# This is incredibly odd when the value is integer-like with a leading
# zero. These values are typically parsed as octal integers, meaning
# quotes would normally be required (that's good). But when the value
# has an '8' or '9' in it, this would make it an invalid octal number
# and so quotes would no longer be required (that's confusing).
# We will override str and unicode output to choose the quotation
# style with our own logic. (According to PyYAML, style can be one of
# the empty string, ', ", |, or >, or None to, presumably, choose
# automatically and use no quoting where possible.)
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
    # In Python 2, 'str' and 'unicode' both should serialize to YAML strings.
    # Unicode strings come out with unnecessary type tags in Python 2. The easy
    # solution is this:
    #   Dumper.add_representer(unicode, lambda dumper, value:
    #        dumper.represent_scalar(u'tag:yaml.org,2002:str', value))
    # but because we are also overriding string behavior, we use our own representer.
    Dumper.add_representer(str, our_string_representer)
    Dumper.add_representer(unicode, our_string_representer)
else:
    # In Python 3, only 'str' are strings. 'bytes' should only hold binary data
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
    return do_load(stream, yaml.load)

def load_all(stream):
    return do_load(stream, yaml.load_all)

def do_load(stream, load_func):
    # Read any comment block at the start.
    initial_comment_block = ""

    # We can only read a comment block if we can seek the stream so we can simulate
    # a peek() so we can test for a comment block without consuming the data. Seek
    # isn't provided on the Python 2 io.TextIOWrapper so we can't use it on text streams.
    if sys.version < '3' and isinstance(stream, file):
        stream = io.open(stream.fileno(), mode="rb", closefd=False)

    # Try reading the stream until the first non-comment line, then seek back to the
    # start of that line.
    try:
        while True:
            p = stream.tell()
            line = stream.readline()
            if line[0] != "#":
                stream.seek(p)
                break
            initial_comment_block += line
    except (AttributeError, io.UnsupportedOperation) as e:
        # seek, tell, and readline may not be present and will raise an AttributeError
        # or seek/tell may raise io.UnsupportedOperation.
        pass

    # Read the object from the stream.
    obj = load_func(stream, Loader=Loader)

    # Attach our initial comment to the object so we can save it later (assuming
    # this object is written back out).
    if initial_comment_block:
        if isinstance(obj, list):
            # The list class can't be assigned any custom attributes, but we can make a subclass that can.
            # Clone the list object into a RtYamlList instance.
            obj = RtYamlList(obj)
        if isinstance(obj, dict):
            # The dict class can't be assigned any custom attributes, so we'll use an OrderedDict instead, which can.
            obj = OrderedDict(obj)
        obj.__initial_comment_block = initial_comment_block

    return obj

def dump(data, stream=None):
    return do_dump(data, stream, yaml.dump)

def dump_all(data, stream=None):
    return do_dump(data, stream, yaml.dump_all)

def do_dump(data, stream, dump_func):
    # If we pulled in an initial comment block when reading the stream, write
    # it back out at the start of the stream. If we're dumping to a string,
    # then stream is none.
    if hasattr(data, '__initial_comment_block') and stream is not None:
        stream.write(data.__initial_comment_block)

    # Write the object to the stream.
    ret = dump_func(data, stream, default_flow_style=False, allow_unicode=True, Dumper=Dumper)

    # If we're dumping to a stream, pre-pend the initial comment block.
    if hasattr(data, '__initial_comment_block') and stream is None and isinstance(ret, str):
        ret = data.__initial_comment_block + ret

    return ret

def pprint(data):
    yaml.dump(data, sys.stdout, default_flow_style=False, allow_unicode=True)

# This class is a helper that facilitates editing YAML files
# in place. Use as:
#
# with rtyaml.edit("path/to/data.yaml", default={}) as data:
#   data["hello"] = "world"
#
# The file is opened for editing ("r+ mode"), read, and its
# parsed YAML data returned as the with-block variable (`data`
# in this case). The file is kept open while the with-block
# is executing. When the with-block exits the stream is overwritten
# with the new YAML data, and the file is closed.
#
# This will of course only work if the file contains an array
# or object (dict), and you cannot assign a new value to the
# with-block variable --- you can only call its methods, e.g.
# you can edit the list and dict, but you can't replace the
# value with an entirely new list or dict.
#
# If the default parameter is not given, or is None, the file
# must exist. Otherwise, if the file doesn't exist, it's created
# and the with-block variable holds the default value.
#
# You can also pass a stream as the first argument if you want
# to open the file yourself. The stream must support seek, truncate,
# and close.
class edit:
    def __init__(self, fn_or_stream, default=None):
        self.fn_or_stream = fn_or_stream
        self.default = default
    def __enter__(self):
        if isinstance(self.fn_or_stream, str):
            # Open the named file.
            try:
                self.stream = open(self.fn_or_stream, "r+")
            except FileNotFoundError:
                if not isinstance(self.default, (list, dict)):
                    # If there is no default and the file
                    # does not exist, re-raise the exception.
                    raise
                else:
                    # Create a new file holding the default,
                    # then seek back to the beginning so
                    # we can read it below.
                    self.stream = open(self.fn_or_stream, "w+")
                    dump(self.default, self.stream)
                    self.stream.seek(0)

            self.close_on_exit = True
        else:
            # Use the given stream.
            self.stream = self.fn_or_stream

        # Parse stream and return data.
        self.data = load(self.stream)
        return self.data

    def __exit__(self, *exception):
        # Truncate stream and write new data.
        self.stream.seek(0);
        self.stream.truncate()
        dump(self.data, self.stream)

        # Close stream if we opened it.
        if getattr(self, "close_on_exit", False):
            self.stream.close()
