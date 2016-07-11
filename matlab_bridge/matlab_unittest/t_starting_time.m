function t_starting_time(verbosity)

% TESTS use of TimeSeries.starting_time

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

function test_nodata_series()
    name = 'starting_time';
    % create_startingtime_series(fname, name, 'acquisition')
    create_startingtime_series(fname, name, '/acquisition/timeseries');
    test_utils.verify_timeseries(fname, name, 'acquisition/timeseries', 'TimeSeries');
    test_utils.verify_absent(fname, ['acquisition/timeseries/', name], 'timestamps');
    val = test_utils.verify_present(fname, ['acquisition/timeseries/', name], 'starting_time');
    if val ~= 0.125
        test_utils.error('Checking start time', 'Incorrect value')
    end
    val = test_utils.verify_attribute_present(fname, ['acquisition/timeseries/starting_time/', name], 'rate');
    if val ~= 2
        test_utils.error('Checking rate', 'Incorrect value')
    end
end

function create_startingtime_series(fname, name, target) 
   settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'start_time', 'Sat Jul 04 2015 3:14:16' ...
        'identifier', nwb_utils.create_identifier('starting time test'), ...
        'description','time series starting time test'};
    f = nwb_file(settings{:});
    
    %
%     stime = neurodata.create_timeseries('TimeSeries', name, target)
%     stime.set_data([0, 1, 2, 3], unit='n/a', conversion=1, resolution=1)
%     stime.set_value('num_samples', 4)
%     stime.set_time_by_rate(0.125, 2)
    %
    
    stime = f.make_group('<TimeSeries>', name, 'path', target);
    stime.set_dataset('data', [0, 1, 2, 3], 'attrs', {'unit', 'n/a', ...
        'conversion', 1, 'resolution', 1});
    stime.set_dataset('num_samples', 4);
    
    % stime.set_time_by_rate(0.125, 2)
    stime.set_dataset('starting_time', 0.125, 'attrs', {'rate', 2, 'unit', 'Seconds'});
%     stime.finalize()
%     neurodata.close()
    f.close()
end

test_nodata_series()
fprintf('%s PASSED\n', script_name);
end

