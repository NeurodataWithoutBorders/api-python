function t_array_layout(verbosity)
    global array_examples fname
    % TESTS storing arrays of different dimensions
    % This test made many to ensure consistency between data files
    % created in matlab and python, since matlab stores arrays in
    % column major order and python in row major order.  The
    % nwb file created by the matlab version of this test should
    % match that created by the python version (e.g. this test).

    script_base_name = mfilename();
    script_name = [script_base_name '.m'];
    fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
    if nargin < 1
        % default, display all information. Other options are: 'none', 'summary'
        verbosity = 'all';
    end

    function [f] = create_nwb_file(fname)
        settings = { ...
            'file_name', fname, ...
            'mode', 'w', ...
            'verbosity', verbosity, ...
            'start_time', 'Sat Jul 04 2015 3:14:16', ...
            'identifier', nwb_utils.create_identifier('array layout test'), ...
            'description','Test array layout storage'};
        f = nwb_file(settings{:});
    end



    % make manifold 3-d array global so can use for storing and testing
    % old version, incorrect - does not match Python version dimensions
    % man_v1 = [1 2 3 ; 2 3 4];
    % man_v1(:,:,2) = [3,4,5 ; 4,5,6];

    % build 3d array equivalant to following in Python
    % [[[1,2,3],[2,3,4]],[[3,4,5],[4,5,6]]]
    man1 = [1 2; 3 4];
    man2 = [2 3; 4 5];
    man3 = [3 4; 5 6];
    manifold = cat(3, man1, man2, man3); 

    % cell array of: name, value
    % set values to type int32; otherwise they will default to matlab
    % double.  Setting to int64 causes error to be generated:
    % Python Error: ValueError: bad typecode (must be c, b, B, u, h, H, i, I, l, L, f or d)
    % Not sure why,
    array_examples = { ...
        {'oneD_range5', int32([0, 1, 2, 3, 4])}, ...
        {'twoD_2rows_3cols', int32([ 0, 1, 2 ; 3, 4, 5])}, ...
        {'threeD_2x2x3', int32(manifold)} ...
        };


    % function test_field(fname, name, subdir)
    %     val = test_utils.verify_present(fname, ['general/optophysiology/', subdir, '/'], lower(name));
    %     if ~strcmp(val, name)
    %         test_utils.error('Checking metadata', 'field value incorrect');
    %     end
    % end

    function test_array_layout()
        f = create_nwb_file(fname);
        ang = f.make_group('analysis');
        stg = ang.make_custom_group('arrays');
        for idx = 1:length(array_examples)
            example = array_examples{idx};
            [name, val] = example{:};
            % prepend 'ga_' on attribute name stored in group
            ga_name = ['ga_' name];
            % print("Setting %s attribute" % name)
            stg.set_attr(ga_name, val);
            % print("Setting %s dataset" % name)
            % prepend 'da_' on attribute name stored with dataset
            da_name = ['da_' name];
            attrs = {da_name, val};
            % also set attribute with same name and value
            stg.set_custom_dataset(name, val, 'attrs', attrs);
        end
        f.close()
        % now read created file and verify values match
        errors = {};
        for idx = 1:length(array_examples)
            example = array_examples{idx};
            [name, val] = example{:};
            % read group attribute
            ga_name = ['ga_' name];
            aa_path = '/analysis/arrays'; 
            data = h5readatt(fname, aa_path, ga_name);
            datat = nwb_utils.h5reshape(data);
            if ~isequal(datat, val)
                msg = sprintf('Unexpected value for group attribute %s', ga_name);
                errors{end+1} = msg;
            end
            % read dataset value
            path = [aa_path '/' name]; 
            data = h5read(fname, path);
            datat = nwb_utils.h5reshape(data);  % convert from row to column major
            if ~isequal(datat, val)
                msg = sprintf('Unexpected value for dataset %s', name);
                errors{end+1} = msg;
            end
            % check dataset attribute value
            da_name = ['da_' name];
            data = h5readatt(fname, path, da_name);
            datat = nwb_utils.h5reshape(data);
            if ~isequal(datat, val)
                msg = sprintf('Unexpected value for dataset attribute %s', da_name);
                errors{end+1} = msg;
            end
        end
        if ~isempty(errors)
            fprintf('Found errors:\n');
            for i = 1:length(errors)
                fprintf('%s\n', errors{i})
            end
            error('Error exit - see errors above')
        end
                
    %     f = h5py.File(fname, "r")
    %     stg = f["analysis/arrays"]
    %     errors = []
    %     for example in array_examples:
    %         name,  val = example
    %         # check attribute value
    %         aval = stg.attrs[name]
    %         if not values_match(val, aval):
    %             error = "attribute %s, expected='%s' (type %s) \nfound='%s' (type %s)" % (
    %                 name, val, type(val), aval, type(aval))
    %             errors.append(error)
    %         # check dataset value
    %         dval = stg[name].value
    %         if not values_match(val, dval):
    %             error = "dataset %s, expected='%s' (type %s) \nfound='%s' (type %s)" % (
    %                 name, val, type(val), aval, type(aval))
    %             errors.append(error)           

    %     f.close()
    %     if len(errors) > 0:
    %         sys.exit("Errors found:\n%s" % "\n".join(errors))
        % print("%s PASSED" % __file__)
    end

    test_array_layout()
    fprintf('%s PASSED\n', script_name);
end
