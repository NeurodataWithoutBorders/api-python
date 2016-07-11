function t_if_add_ts(verbosity)

% test opening file in append mode
% TESTS creating a module
% TESTS creating an interface
% TESTS adding a timeseries to an interface

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end


function test_file()
    create_iface_series(fname, true);
    name1 = 'Ones';
    test_utils.verify_timeseries(fname, name1, 'processing/test module/BehavioralEvents', 'TimeSeries')
end


function create_iface_series(fname, newfile)
    if newfile
         settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
             'start_time', 'Sat Jul 04 2015 3:14:16' ...
             'identifier', nwb_utils.create_identifier('interface timeseries example'), ...
             'description','Test interface timeseries file'};
    else
         settings = {'file_name', fname, 'mode', 'r+'};
    end
    f = nwb_file(settings{:});
  
    %
%     mod = neurodata.create_module('test module')
%     iface = mod.create_interface('BehavioralEvents')
%     ts = neurodata.create_timeseries('TimeSeries', 'Ones')
%     ts.set_data(np.ones(10), unit='Event', conversion=1.0, resolution=float('nan'))
%     ts.set_value('num_samples', 10)
%     ts.set_time(np.arange(10))
%     iface.add_timeseries(ts)
%     iface.finalize()
%     mod.finalize()
    
    
    mod = f.make_group('<Module>', 'test module');
    iface = mod.make_group('BehavioralEvents');
    ts = iface.make_group('<TimeSeries>', 'Ones');
    ts.set_dataset('data', ones([1, 10]), 'attrs', {'unit', 'Event', ...
        'conversion', 1.0, 'resolution', NaN});
    ts.set_dataset('num_samples', 10);
    ts.set_dataset('timestamps',0:9);
    
    %
    % neurodata.close()
    f.close()
end

test_file()
fprintf('%s PASSED\n', script_name);
end

