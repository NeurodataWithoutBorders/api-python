classdef file < handle
    %Class for creating hdf5 files using h5gate specification language
    % Calls python functions in h5gate.  < handle (above) is to inherit
    % from handle, which causes the same object to be referenced, rather
    % than a new one created each call.
    
    properties
        file_name
        file_pointer  % HDf5 file created in matlab
        fg_file       % File_gate (h5gate) object (made by Python h5gate)
    end
    
    methods
        function obj = file(file_name, spec_files, default_ns, options)
            % Create file object (wrapper for Python h5gate File)
            obj.file_name = file_name;
            % fprintf('before calling h5gate, file_name=%s', file_name);
            if count(py.sys.path,'') == 0
                insert(py.sys.path,int32(0),'');
            end
            kwargs = pyargs('spec_files', spec_files, 'default_ns', default_ns, 'options', options);
            obj.fg_file = py.nwb.h5gate.File(file_name, kwargs);
        end
        function [group_obj] = make_group(obj, id, varargin)
            % parameters in h5gate.make_group are:
            % (self, qid, name='', path='', attrs={}, link='', abort=True):
            arg_names = { 'name', 'path', 'attrs', 'link', 'abort'};
            arg_types = { 'char', 'char', 'cell',  'char', 'logical' };
            arg_default={ '',     '',      {},     '',     true };
            arg_vals = obj.parse_arguments(varargin, arg_names, arg_types, arg_default);
            name = arg_vals.name;
            path = arg_vals.path;
            % attrs = py.list(arg_vals.attrs);
            attrs = arg_vals.attrs;
            [atrs1d, attrs_shape] = obj.flatten_attrs(attrs);
            atrs1d = py.list(atrs1d);
            link = arg_vals.link;
            abort = arg_vals.abort;
            % calls the python function make_group in h5gate
            fg_group = obj.fg_file.make_group(id, name,  path, atrs1d, link, abort, attrs_shape);
            % call the matlab group constructor
            group_obj = h5g8.group(obj, fg_group);
        end
        function [group_obj] = make_custom_group(obj, qid, varargin)
            % parameters in h5gate.make_custom_group are:
            % (self, qid, name='', path='', attrs={}):
            arg_names = { 'name', 'path', 'attrs'};
            arg_types = { 'char', 'char', 'cell'};
            arg_default={ '',     '',      {}};
            arg_vals = obj.parse_arguments(varargin, arg_names, arg_types, arg_default);
            name = arg_vals.name;
            path = arg_vals.path;
            % attrs = py.list(arg_vals.attrs);
            attrs = arg_vals.attrs;
            [atrs1d, attrs_shape] = obj.flatten_attrs(attrs);
            atrs1d = py.list(atrs1d);
            % call python function make_custom_group in h5gate
            fg_group = obj.fg_file.make_custom_group(qid, name,  path, atrs1d, attrs_shape);
            % call the matlab group constructor
            group_obj = h5g8.group(obj, fg_group);
        end        
        function [ds_obj] = set_dataset(obj, id, value, varargin)
            % parameters in h5gate.set_dataset are:
            % (self, qid, value, name='', path='', attrs={}, dtype=None, compress=False):
            arg_names = { 'name', 'path', 'attrs', 'dtype', 'compress'};
            arg_types = { 'char', 'char', 'cell',  'char', 'logical' };
            arg_default={ '',     '',     {},      '',     false };
            arg_vals = obj.parse_arguments(varargin, arg_names, arg_types, arg_default);
            name = arg_vals.name;
            path = arg_vals.path;
            % attrs = py.list(arg_vals.attrs);
            attrs = arg_vals.attrs;
            [atrs1d, attrs_shape] = obj.flatten_attrs(attrs);
            atrs1d = py.list(atrs1d);
            dtype = arg_vals.dtype;
            compress = arg_vals.compress;
            % value_info = obj.make_value_info(value);
            value = obj.get_link_node(value);
            [val1d, shape] = obj.flatten(value);
            % pass value_info to Python instead of value to avoid type conversion
            % fg_dataset = obj.fg_file.set_dataset(id, value_info, name, path, attrs, dtype, compress);
            fg_dataset = obj.fg_file.set_dataset(id, val1d, name, path, atrs1d, dtype, compress, shape, attrs_shape);
            ds_obj = h5g8.dataset(obj, fg_dataset);
            % obj.process_h5commands(value, value_info);
        end
        function [ds_obj] = set_custom_dataset(obj, id, value, varargin)
            % parameters in h5gate.set_custom_dataset are:
            % (self, qid, value, name='', path='', attrs={}, dtype=None, compress=False)
            arg_names = { 'name', 'path', 'attrs', 'dtype', 'compress'};
            arg_types = { 'char', 'char', 'cell',  'char', 'logical' };
            arg_default={ '',     '',     {},      '',     false };
            arg_vals = obj.parse_arguments(varargin, arg_names, arg_types, arg_default);
            name = arg_vals.name;
            path = arg_vals.path;
            % attrs = py.list(arg_vals.attrs);
            attrs = arg_vals.attrs;
            [atrs1d, attrs_shape] = obj.flatten_attrs(attrs); % modifies attrs
            atrs1d = py.list(atrs1d);
            dtype = arg_vals.dtype;
            compress = arg_vals.compress;
            % value_info = obj.make_value_info(value);
            value = obj.get_link_node(value);
            [val1d, shape] = obj.flatten(value);
            % pass value_info to Python instead of value to avoid type conversion
            % fg_dataset = obj.fg_file.set_custom_dataset(id, value_info, name, path, attrs, dtype, compress);
            fg_dataset = obj.fg_file.set_custom_dataset(id, val1d, name, path, atrs1d, dtype, compress, shape, attrs_shape);
            ds_obj = h5g8.dataset(obj, fg_dataset);
            % obj.process_h5commands(value, value_info);
        end
        function [ml_node] = get_node(obj, full_path, varargin)
            % return a h5g8.node given the full path
            arg_names = { 'abort'};
            arg_types = { 'logical' };
            arg_default={  true };
            arg_vals = obj.parse_arguments(varargin, arg_names, arg_types, arg_default);
            abort = arg_vals.abort;
            fg_node = obj.fg_file.get_node(full_path, abort);
            % create a new h8g8 node wrapping the h5gate node
            if isa(fg_node, 'py.nwb.h5gate.Dataset')
                ml_node = h5g8.dataset(obj, fg_node);
            elseif isa(fg_node, 'py.nwb.h5gate.Group')
                ml_node = h5g8.group(obj, fg_node);
            else
                error('unrecognized type returned in get_node "%s"', class(fg_node));
            end
        end
        function close(obj)
            obj.fg_file.close();
        end
