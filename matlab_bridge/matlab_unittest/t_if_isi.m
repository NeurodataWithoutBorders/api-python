function t_if_isi(verbosity)

% TESTS storage of retonotopic imaging data

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

function test_axis(fname, iname, num)
    val = test_utils.verify_present(fname, iname, ['axis_', num, '_phase_map']);
    shape = size(val);
    if shape(1) ~= 2 || shape(2) ~= 3 % len(val) ~= 2 || length(val(1)) ~= 3
        test_utils.error('Checking axis-'+num, 'wrong dimension')
    end
    if num == '1'
        if val(1,1) ~= 1.0
            test_utils.error('Checking axis-''+num, ''wrong contents')
        end
    elseif num == '2'
        if val(1,1) ~= 3.0
            test_utils.error('Checking axis-'+num+' contents', 'wrong contents')
        end
    end
    val = test_utils.verify_attribute_present(fname, [iname, '/axis_', num, '_phase_map'], 'unit');
    if ~strcmp(val, 'degrees')
        test_utils.error('Checking axis-'+num+' unit', 'Wrong value')
    end
    val = test_utils.verify_attribute_present(fname, [iname, '/axis_', num, '_phase_map'], 'dimension');
    if val(1) ~= 2 || val(2) ~= 3
        test_utils.error('Double-checking axis-'+num+' dimension', 'Wrong value')
    end
    val = test_utils.verify_attribute_present(fname, [iname, '/axis_', num, '_phase_map'], 'field_of_view');
    if val(1) ~= .1 || val(2) ~= .1
        test_utils.error('Checking axis-'+num+' field-of-view', 'Wrong value')
    end
    % now check power map. it only exists for axis 1
    if num == '1'
        val = test_utils.verify_present(fname, iname, ['axis_', num, '_phase_map']);
        shape = size(val);
        if shape(1) ~= 2 || shape(2) ~= 3   % len(val) ~= 2 || len(val(1)) ~= 3
            test_utils.error(['Checking axis-', num, ' power map'], 'wrong dimension')
        end
        val = test_utils.verify_attribute_present(fname, [iname, '/axis_', num, '_power_map'], 'dimension');
        if val(1) ~= 2 || val(2) ~= 3
            test_utils.error(['Double-checking axis-', num, '-power dimension'], 'Wrong value')
        end
        val = test_utils.verify_attribute_present(fname, [iname, '/axis_', num, '_power_map'], 'field_of_view');
        if val(1) ~= .1 || val(2) ~= .1
            test_utils.error(['Checking axis-', num, '-power field-of-view'], 'Wrong value')
        end
    end
end

function test_image(fname, iname, img)
    val = test_utils.verify_present(fname, iname, img);
    shape = size(val);
    if shape(1) ~= 2 || shape(2) ~= 3  % len(val) ~= 2 || len(val(1)) ~= 3
        test_utils.error(['Checking image ', img], 'wrong dimension');
    end
    if val(2,2) ~= 144
        test_utils.error(['Checking image ', img], 'wrong contents');
    end
    val = test_utils.verify_attribute_present(fname, [iname, '/', img], 'format');
    if ~strcmp(val, 'raw')
        test_utils.error(['Checking image ', img, ' format'], 'wrong contents')
    end
    val = test_utils.verify_attribute_present(fname, [iname, '/', img], 'dimension');
    if length(val) ~= 2 || val(1) ~= 2 || val(2) ~= 3
        test_utils.error(['Checking image ',img,' dimension'], 'wrong contents')
    end
    val = test_utils.verify_attribute_present(fname, [iname,'/',img], 'bits_per_pixel');
    if val ~= 8
        test_utils.error(['Checking image ',img,' bpp'], 'wrong contents')
    end
end

function test_sign_map(fname, iname)
    val = test_utils.verify_present(fname, iname, 'sign_map');
    shape = size(val);
    if shape(1) ~= 2 || shape(2) ~= 3  % len(val) ~= 2 || len(val(1)) ~= 3
        test_utils.error('Checking sign map', 'wrong dimension')
    end
    if val(2, 2) ~= -.5
        test_utils.error('Checking sign map', 'wrong content')
    end
    val = test_utils.verify_attribute_present(fname, [iname, '/sign_map'], 'dimension');
    if length(val) ~= 2 || val(1) ~= 2 || val(2) ~= 3
        test_utils.error('Checking sign map dimension', 'wrong contents')
    end
end


