function t_general_patch(verbosity)

% TESTS fields stored in general/intracellular_ephys

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

function test_field(fname, name, subdir)
    val = test_utils.verify_present(fname, ['general/intracellular_ephys/', subdir, '/'], lower(name));
    if ~strcmp(val, name)
        test_utils.error('Checking metadata', 'field value incorrect');
    end
end

function test_general_intra()
    create_general_intra(fname)
    %
    val = test_utils.verify_present(fname, 'general/intracellular_ephys/', 'intra_custom');
    if ~strcmp(val, 'INTRA_CUSTOM')
        test_utils.error('Checking custom', 'Field value incorrect')
    end
    %

    test_field(fname, 'DESCRIPTION', 'p1')
    test_field(fname, 'FILTERING', 'p1')
    test_field(fname, 'DEVICE', 'p1')
    test_field(fname, 'LOCATION', 'p1')
    test_field(fname, 'RESISTANCE', 'p1')
    test_field(fname, 'SLICE', 'p1')
    test_field(fname, 'SEAL', 'p1')
    test_field(fname, 'INITIAL_ACCESS_RESISTANCE', 'p1')
    test_field(fname, 'INTRA_ELECTRODE_CUSTOM', 'p1')
    %
    test_field(fname, 'DESCRIPTION', 'e2')
    test_field(fname, 'FILTERING', 'e2')
    test_field(fname, 'DEVICE', 'e2')
    test_field(fname, 'LOCATION', 'e2')
    test_field(fname, 'RESISTANCE', 'e2')
    test_field(fname, 'SLICE', 'e2')
    test_field(fname, 'SEAL', 'e2')
    test_field(fname, 'INITIAL_ACCESS_RESISTANCE', 'e2')
    test_field(fname, 'INTRA_ELECTRODE_CUSTOM', 'e2')
end

function create_general_intra(fname)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'identifier', nwb_utils.create_identifier('general intracellular test'), ...
        'description','test elements in /general/intracellular_ephys'};
    f = nwb_file(settings{:});
        
    %
    % neurodata.set_metadata(INTRA_CUSTOM('intra_custom'), 'INTRA_CUSTOM');
    
    g = f.make_group('intracellular_ephys');
    g.set_custom_dataset('intra_custom', 'INTRA_CUSTOM');
    
    %
%     neurodata.set_metadata(INTRA_ELECTRODE_DESCRIPTION('p1'), 'DESCRIPTION')
%     neurodata.set_metadata(INTRA_ELECTRODE_FILTERING('p1'), 'FILTERING')
%     neurodata.set_metadata(INTRA_ELECTRODE_DEVICE('p1'), 'DEVICE')
%     neurodata.set_metadata(INTRA_ELECTRODE_LOCATION('p1'), 'LOCATION')
%     neurodata.set_metadata(INTRA_ELECTRODE_RESISTANCE('p1'), 'RESISTANCE')
%     neurodata.set_metadata(INTRA_ELECTRODE_SEAL('p1'), 'SEAL')
%     neurodata.set_metadata(INTRA_ELECTRODE_SLICE('p1'), 'SLICE')
%     neurodata.set_metadata(INTRA_ELECTRODE_INIT_ACCESS_RESISTANCE('p1'), 'INITIAL_ACCESS_RESISTANCE')
%     neurodata.set_metadata(INTRA_ELECTRODE_CUSTOM('p1', 'intra_electrode_custom'), 'INTRA_ELECTRODE_CUSTOM')
    
    p1 = g.make_group('<electrode_X>', 'p1');
    p1.set_dataset('description', 'DESCRIPTION');
    p1.set_dataset('filtering', 'FILTERING');
    p1.set_dataset('device','DEVICE');
    p1.set_dataset('location','LOCATION');
    p1.set_dataset('resistance','RESISTANCE');
    p1.set_dataset('seal','SEAL');
    p1.set_dataset('slice','SLICE');
    p1.set_dataset('initial_access_resistance','INITIAL_ACCESS_RESISTANCE');
    p1.set_custom_dataset('intra_electrode_custom','INTRA_ELECTRODE_CUSTOM');
    %
%     neurodata.set_metadata(INTRA_ELECTRODE_DESCRIPTION('e2'), 'DESCRIPTION')
%     neurodata.set_metadata(INTRA_ELECTRODE_FILTERING('e2'), 'FILTERING')
%     neurodata.set_metadata(INTRA_ELECTRODE_DEVICE('e2'), 'DEVICE')
%     neurodata.set_metadata(INTRA_ELECTRODE_LOCATION('e2'), 'LOCATION')
%     neurodata.set_metadata(INTRA_ELECTRODE_RESISTANCE('e2'), 'RESISTANCE')
%     neurodata.set_metadata(INTRA_ELECTRODE_SEAL('e2'), 'SEAL')
%     neurodata.set_metadata(INTRA_ELECTRODE_SLICE('e2'), 'SLICE')
%     neurodata.set_metadata(INTRA_ELECTRODE_INIT_ACCESS_RESISTANCE('e2'), 'INITIAL_ACCESS_RESISTANCE')
%     neurodata.set_metadata(INTRA_ELECTRODE_CUSTOM('e2', 'intra_electrode_custom'), 'INTRA_ELECTRODE_CUSTOM')
    %
    e2 = g.make_group('<electrode_X>', 'e2');
    e2.set_dataset('description', 'DESCRIPTION');
    e2.set_dataset('filtering', 'FILTERING');
    e2.set_dataset('device','DEVICE');
    e2.set_dataset('location','LOCATION');
    e2.set_dataset('resistance','RESISTANCE');
    e2.set_dataset('seal','SEAL');
    e2.set_dataset('slice','SLICE');
    e2.set_dataset('initial_access_resistance','INITIAL_ACCESS_RESISTANCE');
    e2.set_custom_dataset('intra_electrode_custom','INTRA_ELECTRODE_CUSTOM');
    
    % neurodata.close()
    f.close()
end

test_general_intra()
fprintf('%s PASSED\n', script_name);
end

