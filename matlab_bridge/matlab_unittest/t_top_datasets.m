function t_top_datasets(verbosity)

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

% TESTS top-level datasets

function test_refimage_series()
    name = 'refimage';
    create_refimage(fname, name)
    val = test_utils.verify_present(fname, '/', 'identifier');
    if ~strcmp(val, 'vwx')
        test_utils.error('Checking file idenfier', 'wrong contents')
    end
    val = test_utils.verify_present(fname, '/', 'file_create_date');
    val = test_utils.verify_present(fname, '/', 'session_start_time');
    if ~strcmp(val, 'xyz')
        test_utils.error('Checking session start time', 'wrong contents')
    end
    val = test_utils.verify_present(fname, '/', 'session_description');
    if ~strcmp(val, 'wxy')
        test_utils.error('Checking session start time', 'wrong contents')
    end
end

function create_refimage(fname, name)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'start_time', 'xyz' ...
        'identifier', 'vwx', ...
        'description','wxy'};
    f = nwb_file(settings{:});
    f.close()
end

test_refimage_series()
fprintf('%s PASSED\n', script_name);
end

