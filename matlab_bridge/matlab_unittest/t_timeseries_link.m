function t_timeseries_link(verbosity)


% create multiple time series and link data and timestamps to between them
% TESTS hard linking of TimeSeries.data
% TESTS linked value in TimeSeries.data
% TESTS annotation of TimeSeries.data link
% TESTS hard linking of TimeSeries.timestamps
% TESTS linked value in TimeSeries.timestamps
% TESTS annotation of TimeSeries.timestamps link


script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end


function test_ts_link()
    root = 'root';
    create_linked_series(fname, root)
    test_utils.verify_timeseries(fname, [root,'1'], 'stimulus/templates', 'TimeSeries')
    test_utils.verify_timeseries(fname, [root,'2'], 'stimulus/presentation', 'TimeSeries')
    test_utils.verify_timeseries(fname, [root,'3'], 'acquisition/timeseries', 'TimeSeries')
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % make sure data is present in ts using link
    val = test_utils.verify_present(fname, 'stimulus/presentation/root2', 'data');
    if val(1) ~= 1
        test_utils.error('Checking link content', 'Incorrect value')
    end
    % make sure link is documented
    val = test_utils.verify_attribute_present(fname, 'stimulus/presentation/root2', 'data_link');
    if ~test_utils.search_for_substring(val, 'root1')
        test_utils.error('Checking attribute data_link', 'Name missing')
    end
    if ~test_utils.search_for_substring(val, 'root2')
        test_utils.error('Checking attribute data_link', 'Name missing')
    end
    val = test_utils.verify_attribute_present(fname, 'stimulus/templates/root1', 'data_link');
    if ~test_utils.search_for_substring(val, 'root1')
        test_utils.error('Checking attribute data_link', 'Name missing')
    end
    if ~test_utils.search_for_substring(val, 'root2')
        test_utils.error('Checking attribute data_link', 'Name missing')
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % make sure timestamps is present in ts using link
    val = test_utils.verify_present(fname, 'acquisition/timeseries/root3', 'timestamps');
    if val(1) ~= 2
        test_utils.error('Checking link content', 'Incorrect value')
    end
    % make sure link is documented
    val = test_utils.verify_attribute_present(fname, 'stimulus/presentation/root2', 'timestamp_link');
    if ~test_utils.search_for_substring(val, 'root2')
        test_utils.error('Checking attribute timestamp_link', 'Name missing')
    end
    if ~test_utils.search_for_substring(val, 'root3')
        test_utils.error('Checking attribute timestamp_link', 'Name missing')
    end
    val = test_utils.verify_attribute_present(fname, 'acquisition/timeseries/root3', 'timestamp_link');
    if ~test_utils.search_for_substring(val, 'root2')
        test_utils.error('Checking attribute timestamp_link', 'Name missing')
    end
    if ~test_utils.search_for_substring(val, 'root3')
        test_utils.error('Checking attribute timestamp_link', 'Name missing')
    end
end

function create_linked_series(fname, root)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'start_time', 'Sat Jul 04 2015 3:14:16' ...
        'identifier', nwb_utils.create_identifier('link test'), ...
        'description','time series link test'};
    f = nwb_file(settings{:});
    %
%     first = neurodata.create_timeseries('TimeSeries', root+'1', 'template')
%     first.ignore_time()
%     first.set_value('num_samples', 1)
%     first.set_data([1], unit='parsec', conversion=1, resolution=1e-12)
%     first.finalize()
    %
    
    first = f.make_group('<TimeSeries>', [root, '1'], 'path', '/stimulus/templates');
    % first.ignore_time()
    % first.set_value('num_samples', 1)
    first.set_dataset('num_samples', 1);
    d1 = first.set_dataset('data', {1}, 'attrs', {'unit', 'parsec', 'conversion', 1, ...
        'resolution', 1e-12});
    % first.finalize()
    
%     second = neurodata.create_timeseries('TimeSeries', root+'2', 'stimulus')
%     second.set_time([2])
%     second.set_value('num_samples', 1)
%     second.set_data_as_link(first)
%     second.finalize()
    %
    
    second = f.make_group('<TimeSeries>', [root, '2'], 'path', '/stimulus/presentation');
    t2 = second.set_dataset('timestamps', {2});
    second.set_dataset('num_samples', 1);
    second.set_dataset('data', d1); 
    
%     third = neurodata.create_timeseries('TimeSeries', root+'3', 'acquisition')
%     third.set_time_as_link(second)
%     third.set_value('num_samples', 1)
%     third.set_data([3], unit='parsec', conversion=1, resolution=1e-9)
%     third.finalize()

    third = f.make_group('<TimeSeries>', [root,'3'], 'path', '/acquisition/timeseries');
    third.set_dataset('timestamps', t2);
    third.set_dataset('num_samples', 1);
    third.set_dataset('data', {3}, 'attrs', {'unit', 'parsec', 'conversion', 1, ...
        'resolution', 1e-9});

    %
    % neurodata.close()
    f.close()
end

test_ts_link()
fprintf('%s PASSED\n', script_name);
end

