function t_no_time(verbosity)

% creates time series without 'timestamps' or 'starting_time' fields
% TESTS TimeSeries.ignore_time()
% TESTS timeseries placement in acquisition, stimulus, templates

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

function test_notime_series()
    name = 'notime';
    % create_notime_series(fname, name, 'acquisition')
    create_notime_series(fname, name, '/acquisition/timeseries')
    test_utils.verify_timeseries(fname, name, 'acquisition/timeseries', 'TimeSeries')
    test_utils.verify_absent(fname, ['acquisition/timeseries/',name], 'timestamps')
    test_utils.verify_absent(fname, ['acquisition/timeseries/',name], 'starting_time')

    % create_notime_series(fname, name, 'stimulus')
    create_notime_series(fname, name, '/stimulus/presentation')
    test_utils.verify_timeseries(fname, name, 'stimulus/presentation', 'TimeSeries')
    % create_notime_series(fname, name, 'template')
    create_notime_series(fname, name, '/stimulus/templates')
    test_utils.verify_timeseries(fname, name, 'stimulus/templates', 'TimeSeries')
end

function create_notime_series(fname, name, target)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'start_time', 'Sat Jul 04 2015 3:14:16' ...
        'identifier', nwb_utils.create_identifier('notime example'), ...
        'description','Test no time'};
    f = nwb_file(settings{:});

    notime = f.make_group('<TimeSeries>', name, 'path', target);
    % following used for testing more missing_fields
    % notime = f.make_group('<VoltageClampSeries>', name, path=target)
    % not sure why cell array used below.  Maybe required if only one
    % element
    notime.set_dataset('data', {0.0}, 'attrs', {'unit', 'n/a', ...
        'conversion', 1.0, 'resolution', 1.0});
    f.close()
end

test_notime_series()
fprintf('%s PASSED\n', script_name);
end

