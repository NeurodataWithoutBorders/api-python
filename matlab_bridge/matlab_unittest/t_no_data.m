function t_no_data(verbosity)

% creates time series without 'data' field
% TESTS TimeSeries.ignore_data()

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end


function test_nodata_series()
    name = 'nodata';
    % create_nodata_series(fname, name, 'acquisition')
    create_nodata_series(fname, name, '/acquisition/timeseries');
    test_utils.verify_timeseries(fname, name, 'acquisition/timeseries', 'TimeSeries');
    test_utils.verify_absent(fname, ['acquisition/timeseries/', name], 'data');
end

function create_nodata_series(fname, name, target)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity ...
        'start_time', 'Sat Jul 04 2015 3:14:16' ...
        'identifier', nwb_utils.create_identifier('nodata example'), ...
        'description','time series no data test'};
    f = nwb_file(settings{:});
    nodata = f.make_group('<TimeSeries>', name, 'path', target);
    nodata.set_dataset('timestamps', {0});  % use cell array to create 1 element array
    f.close()
end

test_nodata_series()
fprintf('%s PASSED\n', script_name);
end

