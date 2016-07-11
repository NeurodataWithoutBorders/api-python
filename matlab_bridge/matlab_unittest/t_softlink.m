function t_softlink(verbosity)

% creates time series without 'data' field
% TESTS softlink of TimeSeries.data

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname1 = [regexprep(script_base_name, '^t_', 's_') '1.nwb'];
fname2 = [regexprep(script_base_name, '^t_', 's_') '2.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

function test_softlink()
    name1 = 'softlink_source';
    name2 = 'softlink_reader';
%     create_softlink_source(fname1, name1, 'acquisition')
%     create_softlink_reader(fname2, name2, fname1, name1, 'acquisition')
    create_softlink_source(fname1, name1, '/acquisition/timeseries');
    create_softlink_reader(fname2, name2, fname1, name1, '/acquisition/timeseries');
    %
    test_utils.verify_timeseries(fname1, name1, 'acquisition/timeseries', 'TimeSeries');
    test_utils.verify_timeseries(fname2, name2, 'acquisition/timeseries', 'TimeSeries');
    %
    val = test_utils.verify_present(fname2, ['acquisition/timeseries/', name2], 'data');
end
    

function create_softlink_reader(fname, name, src_fname, src_name, target)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'start_time', 'Sat Jul 04 2015 3:14:16' ...
        'identifier', nwb_utils.create_identifier('softlink reader'), ...
        'description','softlink test'};
    f = nwb_file(settings{:});
    
%     source = neurodata.create_timeseries('TimeSeries', name, target)
%     source.set_data_as_remote_link(src_fname, 'acquisition/timeseries/'+src_name+'/data')
%     source.set_time([345])
%     source.finalize()
%     neurodata.close()
    
    source = f.make_group('<TimeSeries>', name, 'path', target);
    % source.set_data_as_remote_link(src_fname, 'acquisition/timeseries/'+src_name+'/data')
    extlink = sprintf('extlink:%s,%s', src_fname, ['acquisition/timeseries/', src_name, '/data']);
    source.set_dataset('data', extlink);
    source.set_dataset('timestamps', {345});  % put in cell array to make array in hdf5 file
%     source.finalize()
%     neurodata.close()
    f.close()
end

function create_softlink_source(fname, name, target)
    
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'start_time', 'Sat Jul 04 2015 3:14:16' ...
        'identifier', nwb_utils.create_identifier('softlink source'), ...
        'description','time series no data test'};
    f = nwb_file(settings{:});
    % source = neurodata.create_timeseries('TimeSeries', name, target)
    source = f.make_group('<TimeSeries>', name, 'path', target);
    % source.set_data([234], unit='parsec', conversion=1, resolution=1e-3)
    source.set_dataset('data', {234}, 'attrs', {'unit', 'parsec', ... 
        'conversion', 1, 'resolution', 1e-3});
    % source.set_time([123])
    source.set_dataset('timestamps', {123});
    % source.finalize()
    % neurodata.close()
    f.close()
end

test_softlink()
fprintf('%s PASSED\n', script_name);
end

