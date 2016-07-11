function [arg_vals] = parse_arguments(args,  arg_names, arg_types, arg_default)
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
                    class(val), arg, arg_types{i})
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
        