%         function delete(obj)
%           % called when obj deleted
%           fprintf('matlab nwb.file delete called for file %s', obj.file_name)
%         end
        
        %%%%%% Support functions
        function [arg_vals] = parse_arguments(obj, args,  arg_names, arg_types, arg_default)
            % parse variable arguements passed to function, return
            % values for each defined in arg_defs.  arg_names has argument
            % names, arg_types, the expected type, either 'char' (string) or 'cell'
            % 'cell' is cell array used for list of alternate key, values
            % set up default values to empty string or empty cell array
            arg_vals = struct;
            for i=1:numel(arg_names)
                arg_vals.(arg_names{i}) = arg_default{i};
            end
            found_named_arg = '';
            i = 1;
            while i <= numel(args)
                arg = args{i};
                if ischar(arg) && ismember(arg, arg_names)
                    % found named argument
                    val = args{i+1};
                    [~, idx] = ismember(arg, arg_names);
                    if ~strcmp(class(val), arg_types{idx})
                        error('Unexpected type (%s) for parameter "%s", expecting "%s"', ...
                            class(val), arg, arg_types{idx})
                    end
                    found_named_arg = arg;
                    arg_vals.(arg) = val;
                    i = i + 2;
                    continue
                end
                if found_named_arg
                    error('Unnamed argument appears after named argument "%s"', ...
                        found_named_arg)
                end
                % maybe found valid un-named argument
                if i > numel(arg_names)
                    error('Too many un-named arguments in function call');
                end
                if ~strcmp(class(arg), arg_types{i})
                    error('Unnamed argment "%s" is type "%s"; expected type "%s"', ...
                        arg_names{i}, class(arg), arg_types{i});
                end
                % seems to be valid, save it
                arg_vals.(arg_names{i}) = arg;
                i = i + 1;
            end
        end
        function [val1d, shape] = flatten(obj, value)
            % If value is a multidimensional array (more than scalar or 1-d)
            % convert it to a 1-d array, and return the shape of the
            % transposed original array.  This done because multidimensional
            % arrays cannot be passed into Python, only 1-D values.  So
            % multidimensional arrays must be converted to 1-D, passed into
            % python, then converted to a multidimensional array of the
            % proper shape.
            % dtype = class(value);
            if ischar(value) || isscalar(value)
                % strings and scalar values are not converted
                shape = '';
                val1d = value;
                return
            end
            shape = int32(size(value));
            empty_array = length(shape) == 2 && length(value) == 0;
            if empty_array
               val1d = {};
               % pass in empty tuple so h5gate deflatten makes empty array
               shape = '0,';
               return
            end
            one_by_n = length(shape) == 2 && shape(1) == 1;
            if one_by_n
                % 1-d array.  Do nothing
                val1d = value;
                % set shape to "length," (as a string).  This will be
                % ignored by deflatten, but detected by deflatten_attrs
                % (both functions in h5gate).
                shape = sprintf('%i,', length(value));
            else
                % is multidimensional, convert to 1-d and save shape
                valt = nwb_utils.h5reshape(value); % make transponse
