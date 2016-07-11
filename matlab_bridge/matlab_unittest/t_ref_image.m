function t_ref_image(verbosity)

% TESTS storage of reference image

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end


function test_refimage_series()
    name = 'refimage';
    create_refimage(fname, name)
    val = test_utils.verify_present(fname, 'acquisition/images/', name);
    %if len(val) != 6:
    if length(val) ~= 5
        test_utils.error('Checking ref image contents', 'wrong dimension')
    end
    val = test_utils.verify_attribute_present(fname, ['acquisition/images/', name], 'format');
    if ~strcmp(val, 'raw')
        test_utils.error('Checking ref image format', 'Wrong value')
    end
    val = test_utils.verify_attribute_present(fname, ['acquisition/images/',name], 'description');
    if ~strcmp(val, 'test')
        test_utils.error('Checking ref image description', 'Wrong value')
    end
end

function create_refimage(fname, name)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'start_time', 'Sat Jul 04 2015 3:14:16' ...
        'identifier', nwb_utils.create_identifier('reference image test'), ...
        'description','reference image test'};
    f = nwb_file(settings{:});
    
    % neurodata.create_reference_image([1,2,3,4,5], name, 'raw', 'test')
    f.set_dataset('<image_X>', [1,2,3,4,5], 'dtype', 'uint8', 'name', name, 'attrs', { ...
        'description', 'test', 'format', 'raw'});
        
    f.close()
end

test_refimage_series()
fprintf('%s PASSED\n', script_name);
end

