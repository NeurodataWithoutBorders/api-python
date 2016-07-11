classdef group < h5g8.node
    %Class for matlab nwb group objects
    methods
        function obj = group(ml_f, fg_group)
            % create a matlab group that wraps the Python fg_group
            % ml_f is the matlab h5g8 file object
            % fg_group is the python h5gate Group object
            obj = obj@h5g8.node(ml_f, fg_group); % save in superclass
        end
        function [group_obj] = make_group(obj, id, varargin)
            % make a group inside the current group
            % parameters in h5gate make_group are:
            % (self, id, name='', attrs={}, link='', abort=True ):
            arg_names = { 'name', 'attrs', 'link', 'abort'};
            arg_types = { 'char', 'cell',  'char', 'logical' };
            arg_default={ '',     {},      '',     true };
            arg_vals = obj.ml_file.parse_arguments(varargin, arg_names, arg_types, arg_default);
            name = arg_vals.name;
            % attrs = py.list(arg_vals.attrs);
            attrs = arg_vals.attrs;
            [atrs1d, attrs_shape] = obj.ml_file.flatten_attrs(attrs); % modifies attrs
            atrs1d = py.list(atrs1d);
            link = arg_vals.link;
            abort = arg_vals.abort;
            fg_grp = obj.fg_node.make_group(id, name, atrs1d, link, abort, attrs_shape);
            group_obj = h5g8.group(obj.ml_file, fg_grp);
        end
        function [group_obj] = make_custom_group(obj, qid, varargin)
            % make a custom group inside the current group
            % parameters in h5gate make_custom_group are:
            % make_custom_group(self, qid, name='', path='', attrs={}):
            arg_names = { 'name', 'path', 'attrs'};
            arg_types = { 'char', 'char', 'cell' };
            arg_default={ '',     '',     {} };
            arg_vals = obj.ml_file.parse_arguments(varargin, arg_names, arg_types, arg_default);
            name = arg_vals.name;
            path = arg_vals.path;
            % attrs = py.list(arg_vals.attrs);
            attrs = arg_vals.attrs;
            [atrs1d, attrs_shape] = obj.ml_file.flatten_attrs(attrs); % modifies attrs
            atrs1d = py.list(atrs1d);
            fg_grp = obj.fg_node.make_custom_group(qid, name, path, atrs1d, attrs_shape);
            group_obj = h5g8.group(obj.ml_file, fg_grp);
        end     
        function [ds_obj] = set_dataset(obj, id, value, varargin)
            % set dataset inside the current group
            % parameters in h5gate set_dataset are:
            % (self, id, value, name='', attrs={}, dtype=None, compress=False):
            arg_names = { 'name', 'attrs', 'dtype', 'compress'};
            arg_types = { 'char', 'cell',  'char', 'logical' };
            arg_default={ '',     {},      '',     false };
            arg_vals = obj.ml_file.parse_arguments(varargin, arg_names, arg_types, arg_default);
            name = arg_vals.name;
            % attrs = py.list(arg_vals.attrs);
            attrs = arg_vals.attrs;
            [atrs1d, attrs_shape] = obj.ml_file.flatten_attrs(attrs); % modifies attrs
            atrs1d = py.list(atrs1d);
            dtype = arg_vals.dtype;
            compress = arg_vals.compress;
            % value_info = obj.ml_file.make_value_info(value);
            value = obj.ml_file.get_link_node(value);
            [val1d, shape] = obj.ml_file.flatten(value);
            % pass value_info to Python instead of value to avoid type conv
            % Need to setup named parameter list
            % fg_dataset = obj.fg_node.set_dataset(id, value_info, name, attrs, dtype, compress);
            fg_dataset = obj.fg_node.set_dataset(id, val1d, name, atrs1d, dtype, compress, shape, attrs_shape);
            ds_obj = h5g8.dataset(obj.ml_file, fg_dataset);
        end
        function [ds_obj] = set_custom_dataset(obj, qid, value, varargin)
            % set custom dataset inside the current group
            % parameters in h5gate set_custom_dataset are:
            % (self, qid, value, name='', path='', attrs={}, dtype=None, compress=False):
            arg_names = { 'name', 'path', 'attrs', 'dtype', 'compress'};
            arg_types = { 'char', 'char', 'cell',  'char', 'logical' };
            arg_default={ '',     '',     {},      '',     false };
            arg_vals = obj.ml_file.parse_arguments(varargin, arg_names, arg_types, arg_default);
            name = arg_vals.name;
            path = arg_vals.path;
            % attrs = py.list(arg_vals.attrs);
            attrs = arg_vals.attrs;
            [atrs1d, attrs_shape] = obj.ml_file.flatten_attrs(attrs); % modifies attrs
            atrs1d = py.list(atrs1d);
            dtype = arg_vals.dtype;
            compress = arg_vals.compress;
            % value_info = obj.ml_file.make_value_info(value);
            value = obj.ml_file.get_link_node(value);
            [val1d, shape] = obj.ml_file.flatten(value);
            % pass value_info to Python instead of value to avoid type conv
            % Need to setup named parameter list
            fg_dataset = obj.fg_node.set_custom_dataset(qid, val1d, name, path, atrs1d, dtype, compress, shape, attrs_shape);
            ds_obj = h5g8.dataset(obj.ml_file, fg_dataset);
        end
    end
    
end