%                 nel = numel(value);
%                 val1d = reshape(value, [1, nel]);
                nel = numel(value);
                % val1d = reshape(value, [1, nel]);
                val1d = reshape(valt, [1, nel]);
                % fprintf('after flatten, values are:')
                % val1d(1:15)
            end
        end
        function [atrs1d, attrs_shape] = flatten_attrs(obj, attrs)
            % convert any attribute values that are multidimensional
            % arrays into a 1-d array.  Return flattend attrs (atrs1d)
            % and the shapes (attrs_shape).
            len_attrs = length(attrs);
            if len_attrs == 0
                % no attributes, return empty cell array for shapes
                attrs_shape = {};
                atrs1d = attrs;
                return
            end
            if mod(len_attrs, 2) == 1
                error('Invalid length of attrs (%i), must be even since they are key-value pairs', len_attrs)
            end
            atrs1d = cell([1,len_attrs]);
            attrs_shape = cell([1,len_attrs/2]);
            for i = 1:length(attrs_shape)
                ival = i*2;
                ikey = ival - 1;
                % copy key
                atrs1d{ikey} = attrs{ikey};
                [val1d, shape] = obj.flatten(attrs{ival});
                % save flattened attrs value
                atrs1d{ival} = val1d;
                if ischar(shape)
                    % shape is a char with int followed by comma, like:
                    % e.g. '0,' or '1,' or '34,'; or is empty strin
                    cvs_shape = shape;
                else
                    % convert numeric shape (array) into cvs string
                    cvs_shape = sprintf('%i,', shape);
                    cvs_shape = cvs_shape(1:end-1); % remove trailing ','
                end
                % save shape of that value
                attrs_shape{i} = cvs_shape;
            end
            % check for all cells empty in attrs_shape
            if all(cellfun(@isempty,attrs_shape))
                % no values were changed
                attrs_shape = {};
            end
        end
        function [link_node] = get_link_node(obj, value)
            % if value is a matlab h5g8 node, return the corresponding
            % python h5gate node for making a link
            % otherwise, just return the passed in value
            if isa(value, 'h5g8.node')
                % making link to other group or dataset
                link_node = value.fg_node;
            else
                link_node = value;
            end
        end 
        function [value_info] = make_value_info(obj, value)
            % create a string specifying the data type and dimensions
            % of matlab array value.  This string (value_info) is
            % passed to the Python code instead of the actual array.
            % Python code uses it to validate that "set_dataset" calls
            % has diminsions and data type matching that specified
            % for the data set in the specification language
            % ADDITION: if value is a matalb h5g8.dataset, then should
            % create a link to the specified dataset.  In this case
            % the corresponding h5gate.Dataset is returned so
            % h5gate will make the link.
            if isa(value, 'h5g8.dataset')
                % making link to other group
                value_info = value.fg_node;
                return
            end
            dtype = class(value);
            shape = size(value);
            one_by_n = length(shape) == 2 && shape(1) == 1;
            if (~iscellstr(value) && isscalar(value)) || (strcmp(dtype, 'char')  && one_by_n)
                shape_str = '[scalar]';
            elseif one_by_n
                shape_str = sprintf('[%i]', shape(2));
            else
                shape_str = mat2str(shape);
            end
            if strcmp(dtype, 'char') || iscellstr(value)
                type_str = 'str';  % to match python
            elseif ~isempty(strfind(dtype, 'int')) || strcmp(dtype, 'short')
                type_str = 'int';
            elseif nnz(strcmp(dtype, {'double', 'single', 'float'})) == 1
                type_str = 'float';
            else
                error('Unknown datatype (%s) in make_value_info', dtype);
            end
            value_info = sprintf('value_info: type="%s", shape="%s"', type_str, shape_str);
        end     
        function [h5_type] = get_h5_type(obj, ml_type)
            % Returns the hdf5 type corresponding to the numeric matlab type
            % Parameter ml_type is the matlab type
            % This taken from function "set_datatype_id" in
            % file "h5datacreate.m" available at the mathworks
            % shared code section
            switch ml_type
                case 'double'
                    h5_type = 'H5T_NATIVE_DOUBLE';
                case {'single','float'}
                    h5_type = 'H5T_NATIVE_FLOAT';
                case 'int64'
                    h5_type = 'H5T_NATIVE_LLONG';
                case 'uint64'
                    h5_type = 'H5T_NATIVE_ULLONG';
                case {'int32','int'}
                    h5_type = 'H5T_NATIVE_INT';
                case {'uint32','uint'}
                    h5_type = 'H5T_NATIVE_UINT';
                case {'int16','short'}
                    h5_type = 'H5T_NATIVE_SHORT';
                case 'uint16'
                    h5_type = 'H5T_NATIVE_USHORT';
                case 'int8'
                    h5_type = 'H5T_NATIVE_SCHAR';
                case 'uint8'
                    h5_type = 'H5T_NATIVE_UCHAR';
                otherwise
                    error('Unsupported datatype (%s) for writing to hdf5.\n', ml_type);
            end
        end
        function [type_id, space_id] = get_h5_properties(obj, data, path)
            % Create hdf5 type_id and space_id.  These are used for
            % creating hdf5 datasets and attributes. "data" is data being saved.
            % path is path to node.  Displayed if there is an error.
            ml_type = class(data);
            shape = size(data);
            one_by_n = length(shape) == 2 && shape(1) == 1;
            if ischar(data)  && one_by_n
                % save single string
                % some of this from: https://www.hdfgroup.org/hdf5-quest.html#str1
                len = shape(2);
                type_id = H5T.copy('H5T_C_S1');
                H5T.set_size (type_id, len);
                H5T.set_strpad(type_id, 'H5T_STR_NULLPAD');
                space_id = H5S.create('H5S_SCALAR');
             elseif iscellstr(data)
                % save cell array of strings, allow saving if empty
                if ~one_by_n && ~isempty(data)
                    error('Saving 2+ dimensional cell array of strings not implemented, path=\n%s', path)
                end
                len = shape(2);
                type_id = H5T.copy('H5T_C_S1');
                H5T.set_size (type_id, 'H5T_VARIABLE');
                space_id = H5S.create_simple(1,len,len);
             elseif isscalar(data)
                % saving a scalar numeric value
                h5_type = obj.get_h5_type(ml_type);
                % type_id = H5T.copy('H5T_NATIVE_INT');
                type_id = H5T.copy(h5_type);
                space_id = H5S.create('H5S_SCALAR');
             elseif one_by_n
                % saving a one-d numeric array
                h5_type = obj.get_h5_type(ml_type);
                type_id = H5T.copy(h5_type);
                len = shape(2);
                space_id = H5S.create_simple(1,len,len);
             else
                % should be saving multi-dimensional numeric array
                h5_type = obj.get_h5_type(ml_type);
                type_id = H5T.copy(h5_type);
                h5_dims = fliplr(shape);
                h5_maxdims = h5_dims;
                rank = length(h5_dims);
                space_id = H5S.create_simple(rank,h5_dims,h5_maxdims);
            end
        end
        function [chunk_r] = guess_chunk(obj, shape, typesize)
            % Guess an appropriate chunk layout for a dataset, given its shape and
            % the size of each element in bytes.  Chunks are generally close
            % to some power-of-2 fraction of
            % each axis, slightly favoring bigger values for the last index.
            % This function from h5py, _hl/filter.py (converted to Matlab)        
            CHUNK_BASE = 16*1024;    % Multiplier by which chunks are adjusted
            CHUNK_MIN = 8*1024;      % Soft lower limit (8k)
            CHUNK_MAX = 1024*1024;    % Hard upper limit (1M)
            one_by_n = length(shape) == 2 && shape(1) == 1;
            if one_by_n
                shape = shape(2);
            end
            chunks = shape;
            % Determine the optimal chunk size in bytes using a PyTables expression.
            % This is kept as a float.
            dset_size = prod(chunks)*typesize;
            target_size = CHUNK_BASE * (2.^log10(dset_size/(1024.*1024)));
            if target_size > CHUNK_MAX
                target_size = CHUNK_MAX;
            elseif target_size < CHUNK_MIN
                target_size = CHUNK_MIN;
            end
            ndims = length(shape);
            idx = 0;
            while true
                % Repeatedly loop over the axes, dividing them by 2.  Stop when:
                % 1a. We're smaller than the target chunk size, OR
                % 1b. We're within 50% of the target chunk size, AND
                %  2. The chunk is smaller than the maximum chunk size
                chunk_bytes = prod(chunks)*typesize;
                if (chunk_bytes < target_size || ...
                 abs(chunk_bytes-target_size)/target_size < 0.5) && ...
                 chunk_bytes < CHUNK_MAX
                    break
                end
                if prod(chunks) == 1
                    break  % Element size larger than CHUNK_MAX
                end
                idxm = mod(idx, ndims) + 1;
                chunks(idxm) = ceil(chunks(idxm) / 2.0);
                idx = idx + 1;
            end
            chunk_r = floor(chunks);
        end        
        function [ml_data] = convert_py_data(obj, py_data)
            % converts data from type passed by python to
            % type used by matlab
            ptype = class(py_data);
            if ~strcmp(ptype(1:3), 'py.')
                % no need to convert, is not python type
                ml_data = py_data;
            else
                switch ptype
                    case {'py.str', 'py.numpy.string_'}
                        ml_data = char(py_data);
                    otherwise
                        fprintf('data cannot convert is:');
                        py_data
                        error('Unable to convert Python type "%s" to matlab', ptype)
                end
            end
        end 
        function save_dataset(obj, path, data, dtype, compress)
            % Creates hdf5 dataset at location path, writes value into it.
            % This is done using the low level matlab hdf5 api to enable
            % using the file_pointer to the hdf5 file, which must be
            % available for writing other nodes and attributes
            % dtype - specified data type (ignored now.  Uses matlab type).
            % compression - True if should compress
            % TODO - use dtype and compression
            if isempty(data)
                fprintf('Warning: attempted to save data with length 0, path=%s\n', path);
                data = '-';  % just save as a dash for now
            end
            f = obj.file_pointer;
            % create any intermediate groups along the way.
		    lcpl = H5P.create('H5P_LINK_CREATE');
		    H5P.set_create_intermediate_group(lcpl,1);
            [type_id, space_id] = obj.get_h5_properties(data, path);
            if iscellstr(data) && length(data) > 1
                % save cell array of strings
                % Create a dataset plist for chunking. This is needed for
                % all strings to display in hdfview.  Not sure why.
                dcpl = H5P.create('H5P_DATASET_CREATE');
                H5P.set_chunk(dcpl,2);
            elseif compress
                % need to create dcpl for compression,
                % from h5py/_hl/filters.py and dataset.py and
                % https://www.hdfgroup.org/ftp/HDF5/examples/examples-by-api/matlab/HDF5_M_Examples/h5ex_d_gzip.m
                shape = size(data);
                dv = data(1);
                s = whos('dv');
                itemsize = s.bytes;
                chunk = obj.guess_chunk(shape, itemsize);
                dcpl = H5P.create('H5P_DATASET_CREATE');
                H5P.set_deflate (dcpl, 4);
                H5P.set_chunk(dcpl,fliplr(chunk));
            else
                dcpl = 'H5P_DEFAULT';
            end
            % create the dataset
            dapl = 'H5P_DEFAULT';
            dset_id = H5D.create(f,path,type_id,space_id,lcpl,dcpl,dapl);
            % write data into it
            plist = 'H5P_DEFAULT';
            H5D.write(dset_id,'H5ML_DEFAULT','H5S_ALL','H5S_ALL',plist,data);
            H5T.close(type_id);
            H5S.close(space_id);
            H5D.close(dset_id); 
        end
        function save_attribute(obj, path, name, data)
            % Create and saves hdf5 attribute.  path -path to node,
            % name -name of attribute, data -data to save
            f = obj.file_pointer;
            obj_id = H5O.open(f,path,'H5P_DEFAULT');
            % delete attribute if already exist
            try
                attr_id = H5A.open_by_name(f,path,name);
                % attribute exists, delete it
                H5A.delete(obj_id,name);
            catch
                % attribute does not exist, no need to delete it
            end
            acpl = H5P.create('H5P_ATTRIBUTE_CREATE');
            [type_id, space_id] = obj.get_h5_properties(data, path);
            attr_id = H5A.create(obj_id,name,type_id,space_id,acpl);
            H5A.write(attr_id,'H5ML_DEFAULT',data)
            H5O.close(obj_id);
            H5A.close(attr_id);
            H5T.close(type_id);
        end
        function process_h5commands(obj, value, value_info)
            % process all the hdf5 commands generated by the h5gate python module
            % value and value_info are only used for create_dataset command
            plist = 'H5P_DEFAULT';
            for full_cmd = obj.fg_file.h5commands;
                cmd_tuple = py.operator.getitem(full_cmd , int32(0));   %R2015b: full_cmd{1};
                cmd =  char(py.operator.getitem(cmd_tuple, int32(0)));  %R2015b: char(cmd_tuple{1});
                switch cmd
                    case 'create_file'
                        filename = char(py.operator.getitem(cmd_tuple, int32(1))); %R2015b: char(cmd_tuple{2});
                        obj.file_pointer = H5F.create(filename, ...
                            'H5F_ACC_TRUNC', 'H5P_DEFAULT', 'H5P_DEFAULT');
                    case 'close_file'
                        H5F.close(obj.file_pointer);
                    case 'create_group'
                        path = char(py.operator.getitem(cmd_tuple, int32(1))); %R2015b: char(cmd_tuple{2});
                        % H5G.create(obj.file_pointer,path,plist)
                        lcpl = H5P.create('H5P_LINK_CREATE');
		                H5P.set_create_intermediate_group(lcpl,1);
                        H5G.create(obj.file_pointer,path,lcpl,plist,plist);
                    case 'create_dataset'
                        path = char(py.operator.getitem(cmd_tuple, int32(1))); %R2015b:  char(cmd_tuple{2});
                        data = obj.convert_py_data(py.operator.getitem(cmd_tuple, int32(2)));  %R2015b: obj.convert_py_data(cmd_tuple{3});
                        dtype = char(py.operator.getitem(cmd_tuple, int32(3)));  %R2015b: char(cmd_tuple{4});
                        compress = py.operator.getitem(cmd_tuple, int32(4));  %R2015b: cmd_tuple{5};
                        if nargin == 3 || isempty(path)
                            % was passed value and value info, make sure
                            % value_info matches data, then use value for data
                            if ~strcmp(data, value_info)
                                error('create_dataset value_info (%s) does not match data', value_info);
                            end
                            data = value;
                        end
                        obj.save_dataset(path, data, dtype, compress);
                    case 'set_attribute'
                        path = char(py.operator.getitem(cmd_tuple, int32(1)));  %R2015b: char(cmd_tuple{2});
                        name = char(py.operator.getitem(cmd_tuple, int32(2))); %R2015b: char(cmd_tuple{3});
                        data = obj.convert_py_data(py.operator.getitem(cmd_tuple, int32(3))); %R2015b: obj.convert_py_data(cmd_tuple{4});
                        obj.save_attribute(path, name, data);
                    case 'create_softlink'
                        path = char(py.operator.getitem(cmd_tuple, int32(1)));  %R2015b: char(cmd_tuple{2});
                        target_path = char(py.operator.getitem(cmd_tuple, int32(2)));  %R2015b: char(cmd_tuple{3});
                        lcpl = 'H5P_DEFAULT';
                        lapl = 'H5P_DEFAULT';
                        H5L.create_soft(target_path,obj.file_pointer,path,lcpl,lapl);
                    otherwise
                        error('** Invalid h5 command from h5gate %s', cmd);
                end
            end
            obj.fg_file.clear_storage_commands();
            return
        end
    end
end

