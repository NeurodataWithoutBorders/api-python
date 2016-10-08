{
    "$schema": "http://json-schema.org/draft-04/schema#",
    "description": "json-schema for h5gate specification language.  Used by check_schema.py",
    "type": "object",
    "patternProperties": {"^[a-zA-Z0-9_\-]+$": { "$ref": "#/definitions/h5g_schema" }},
    "additionalProperties": False,
    "definitions": {
        "h5g_schema": {
            "type": "object",
            "properties": {
                "info": {"$ref": "#/definitions/h5g_schema_info" },
                "schema": {"$ref": "#/definitions/h5g_schema_schema"},
                "doc": {"$ref": "#/definitions/h5g_schema_doc"},
            },
            "required": ["info", "schema" ],
            "additionalProperties": False,
        },
        "h5g_schema_info": {
            "type": "object",
            "properties": {
                "name": { "type": "string" },
                "version": { "type": "string" },
                "date": { "type": "string" },
                "author": { "type": "string" },
                "contact": { "type": "string" },
                "description": { "type": "string"}
            },
            "required": ["name", "version", "date", "author", "contact", "description"],
        },
        "h5g_schema_schema": {
            "type": "object",
            "patternProperties": {
                # group indicated by trailing slash, possibly followed by quantity
                "/[!+*^?]?$": { "$ref": "#/definitions/h5g_group" },
                # dataset indicated by absence of trailing slash
                "[^/!+*^?][!+*^?]?$": { "$ref": "#/definitions/h5g_dataset" }
            },
            "additionalProperties": False,
        },
        "h5g_group": {
            "type": "object",
            "properties": {
                "description": {  "$ref": "#/definitions/h5g_description" },
                "_description": { "type": "string" },
                "_required": { "$ref": "#/definitions/group_required" },
                "_exclude_in": { "$ref": "#/definitions/group_exclude_in" },
                "_closed": { "type": "boolean" },
                "_properties": { "$ref": "#/definitions/group_properties" },
                "attributes": { "$ref": "#/definitions/attributes" },
                "merge": { "$ref": "#/definitions/group_merge" },
                "merge+": { "$ref": "#/definitions/group_merge+" },
 	            "include": { "$ref": "#/definitions/group_include" },
	            "link":  { "$ref": "#/definitions/group_link" },
	            "autogen":  { "$ref": "#/definitions/autogen_create" }
	        },
	        "patternProperties": {
                "/[!+*^?]?$": { "$ref": "#/definitions/h5g_group" },
                # Need to explicitly exclude patterns that are reserved (cannot be names of member datasets)
                "^(?!(_description|description|_required|_exclude_in|_closed|_properties|attributes|merge|merge\+|include|link|autogen)$)[^\/]+[!+*^?]?$": { "$ref": "#/definitions/h5g_dataset" }
            },
            "additionalProperties": False,
        },
        "h5g_dataset": {
            "type": "object",
            # "required": ["data_type"],  # cannot require data_type in extensions because might only be adding attribute
            "properties": {
            	"description": {"type": "string" },
                "data_type": { "$ref": "#/definitions/data_type" },
	            "dimensions": {"$ref": "#/definitions/dimensions" },
	            "attributes": { "$ref": "#/definitions/attributes" },
	            "references": {"$ref": "#/definitions/reference"},
                "link":  { "$ref":  "#/definitions/dataset_link"},
                "autogen":  {"$ref": "#/definitions/value_autogen"}
            },
            "patternProperties": {
                "^(?!(description|data_type|dimensions|attributes|references|link|autogen)$)[^\/]+$": { "$ref": "#/definitions/dimension_def" }
            }
        },
        "h5g_schema_doc": {
            "type": "array",
        },
        "h5g_description": {
            "anyOf": [
                { "type" : "string" },
                { "$ref": "#/definitions/h5g_dataset" }
            ]
        },
        "autogen_create": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {"type": "string", "pattern": "create"}
            },
            "additionalProperties": False
        },
        "value_autogen": {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": [ "links", "link_path", "names", "values", "length", "missing" ]
                },
                "target": { "type": "string" },
                "trim": { "type": "boolean" },
                "allow_others": { "type": "boolean" },
                "qty": { "type": "string", "enum": ["!", "*"] },
                "tsig": {
                    "type": "object",
                    "properties": {
                        "type": { "type": "string", "enum": ["group", "dataset"] },
                        "attrs": { "type": "object" }
                    },
                    "additionalProperties": False
                },
                "include_empty": { "type": "boolean" },
                "sort": { "type": "boolean" },
                "format": { "type": "string" }
            }
        },
        "reference": {
            "type": "string"
            # can't be more specific because may be relative or absolute path
        },
        "group_properties": {
            "type": "object",
            "properties": {
                "abstract": {"type": "boolean"},
                "create": {"type": "boolean"},
                "closed": {"type": "boolean"}
            },
            "additionalProperties": False
        },
        "group_required": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z0-9_\-]+$": {  # identifier associated with a condition
                    "type": "array",
                    "items": [
                        { "type": "string" },  # condition string
                        { "type": "string" }   # message string
                    ],
                    "additionalItems": False
                }
            },
            "additionalProperties": False       
        },
        "group_exclude_in": {
            "type": "object",
            "patternProperties": {
                "^/([^/]+/?)*$": {  # path (starts with '/')
                    "type": "array",
                    "items": [ {"type": "string" }],
                    "additionalItems": { "type": "string" }  # ids in array
                }
            },
            "additionalProperties": False       
        },
        "group_merge": {
            "type": "array",
            "items": [{"type": "string", "pattern": "/$" }],
            "additionalItems": { "type": "string", "pattern": "/$" }  
        },
        "group_merge+": {
            # only one group can be listed in "merge+"
            "type": "array",
            "items": [{"type": "string", "pattern": "/$" }],
            "additionalItems": False
        },
        "data_type": {
            "type": "string",
            "pattern": "^(text|any|number|binary|((int|uint|float)((8|16|32|64)!?)?))$"
        },
        "dimensions": {
            "oneOf": [
                { "$ref": "#/definitions/array_of_strings" },
                { "$ref": "#/definitions/array_of_arrays_strings" }
            ]
        },
        "array_of_strings": {
            "type": "array",
            "items": [ {"type": "string" }],
            "additionalItems": { "type": "string" }
        },
        "array_of_arrays_strings": {  
            "type": "array",
            "items": [ { "$ref": "#/definitions/array_of_strings" }],
            "additionalItems": { "$ref": "#/definitions/array_of_strings" }
        },
        "attributes": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z0-9_\-]+$": {  # attribute id
                    "type": "object",
                    # following specifies that "data_type" or "value" required
                    "allOf": [
                        {
                            "type": "object",
                            "anyOf": [
                                {
                                    "type": "object",
                                    "properties": {
                                        "data_type": { "$ref": "#/definitions/data_type" },
                                    },
                                    "required": [ "data_type" ]
                                }, {
                                    "type": "object",
                                    "properties": {
                                        "value": { },
                                    },
                                    "required": [ "value" ]
                                }
                            ]
                        }, {
                            "type": "object",
                            "properties": {
                                "dimensions": { "$ref": "#/definitions/dimensions" },
                                "data_type": { "$ref": "#/definitions/data_type" },
 	                            "description": {"type": "string"},
 	                            "value": {},
 	                            "const": {"type": "boolean"},
                                "references": {"$ref": "#/definitions/reference"},
                                "autogen":  { "$ref": "#/definitions/value_autogen"}
                            },
                            "patternProperties": {
                                "^(?!(description|data_type|dimensions|references|value|const|autogen)$)[^\/]+$": { "$ref": "#/definitions/dimension_def" }
                            },
                            "additionalProperties": False
                        }
                    ]
 	            }
 	        }   
        },
        "dimension_def": {
            "type": "object",
            "required": ["type", "components"],
            "properties": {
                "type": { "type": "string", "pattern": "^structure$" },
                "components": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            # single dimension_components (usual case)
                            { "$ref": "#/definitions/dimension_components" },
                            # multiple dimension_components (specify should match one of them)
                            { "type": "array",
                              "items":  { "$ref": "#/definitions/dimension_components" }}
                        ]
                    }
                }
            }
        },
        "dimension_components": {
			"type": "object",
			"properties": {
				"alias": { "type": "string"},
				"unit": { "type": "string"},
				"references": { "type": "string" }
			},
			"additionalProperties": False,
			"required": ["alias", "unit"]
        },
        
