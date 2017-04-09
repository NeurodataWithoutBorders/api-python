function [f] = nwb_file(varargin)
    % parameters to Python nwb_file.open are:
    % start_time=None, mode="w-", identifier=None, description=None, core_spec="nwb_core.py", extensions=[], default_ns="core", keep_original=False, auto_compress=True)
    arg_names = { 'file_name', 'start_time', 'mode', 'identifier', 'description', 'core_spec', 'extensions', 'default_ns', 'keep_original', 'auto_compress', 'verbosity' };
    arg_types = { 'char',      'char',       'char', 'char',       'char',        'char',      'cell',       'char',       'logical',       'logical',       'char'};
    arg_default={ '',          '',           'w-',   '',           '',            'nwb_core.py', {},         'core',       false,           true,            'all' };
    arg_vals = parse_arguments(varargin, arg_names, arg_types, arg_default);
    % check for correct parameter values
    file_name = arg_vals.file_name;
    if isempty(file_name)
        error('Must specify file name, e.g. "test.nwb"')
    end
    % fprintf('in nwb_file, file_name=%s', file_name)
    mode = arg_vals.mode;
    valid_modes = {'r', 'r+', 'w', 'w-', 'a'};
    if ~isa(mode, 'char') || ~(nnz(strcmp(mode, valid_modes)) == 1)
        error('Invalid mode (%s).  Must be one of: %s', mode, strjoin(valid_modes,', '))
    end
    file_exists = (exist(file_name, 'file') == 2);
    if ~file_exists && (nnz(strcmp(mode, {'r', 'r+'})) == 1)
        error('File not found (%s).  File must exist to use mode "r" or "r+"', file_name)
    end
    creating_file = (strcmp(mode, 'w') || (nnz(strcmp(mode, {'a', 'w-'}))==1 && ~file_exists));
    identifier = arg_vals.identifier;
    description = arg_vals.description;
    if creating_file
        % creating a new file.  identifier and description required.
        if ~isa(identifier, 'char') || strcmp(identifier, '')
            error('When creating a file, "identifier" must be specified and be a string')
        end
        if ~isa(identifier, 'char') || strcmp(description, '')
            error('When creating a file, "description" must be specified and be a string')
        end
    end
    extensions = arg_vals.extensions;
    if ~iscellstr(extensions)
        error('extensions must be a cell array of strings')
    end
    % setup options for h5gate
    % previously had: 'custom_node_identifier', {'schema_id', 'Custom'}, ...
    options = {'mode', mode, ...
        'keep_original', arg_vals.keep_original, ...
        'auto_compress', arg_vals.auto_compress, ...
        'custom_node_identifier', {'neurodata_type', 'Custom'}, ...
        'verbosity', arg_vals.verbosity};
    if strcmp(arg_vals.core_spec, '-')
        spec_files = extensions;
    else
        spec_files = {extensions{:}, arg_vals.core_spec};
    end
    % open file
    f = h5g8.file(file_name, spec_files, arg_vals.default_ns, options);
    % set initial metadata
	py.nwb.nwb_init.nwb_init(f.fg_file, mode, arg_vals.start_time, identifier, description, creating_file)
end

