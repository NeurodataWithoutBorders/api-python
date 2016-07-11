function t_general_species(verbosity)

% TESTS fields stored in general/subject

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end
        
function test_field(fname, name)
    val = test_utils.verify_present(fname, 'general/subject/', lower(name));
    if ~strcmp(val, name)
        test_utils.error('Checking metadata', 'field value incorrect');
    end
end

function test_general_subject()
    create_general_subject(fname);
    val = test_utils.verify_present(fname, 'general/subject/', 'description');
    if ~strcmp(val, 'SUBJECT')
        ut.error('Checking metadata', 'field value incorrect')
    end
    test_field(fname, 'SUBJECT_ID');
    test_field(fname, 'SPECIES');
    test_field(fname, 'GENOTYPE');
    test_field(fname, 'SEX');
    test_field(fname, 'AGE');
    test_field(fname, 'WEIGHT');
end


function create_general_subject(fname)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'identifier', nwb_utils.create_identifier('general subject test'), ...
        'description','test elements in /general/subject'};
    f = nwb_file(settings{:});
    
    %
%     neurodata.set_metadata(SUBJECT, 'SUBJECT')
%     neurodata.set_metadata(SUBJECT_ID, 'SUBJECT_ID')
%     neurodata.set_metadata(SPECIES, 'SPECIES')
%     neurodata.set_metadata(GENOTYPE, 'GENOTYPE')
%     neurodata.set_metadata(SEX, 'SEX')
%     neurodata.set_metadata(AGE, 'AGE')
%     neurodata.set_metadata(WEIGHT, 'WEIGHT')
    %
    
    g = f.make_group('subject');
    g.set_dataset('description', 'SUBJECT');
    g.set_dataset('subject_id', 'SUBJECT_ID');
    g.set_dataset('species', 'SPECIES');
    g.set_dataset('genotype', 'GENOTYPE');
    g.set_dataset('sex', 'SEX');
    g.set_dataset('age', 'AGE');
    g.set_dataset('weight', 'WEIGHT');
    
    % neurodata.close()
    f.close()
end

test_general_subject()
fprintf('%s PASSED\n', script_name);
end