#         "attributes": {
#             "type": "object",
#             "patternProperties": {
#                 "^[a-zA-Z0-9_\-]+$": {  # attribute id
#                     "type": "object",
#                     "properties": {
#                         "dimensions": { "$ref": "#/definitions/dimensions" },
#                         "data_type": { "$ref": "#/definitions/data_type" },
#  	                    "description": {"type": "string"},
#  	                    "value": {},
#  	                    "const": {"type": "boolean"},
#  	                    "references": {"type": "string"},
#  	                    "autogen":  {"type": "object"}
#  	                },
#  	                "additionalProperties": False,
#  	                "oneOf": [
#  	                    # require either data_type and value, allow both
#                         { "required": ["data_type"] },
#                         { "required": ["value"] }
#                     ]
#  	            }
#  	        }   
#         },
         
        "group_include": {
            "type": "object",
            "additionalProperties": False,
            "patternProperties": {
                "^[a-zA-Z0-9_\-<>: ]+/?[+*!?^]?$": {  # Identifier, optionally followd by quantity
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "_options": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "subclasses": { "type": "boolean"}
                            },
                        },
                    },
                },
            },
        },
        "group_link": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "target_type": { "type": "string" },
                "allow_subclasses": { "type": "boolean" }
            }
        },
        "dataset_link": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "target_type": { "type": "string" }
            }
        }
    }
}
#            "properties": {
#             "<MyNewModule>/": {
#               "type": "object",
#               "properties": {
#                 "merge": {
#                   "type": "array",
#                   "items": {
#                     "type": "string"
#                   }
#                 },
#                 "description": {
#                   "type": "string"
#                 },
#                 "include": {
#                   "type": "object",
#                   "properties": {
#                     "eint:MyNewInterface/": {
#                       "type": "object",
#                       "properties": {}
#                     },
#                     "core:BehavioralTimeSeries/": {
#                       "type": "object",
#                       "properties": {}
#                     }
#                   },
#                   "required": [
#                     "eint:MyNewInterface/",
#                     "core:BehavioralTimeSeries/"
#                   ]
#                 }
#               },
#               "required": [
#                 "merge",
#                 "description",
#                 "include"
#               ]
#             }
#           },
#           "required": [
#             "<MyNewModule>/"
#           ]
#         }
#       },
#       "required": [
#         "info",
#         "schema"
#       ]
#     }
#   },
#   "definitions": {
#         "": {},
#         "diskUUID": {},
#         "nfs": {},
#         "tmpfs": {}
#   }
# 
#   "required": [
#     "new_mod"
#   ]
# }