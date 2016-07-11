function t_general_ephys(verbosity)

% TESTS fields stored in general/extracellular_ephys
script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

function test_field(fname, name, subdir)
    val = test_utils.verify_present(fname, ['general/extracellular_ephys/', subdir, '/'], lower(name));
    if ~strcmp(val, name)
        test_utils.error('Checking metadata', 'field value incorrect');
    end
end

function test_general_extra()

    create_general_extra(fname);
    %
    val = test_utils.verify_present(fname, 'general/extracellular_ephys', 'electrode_map');
    shape = size(val);
    if shape(1) ~= 2 && shape(2) ~= 3  % length(val) ~= 2 && length(val[0]) ~= 3:
        test_utils.error('Checking electrode map', 'incorrect dimensions');
    end
    %
    val = test_utils.verify_present(fname, 'general/extracellular_ephys', 'electrode_group');
    if length(val) ~= 2
        test_utils.error('Checking electrode group', 'incorrect dimensions');
    end
    if ~strcmp(val(1), 'p1')
        test_utils.error('Checking electrode group p1', 'incorrect values');
    end
    if ~strcmp(val(2), 'p2')
        test_utils.error('Checking electrode group p2', 'incorrect values');
    end
    %
    val = test_utils.verify_present(fname, 'general/extracellular_ephys', 'impedance');
    if length(val) ~= 2
        test_utils.error('Checking electrode impedance', 'incorrect dimensions');
    end
    %
    val = test_utils.verify_present(fname, 'general/extracellular_ephys/', 'filtering');
    if ~strcmp(val, 'EXTRA_FILTERING')
        test_utils.error('Checking filtering', 'Field value incorrect');
    end
    %
    val = test_utils.verify_present(fname, 'general/extracellular_ephys/', 'EXTRA_CUSTOM');
    if ~strcmp(val, 'EXTRA_CUSTOM')
        test_utils.error('Checking custom', 'Field value incorrect');
    end
%

    test_field(fname, 'DESCRIPTION', 'p1');
    test_field(fname, 'LOCATION', 'p1');
    test_field(fname, 'DEVICE', 'p1');
    test_field(fname, 'EXTRA_SHANK_CUSTOM', 'p1');
    test_field(fname, 'DESCRIPTION', 'p2');
    test_field(fname, 'LOCATION', 'p2');
    test_field(fname, 'DEVICE', 'p2');
    test_field(fname, 'EXTRA_SHANK_CUSTOM', 'p2');
end


function create_general_extra(fname)
    
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'identifier', nwb_utils.create_identifier('general extracellular test'), ...
        'description','test elements in /general/extracellular_ephys'};
    f = nwb_file(settings{:});
%     neurodata.set_metadata(EXTRA_ELECTRODE_MAP, [[1,1,1], [1,2,3]])
%     neurodata.set_metadata(EXTRA_ELECTRODE_GROUP, ['p1', 'p2'])
%     neurodata.set_metadata(EXTRA_IMPEDANCE, [1.0e6, 2.0e6])
%     neurodata.set_metadata(EXTRA_FILTERING, 'EXTRA_FILTERING')
%     neurodata.set_metadata(EXTRA_CUSTOM('EXTRA_CUSTOM'), 'EXTRA_CUSTOM')

    g = f.make_group('extracellular_ephys');
    g.set_dataset('electrode_map', nwb_utils.h5reshape([1,1,1; 1,2,3]));
    g.set_dataset('electrode_group', {'p1', 'p2'});
    g.set_dataset('impedance', [1.0e6, 2.0e6]);
    g.set_dataset('filtering', 'EXTRA_FILTERING');
    g.set_custom_dataset('EXTRA_CUSTOM', 'EXTRA_CUSTOM');

%     neurodata.set_metadata(EXTRA_SHANK_DESCRIPTION('p1'), 'DESCRIPTION')
%     neurodata.set_metadata(EXTRA_SHANK_LOCATION('p1'), 'LOCATION')
%     neurodata.set_metadata(EXTRA_SHANK_DEVICE('p1'), 'DEVICE')
%     neurodata.set_metadata(EXTRA_SHANK_CUSTOM('p1', 'extra_shank_custom'), 'EXTRA_SHANK_CUSTOM')
    
    p1 = g.make_group('<electrode_group_X>', 'p1');
    p1.set_dataset('description', 'DESCRIPTION');
    p1.set_dataset('location', 'LOCATION');
    p1.set_dataset('device', 'DEVICE');
    p1.set_custom_dataset('extra_shank_custom', 'EXTRA_SHANK_CUSTOM');
    %
    
%     neurodata.set_metadata(EXTRA_SHANK_DESCRIPTION('p2'), 'DESCRIPTION')
%     neurodata.set_metadata(EXTRA_SHANK_LOCATION('p2'), 'LOCATION')
%     neurodata.set_metadata(EXTRA_SHANK_DEVICE('p2'), 'DEVICE')
%     neurodata.set_metadata(EXTRA_SHANK_CUSTOM('p2', 'extra_shank_custom'), 'EXTRA_SHANK_CUSTOM')
    %
    
    p2 = g.make_group('<electrode_group_X>', 'p2');
    p2.set_dataset('description', 'DESCRIPTION');
    p2.set_dataset('location', 'LOCATION');
    p2.set_dataset('device', 'DEVICE');
    p2.set_custom_dataset('extra_shank_custom', 'EXTRA_SHANK_CUSTOM');
    
    % neurodata.close()
    f.close();
end

test_general_extra();
fprintf('%s PASSED\n', script_name);
end

