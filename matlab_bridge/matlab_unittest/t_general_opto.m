function t_general_opto(verbosity)

% TESTS fields stored in general/optogenetics

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end


function test_field(fname, name, subdir)
    val = test_utils.verify_present(fname, ['general/optogenetics/', subdir, '/'], lower(name));
    if ~strcmp(val, name)
        test_utils.error('Checking metadata', 'field value incorrect');
    end
end


function test_general_optogen()
    create_general_optogen(fname)
    %
    val = test_utils.verify_present(fname, 'general/optogenetics/', 'optogen_custom');
    if ~strcmp(val, 'OPTOGEN_CUSTOM')
        test_utils.error('Checking custom', 'Field value incorrect')
    end
    %

    test_field(fname, 'DESCRIPTION', 'p1');
    %test_field(fname, 'DESCRIPTIONx', 'p1')
    %test_field(fname, 'DESCRIPTION', 'p1x')
    test_field(fname, 'DEVICE', 'p1');
%    test_field(fname, 'LAMBDA', 'p1')
    test_field(fname, 'EXCITATION_LAMBDA', 'p1');
    test_field(fname, 'LOCATION', 'p1');
    val = test_utils.verify_present(fname, 'general/optogenetics/p1/', 'optogen_site_custom');
    if ~strcmp(val, 'OPTOGEN_SITE_CUSTOM')
        test_utils.error('Checking metadata', 'field value incorrect')
    end
end


function create_general_optogen(fname)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'identifier', nwb_utils.create_identifier('metadata optogenetic test'), ...
        'description','test elements in /general/optophysiology'};
    f = nwb_file(settings{:});
    
%     neurodata.set_metadata(OPTOGEN_CUSTOM('optogen_custom'), 'OPTOGEN_CUSTOM')
%     %
%     neurodata.set_metadata(OPTOGEN_SITE_DESCRIPTION('p1'), 'DESCRIPTION')
%     neurodata.set_metadata(OPTOGEN_SITE_DEVICE('p1'), 'DEVICE')
%     neurodata.set_metadata(OPTOGEN_SITE_LAMBDA('p1'), 'LAMBDA')
%     neurodata.set_metadata(OPTOGEN_SITE_LOCATION('p1'), 'LOCATION')
%     neurodata.set_metadata(OPTOGEN_SITE_CUSTOM('p1', 'optogen_site_custom'), 'OPTOGEN_SITE_CUSTOM')
    %
    
    g = f.make_group('optogenetics');
    g.set_custom_dataset('optogen_custom', 'OPTOGEN_CUSTOM');
    
    p1 = g.make_group('<site_X>', 'p1');
    p1.set_dataset('description','DESCRIPTION');
    p1.set_dataset('device', 'DEVICE');
    p1.set_dataset('excitation_lambda','EXCITATION_LAMBDA');
    p1.set_dataset('location', 'LOCATION');
    p1.set_custom_dataset('optogen_site_custom', 'OPTOGEN_SITE_CUSTOM');
    
    % neurodata.close()
    f.close()
end

test_general_optogen()
fprintf('%s PASSED\n', script_name);
end


