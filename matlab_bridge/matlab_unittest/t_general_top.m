function t_general_top(verbosity)


% TESTS top-level fields stored in general
% TESTS storing metadata from file
% TESTS 'Custom' tagging on custom attributes

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end


function test_field(fname, name)
    val = test_utils.verify_present(fname, 'general/', lower(name));
    if ~strcmp(val, name)
        test_utils.error('Checking metadata', 'field value incorrect');
    end
end

function test_general_top()
    create_general_top(fname)
    test_field(fname, 'DATA_COLLECTION'); 
    test_field(fname, 'EXPERIMENT_DESCRIPTION'); 
    test_field(fname, 'EXPERIMENTER'); 
    test_field(fname, 'INSTITUTION'); 
    test_field(fname, 'LAB'); 
    test_field(fname, 'NOTES'); 
    test_field(fname, 'PROTOCOL'); 
    test_field(fname, 'PHARMACOLOGY'); 
    test_field(fname, 'RELATED_PUBLICATIONS'); 
    test_field(fname, 'SESSION_ID'); 
    test_field(fname, 'SLICES'); 
    test_field(fname, 'STIMULUS'); 
    test_field(fname, 'SURGERY'); 
    test_field(fname, 'VIRUS'); 
    val = test_utils.verify_present(fname, 'general/', 'source_script'); 
    if length(val) < 1000
        test_utils.error('Checking metadata_from_file', 'unexpected field size')
    end
end
        
    % removing test for neurodata_type attribute custom on general/source_script, since its
    % not custom anymore
%     val = ut.verify_attribute_present(fname, 'general/source_script', 'neurodata_type')
%     if val != 'Custom' and val != b'Custom':
%         ut.error('Checking custom tag', 'neurodata_type incorrect')


function create_general_top(fname)
    settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
        'identifier', nwb_utils.create_identifier('general top test'), ...
        'description','test top-level elements in /general'};
    f = nwb_file(settings{:});
    
%     neurodata.set_metadata(DATA_COLLECTION, 'DATA_COLLECTION')
%     neurodata.set_metadata(EXPERIMENT_DESCRIPTION, 'EXPERIMENT_DESCRIPTION')
%     neurodata.set_metadata(EXPERIMENTER, 'EXPERIMENTER')
%     neurodata.set_metadata(INSTITUTION, 'INSTITUTION')
%     neurodata.set_metadata(LAB, 'LAB')
%     neurodata.set_metadata(NOTES, 'NOTES')
%     neurodata.set_metadata(PROTOCOL, 'PROTOCOL')
%     neurodata.set_metadata(PHARMACOLOGY, 'PHARMACOLOGY')
%     neurodata.set_metadata(RELATED_PUBLICATIONS, 'RELATED_PUBLICATIONS')
%     neurodata.set_metadata(SESSION_ID, 'SESSION_ID')
%     neurodata.set_metadata(SLICES, 'SLICES')
%     neurodata.set_metadata(STIMULUS, 'STIMULUS')
%     neurodata.set_metadata(SURGERY, 'SURGERY')
%     neurodata.set_metadata(VIRUS, 'VIRUS')
%     %
%     neurodata.set_metadata_from_file('source_script', __file__)
    %
    
    f.set_dataset('data_collection','DATA_COLLECTION'); 
    f.set_dataset('experiment_description','EXPERIMENT_DESCRIPTION');     
    f.set_dataset('experimenter','EXPERIMENTER'); 
    f.set_dataset('institution','INSTITUTION');      
    f.set_dataset('lab','LAB'); 
    f.set_dataset('notes','NOTES');     
    f.set_dataset('protocol','PROTOCOL'); 
    f.set_dataset('pharmacology','PHARMACOLOGY'); 
    f.set_dataset('related_publications', 'RELATED_PUBLICATIONS'); 
    f.set_dataset('session_id','SESSION_ID');     
    f.set_dataset('slices','SLICES'); 
    f.set_dataset('stimulus','STIMULUS');      
    f.set_dataset('surgery','SURGERY'); 
    f.set_dataset('virus', 'VIRUS'); 
    
    % f.neurodata.set_metadata_from_file('source_script', __file__)
    f.set_dataset('source_script', nwb_utils.load_file(script_name));

    % neurodata.close()
    f.close()
end

test_general_top()
fprintf('%s PASSED\n', script_name);
end

