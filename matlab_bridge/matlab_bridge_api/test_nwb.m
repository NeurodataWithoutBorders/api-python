function [ result ] = test_nwb( )
% - tests calling h5gate matlab interface
    OUTPUT_DIR = './'; % '../created_nwb_files/';
    file_name = 'test_ml.nwb';
    settings = { ...
        'file_name', [OUTPUT_DIR file_name], ...
        'identifier', char(py.nwb.nwb_utils.create_identifier('matlab test')), ...
        'mode', 'w', ...
        'start_time', '2016-04-07T03:16:03.604121', ...
        'description','Test file created using matlab bridge'};
    f = nwb_file(settings{:});
    % f.set_dataset('experimenter', 'Jeff Teeters');
    f.set_dataset('experimenter', 'Jeff Teeters');
    g = f.make_group('<electrode_group_X>', 'shank_01','attrs', {'happy', 'day'});
    g.set_dataset('description', 'Test shank, with four recording sites');
    m = f.make_group('<Module>', 'shank_01', 'attrs', {'Its', 'working'} );
    lfp = m.make_group('LFP');
    ts = lfp.make_group('<ElectricalSeries>', 'LFP_Timeseries');
    ts.set_attr('source', 'moms backyard');
    ts.set_attr('source2', 'moms new backyard with bunnies');
    data = [ 1.2 1.3 1.4; 1.5 1.6 1.7 ];
    % data = zeros(10000, 1);
    times = [ 0.12, 0.13, 0.14, 0.15, 0.16 ];
    d = ts.set_dataset('data', data, 'compress', true);
    d.set_attr('unit', 'light_years');
    ts.set_dataset('timestamps', times);
    ts.set_dataset('num_samples', int64(5));
    % make some custom datasets
    g = f.make_custom_group('custom_subject_info', 'path', '/', 'attrs', {'upc', 'polly45'});
    g.set_custom_dataset('dog_breed', 'Saint Bernard');
    g.make_custom_group('lab_cats', 'attrs', {'info', 'this for help with cats', 'more_info', 'many more cats'});
    f.set_custom_dataset('custom_dataset', 'blue_sky', 'path', '/cust_info', 'attrs', {'info', 'about the blue sky'});
    g2 = f.get_node('/general/experimenter');
    fprintf('found ml_node, path is %s\n',char(g2.fg_node.full_path)); 
    f.close();
    fprintf('done');
    result = 0;
end

