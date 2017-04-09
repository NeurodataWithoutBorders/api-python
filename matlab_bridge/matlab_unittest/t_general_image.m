function t_general_image(verbosity)

% TESTS fields stored in general/optophysiology

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

% make manifold 3-d array global so can use for storing and testing
% old version, incorrect - does not match Python version dimensions
% man_v1 = [1 2 3 ; 2 3 4];
% man_v1(:,:,2) = [3,4,5 ; 4,5,6];

% build 3d array equivalant to following in Python
% [[[1,2,3],[2,3,4]],[[3,4,5],[4,5,6]]]
man1 = [1 2; 3 4];
man2 = [2 3; 4 5];
man3 = [3 4; 5 6];
manifold = cat(3, man1, man2, man3); 



function test_field(fname, name, subdir)
    val = test_utils.verify_present(fname, ['general/optophysiology/', subdir, '/'], lower(name));
    if ~strcmp(val, name)
        test_utils.error('Checking metadata', 'field value incorrect');
    end
end

function test_general_intra()
    create_general_intra(fname)
    %
    val = test_utils.verify_present(fname, 'general/optophysiology/', 'image_custom');
    if ~strcmp(val, 'IMAGE_CUSTOM')
    %if val != 'IMAGE_CUSTOM' and val != b'IMAGE_CUSTOM':
        test_utils.error('Checking custom', 'Field value incorrect')
    end

    test_field(fname, 'DESCRIPTION', 'p1')
    test_field(fname, 'DEVICE', 'p1')
    test_field(fname, 'EXCITATION_LAMBDA', 'p1')
    test_field(fname, 'IMAGE_SITE_CUSTOM', 'p1')
    test_field(fname, 'IMAGING_RATE', 'p1')
    test_field(fname, 'INDICATOR', 'p1')
    test_field(fname, 'LOCATION', 'p1')
    val = test_utils.verify_present(fname, 'general/optophysiology/p1/', 'manifold');
    % convert from row major order to column major order
    % not needed, done in test_utils.verify_present
    % val2 = nwb_utils.h5reshape(val);
    % if length(val) ~= 2 || len(val(1)) ~= 2 || len(val(1, 1)) ~= 3
    if ~isequal(val, manifold)
        test_utils.error('Checking manifold', 'value stored does not match')
    end
    val = test_utils.verify_present(fname, 'general/optophysiology/p1/red/', 'description');
    if ~strcmp(val, 'DESCRIPTION')
        test_utils.error('Checking metadata', 'field value incorrect')
    end
    val = test_utils.verify_present(fname, 'general/optophysiology/p1/green/', 'description');
    if ~strcmp(val, 'DESCRIPTION')
        test_utils.error('Checking metadata', 'field value incorrect')
    end
    val = test_utils.verify_present(fname, 'general/optophysiology/p1/red/', 'emission_lambda');
    if ~strcmp(val, 'CHANNEL_LAMBDA')
        test_utils.error('Checking metadata', 'field value incorrect')
    end
    val = test_utils.verify_present(fname, 'general/optophysiology/p1/green/', 'emission_lambda');
    if ~strcmp(val, 'CHANNEL_LAMBDA')
        test_utils.error('Checking metadata', 'field value incorrect')
    end
end


function create_general_intra(fname)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'identifier', nwb_utils.create_identifier('general optophysiology test'), ...
        'description','test elements in /general/optophysiology'};
    f = nwb_file(settings{:});
    %
    %neurodata.set_metadata(IMAGE_CUSTOM('image_custom'), 'IMAGE_CUSTOM')
    g = f.make_group('optophysiology');
    g.set_custom_dataset('image_custom', 'IMAGE_CUSTOM');
    %
    % neurodata.set_metadata(IMAGE_SITE_DESCRIPTION('p1'), 'DESCRIPTION')
    p1 = g.make_group('<imaging_plane_X>', 'p1');
    p1.set_dataset('description', 'DESCRIPTION');
    
    % MANUAL CHECK
    % try storing string - -type system should balk
    %neurodata.set_metadata(IMAGE_SITE_MANIFOLD('p1'), 'MANIFOLD')
    
    
    % neurodata.set_metadata(IMAGE_SITE_MANIFOLD('p1'), [[[1,2,3],[2,3,4]],[[3,4,5],[4,5,6]]])
%     neurodata.set_metadata(IMAGE_SITE_INDICATOR('p1'), 'INDICATOR')
%     neurodata.set_metadata(IMAGE_SITE_EXCITATION_LAMBDA('p1'), 'EXCITATION_LAMBDA')
%     neurodata.set_metadata(IMAGE_SITE_CHANNEL_LAMBDA('p1', 'red'), 'CHANNEL_LAMBDA')
%     neurodata.set_metadata(IMAGE_SITE_CHANNEL_DESCRIPTION('p1', 'red'), 'DESCRIPTION')
%     neurodata.set_metadata(IMAGE_SITE_CHANNEL_LAMBDA('p1', 'green'), 'CHANNEL_LAMBDA')
%     neurodata.set_metadata(IMAGE_SITE_CHANNEL_DESCRIPTION('p1', 'green'), 'DESCRIPTION')
%     neurodata.set_metadata(IMAGE_SITE_IMAGING_RATE('p1'), 'IMAGING_RATE')
%     neurodata.set_metadata(IMAGE_SITE_LOCATION('p1'), 'LOCATION')
%     neurodata.set_metadata(IMAGE_SITE_DEVICE('p1'), 'DEVICE')
%     neurodata.set_metadata(IMAGE_SITE_CUSTOM('p1', 'image_site_custom'), 'IMAGE_SITE_CUSTOM')
    %
    
    % using h5reshape causes this to fail, not sure why
    %p1.set_dataset('manifold', nwb_utils.h5reshape(manifold));
    p1.set_dataset('manifold', manifold);
    p1.set_dataset('indicator', 'INDICATOR');
    p1.set_dataset('excitation_lambda','EXCITATION_LAMBDA');
    p1_red = p1.make_group('<channel_X>', 'red');
    p1_red.set_dataset('emission_lambda','CHANNEL_LAMBDA');
    p1_red.set_dataset('description','DESCRIPTION');
    p1_green = p1.make_group('<channel_X>', 'green');
    p1_green.set_dataset('emission_lambda','CHANNEL_LAMBDA');
    p1_green.set_dataset('description','DESCRIPTION');
    p1.set_dataset('imaging_rate', 'IMAGING_RATE');
    p1.set_dataset('location', 'LOCATION');
    p1.set_dataset('device', 'DEVICE');
    p1.set_custom_dataset('image_site_custom', 'IMAGE_SITE_CUSTOM');
   
    
    % neurodata.close()
    f.close()
end

test_general_intra()
fprintf('%s PASSED\n', script_name);
end