function test_isi_iface()
    name = 'test_module';
    iname = ['processing/', name, '/ImagingRetinotopy'];
    create_isi_iface(fname, name);

    test_axis(fname, iname, '1');
    test_axis(fname, iname, '2');
    val = test_utils.verify_present(fname, iname, 'axis_descriptions');
    shape = size(val);
    if shape(1) ~= 1 || shape(2) ~= 2 %  in matlab, 1-d array has dims [1 n] ; len(val) ~= 2
        test_utils.error('Checking axis_description', 'wrong dimension')
    end
    if ~strcmp(val(1), 'altitude') || ~strcmp(val(2), 'azimuth')
        test_utils.error('Checking axis_description', 'wrong contents')
    end
    test_image(fname, iname, 'vasculature_image');
    test_image(fname, iname, 'focal_depth_image');
    test_sign_map(fname, iname);
end


% TODO sign map
% TODO dimension of response axes

function create_isi_iface(fname, name)
    
    settings = { ...
        'file_name', fname, ...
        'mode', 'w', ...
        'verbosity', verbosity, ...
        'identifier', nwb_utils.create_identifier('reference image test'), ...
        'description','isi reference image test'...
        };
    f = nwb_file(settings{:});
    
%     module = neurodata.create_module(name)
%     iface = module.create_interface('ImagingRetinotopy')
%     iface.add_axis_1_phase_map([[1.0, 1.1, 1.2],[2.0,2.1,2.2]], 'altitude', .1, .1)
%     iface.add_axis_2_phase_map([[3.0, 3.1, 3.2],[4.0,4.1,4.2]], 'azimuth', .1, .1, unit='degrees')
%     iface.add_axis_1_power_map([[0.1, 0.2, 0.3],[0.4, 0.5, 0.6]], .1, .1)
%     iface.add_sign_map([[-.1, .2, -.3],[.4,-.5,.6]])
%     iface.add_vasculature_image([[1,0,129],[2,144,0]], height=.22, width=.35)
%     iface.add_focal_depth_image([[1,0,129],[2,144,0]], bpp=8)
%     iface.finalize()
%     module.finalize()
    
    module = f.make_group('<Module>', name);
    iface = module.make_group('ImagingRetinotopy');
    % iface.add_axis_1_phase_map([[1.0, 1.1, 1.2],[2.0,2.1,2.2]], 'altitude', .1, .1)
    % cast dimensions as int32.  For some reason, int64 throws a python
    % error.  int32 seems to be stored as int64 in the hdf5 file.
    iface.set_dataset('axis_1_phase_map', [1.0, 1.1, 1.2; 2.0,2.1,2.2], 'attrs', ...
        {'dimension', int32([2,3]), 'field_of_view', [0.1, 0.1], 'unit', 'degrees'});
    % above was: {'dimension', [2,3], 'field_of_view', [0.1, 0.1], 'unit', 'degrees', 't2d', [2,3; 5,7]});
    % not sure what 't2d' is.  That's not in the Python version of the test

    % iface.add_axis_2_phase_map([[3.0, 3.1, 3.2],[4.0,4.1,4.2]], 'azimuth', .1, .1, unit='degrees')
    iface.set_dataset('axis_2_phase_map', [3.0, 3.1, 3.2; 4.0,4.1,4.2], 'attrs', ...
        {'dimension', int32([2,3]), 'field_of_view', [0.1, 0.1], 'unit', 'degrees'});

    iface.set_dataset('axis_descriptions', {'altitude', 'azimuth'});
    
    % iface.add_axis_1_power_map([[0.1, 0.2, 0.3],[0.4, 0.5, 0.6]], .1, .1)
    iface.set_dataset('axis_1_power_map', [0.1, 0.2, 0.3; 0.4, 0.5, 0.6], 'attrs', ...
        {'dimension', int32([2,3]), 'field_of_view', [0.1, 0.1]});
        
    % iface.add_sign_map([[-.1, .2, -.3],[.4,-.5,.6]])
    iface.set_dataset('sign_map', [-.1, .2, -.3; .4,-.5,.6], 'attrs', ...
        { 'dimension', int32([2,3])});
        
    % iface.add_vasculature_image([[1,0,129],[2,144,0]], height=.22, width=.35)
    % for some reason, uint16 is being passed to Python as int64. todo: fix
    iface.set_dataset('vasculature_image', uint16([1,0,129; 2,144,0]), 'attrs', ...
        {'field_of_view', [0.22, 0.35], 'bits_per_pixel', int32(8), 'dimension', int32([2,3]), 'format', 'raw'});
        
    % iface.add_focal_depth_image([[1,0,129],[2,144,0]], bpp=8)
    iface.set_dataset('focal_depth_image', uint16([1,0,129; 2,144,0]), 'attrs', ...
        {'bits_per_pixel',int32(8), 'dimension',int32([2,3]), 'format', 'raw'});
        
    % iface.finalize()
    % module.finalize()
    
    % neurodata.close()
    f.close()
end

test_isi_iface()
fprintf('%s PASSED\n', script_name);
end

