function t_epoch_tag(verbosity)

% create two epochs, add different subset of tags to each
% verify main epoch folder has tag attribute that contains
%   exactly the unique tags of each epoch and that each
%   epoch contains the assigned tags
    
script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end
    
settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
    'identifier', nwb_utils.create_identifier('Epoch tags'), ...
    'description','softlink test'};
f = nwb_file(settings{:});

tags = {'tag-a', 'tag-b', 'tag-c'};

% epoch1 = borg.create_epoch('epoch-1', 0, 3);

epoch1 = f.make_group('<epoch_X>', 'epoch-1');
epoch1.set_dataset('start_time', 0);
epoch1.set_dataset('stop_time', 3);

% for i in range(len(tags)-1):
%     epoch1.add_tag(tags[i+1])
epoch1.set_dataset('tags', tags(2:end));

% epoch2 = borg.create_epoch('epoch-2', 1, 4);
epoch2 = f.make_group('<epoch_X>', 'epoch-2');
epoch2.set_dataset('start_time', 1);
epoch2.set_dataset('stop_time', 4);

% for i in range(len(tags)-1):
%     epoch2.add_tag(tags[i])
epoch2.set_dataset('tags', tags(1:2));

f.close()

% this test modified because tags are stored as dataset rather than attribute
% tags = ut.verify_attribute_present(fname, 'epochs/epoch-1', 'tags');
stored_tags = test_utils.verify_present(fname, 'epochs/epoch-1', 'tags');
for i = 2:length(tags)
    if ~any(strcmp(tags(i), stored_tags))
        test_utils.error('Verifying epoch tag content', 'epoch-1: all tags not present')
    end
end

% tags = ut.verify_attribute_present(fname, 'epochs/epoch-2', 'tags');
stored_tags = test_utils.verify_present(fname, 'epochs/epoch-2', 'tags');
for i = 1:length(tags)-1  % in range(len(tags)-1):
    if ~any(strcmp(tags(i), stored_tags))  % tags[i] not in tags:
        test_utils.error('Verifying epoch tag content', 'epoch-2: all tags not present')
    end
end

stored_tags = test_utils.verify_attribute_present(fname, 'epochs', 'tags');
for i = 1:length(tags)  % in range(len(tags)):
    if ~any(strcmp(tags(i), stored_tags)) % tags[i] not in tags:
        test_utils.error('Verifying epoch tag content', 'epoch-3: all tags not present')
    end
end


fprintf('%s PASSED\n', script_name);
end

