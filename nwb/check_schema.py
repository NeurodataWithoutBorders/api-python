# script to validate h5gate schema files using json schema

import os.path
import sys
# import json
import jsonschema
import ast

def load_schema(file_name):
    """ Load Python file that contains JSON formatted as a Python dictionary.
    Files in this format are used to store the schema because, unlike pure JSON,
    they allow comments and formatting long strings to make them easier to read."""
    if not os.path.isfile(file_name):
        print "Unable to locate file %s" % file_name
        sys.exit(1)
    with file(file_name) as f:
        file_contents = f.read()
    try:
        # use use ast.literal_eval to parse
        pydict = ast.literal_eval(file_contents)
    except Exception, e:
        print "** Unable to parse file '%s' (should be mostly JSON)" % file_name
        print "Error is: %s" % e
        sys.exit(1)
    assert isinstance(pydict, dict), "** File '%s does not contain python dictionary" % file_name
    return pydict


def load_meta_schema():
    meta_schema_file = "meta_schema.json"
    if not os.path.isfile(meta_schema_file):
        print "Unable to locate file %s" % file_name
        sys.exit(1)
    with file(meta_schema_file) as f:
        file_contents = f.read()
    meta_schema = json.loads(file_contents)
    return meta_schema


if __name__ == "__main__":
    nwb_dir = os.path.dirname(os.path.realpath(__file__))
    meta_schema_file = os.path.join(nwb_dir, "meta_schema.py")
    fs_var = "fs"
    if len(sys.argv) != 2:
        print "format is:"
        print "python %s <specification_file>" % sys.argv[0]
        print "where <specification_file> is either the name of a schema file, or '-' for the"
        print "default core specification (nwb_core.py)"
        sys.exit(0)
    schema_file = os.path.join(nwb_dir, 'nwb_core.py') if sys.argv[1] == '-' else sys.argv[1]
    meta_schema = load_schema(meta_schema_file)
    schema = load_schema(schema_file)
    if fs_var not in schema:
        print "** Error, key '%s' not defined in top level of file '%s'" % (fs_var, schema_file)
        sys.exit(1)
    schema = schema[fs_var]
    print "checking specification in file '%s'" % schema_file
    jsonschema.validate(schema, meta_schema)
    print "File is valid."
    


    
