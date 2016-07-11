function t_unittimes(verbosity)

% TESTS creation of UnitTimes interface and data stored within

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

function test_unit_times()
    % create the file we're going to use
    ndata = create_empty_file(fname);
    % create a module to store processed data
    % mod = ndata.create_module('my spike times')
    mod = ndata.make_group('<Module>', 'my spike times');
    % ad a unit times interface to the module
    % iface = mod.create_interface('UnitTimes')
    iface = mod.make_group('UnitTimes');
    % make some data to store
    spikes = create_spikes();
%     for i in range(len(spikes)):
%         iface.add_unit(unit_name = 'unit-%d' % i, 
%                       unit_times = spikes[i], 
%                      description = '<description of unit>',
%                           source = 'Data spike-sorted by B. Bunny')

    for i = 1:length(spikes) % range(len(spikes)):
        unit_name = sprintf('unit-%d', i-1);
        ug = iface.make_group('<unit_N>', unit_name);
        ug.set_dataset('times', spikes{i});
        ug.set_dataset('unit_description', '<description of unit>');
        ug.set_dataset('source', 'Data spike-sorted by B. Bunny');
    end
        

    % clean up and close objects
    % iface.finalize()
    % mod.finalize()
    ndata.close()

    % test random sample to make sure data was stored correctly
%     h5 = h5py.File(fname)
%     times = h5['processing/my spike times/UnitTimes/unit-0/times'].value
%     assert len(times) == len(spikes[0]), 'Spike count for unit-0 wrong'
%     assert abs(times[1] - spikes[0][1]) < 0.001, 'Wrong time found in file'
%     h5.close()
    times = hdf5read(fname,'processing/my spike times/UnitTimes/unit-0/times');
    if length(times) ~= length(spikes{1})
        error('Spike count for unit-0 wrong')
    end
    if abs(times(2) - spikes{1}(2)) >= 0.001
        error('Wrong time found in file')
    end
end


function [spikes] = create_spikes()
    spikes = cell([1, 3]);
    spikes{1} = [1.3, 1.4, 1.9, 2.1, 2.2, 2.3];
    spikes{2} = [2.2, 3.0];
    spikes{3} = [0.3, 0.4, 1.0, 1.1, 1.45, 1.8, 1.81, 2.2];
end


function [f] = create_empty_file(fname)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'start_time', 'Sat Jul 04 2015 3:14:16' ...
        'identifier', nwb_utils.create_identifier('UnitTimes example'), ...
        'description','Test file with spike times in processing module'};
    f = nwb_file(settings{:});
end

test_unit_times()
fprintf('%s PASSED\n', script_name);
end

