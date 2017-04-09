function t_append(verbosity)

% test opening file in append mode
% TESTS modifying existing file
% TESTS creation of modification_time
% TESTS addition of TimeSeries to existing file
% TESTS preservation of TimeSeries when file modified

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

function test_append()
    name1 = 'annot1';
    name2 = 'annot2';
    % create_annotation_series(fname, name1, 'acquisition', True)
    create_annotation_series(fname, name1, 'acquisition/timeseries', true);
    % create_annotation_series(fname, name2, 'acquisition', False)
    create_annotation_series(fname, name2, 'acquisition/timeseries', false);
    test_utils.verify_timeseries(fname, name1, 'acquisition/timeseries', 'TimeSeries');
    test_utils.verify_timeseries(fname, name1, 'acquisition/timeseries', 'AnnotationSeries');
    test_utils.verify_timeseries(fname, name2, 'acquisition/timeseries', 'TimeSeries');
    test_utils.verify_timeseries(fname, name2, 'acquisition/timeseries', 'AnnotationSeries');
    % ut.verify_attribute_present(fname, 'file_create_date', 'modification_time')
 end


function create_annotation_series(fname, name, target, newfile)
    if newfile
        settings = {'file_name', fname, 'verbosity', verbosity, ...
        'identifier', ...
            char(py.nwb.nwb_utils.create_identifier('append example')), ...
        'mode', 'w', ...
        'start_time', 'Sat Jul 04 2015 3:14:16', ...
        'description','Test append file'};
    else
        settings = {'file_name', fname, 'mode', 'r+', 'verbosity', verbosity};
    end
    f = nwb_file(settings{:});
    %
    % annot = neurodata.create_timeseries('AnnotationSeries', name, target)
    annot = f.make_group('<AnnotationSeries>', name, 'path', ['/', target]);
    % annot.set_description('This is an AnnotationSeries '%s' with sample data' % name)
    % annot.set_comment('The comment and description fields can store arbitrary human-readable data')
    % annot.set_source('Observation of Dr. J Doe')
    annot.set_attr('description', sprintf('This is an AnnotationSeries ''%s'' with sample data',  name));
    annot.set_attr('comments', 'The comment and description fields can store arbitrary human-readable data');
    annot.set_attr('source', 'Observation of Dr. J Doe');
    
    %
%     annot.add_annotation('Rat in bed, beginning sleep 1', 15.0)
%     annot.add_annotation('Rat placed in enclosure, start run 1', 933.0)
%     annot.add_annotation('Rat taken out of enclosure, end run 1', 1456.0)
%     annot.add_annotation('Rat in bed, start sleep 2', 1461.0)
%     annot.add_annotation('Rat placed in enclosure, start run 2', 2401.0)
%     annot.add_annotation('Rat taken out of enclosure, end run 2', 3210.0)
%     annot.add_annotation('Rat in bed, start sleep 3', 3218.0)
%     annot.add_annotation('End sleep 3', 4193.0)
    %
    andata = {};
    andata{end+1} = {'Rat in bed, beginning sleep 1', 15.0};
    andata{end+1} = {'Rat placed in enclosure, start run 1', 933.0};
    andata{end+1} = {'Rat taken out of enclosure, end run 1', 1456.0};
    andata{end+1} = {'Rat in bed, start sleep 2', 1461.0};
    andata{end+1} = {'Rat placed in enclosure, start run 2', 2401.0};
    andata{end+1} = {'Rat taken out of enclosure, end run 2', 3210.0};
    andata{end+1} = {'Rat in bed, start sleep 3', 3218.0};
    andata{end+1} = {'End sleep 3', 4193.0};
    shape = [1, length(andata)];
    annotations = cell(shape);
    times = zeros(shape);
    for i = 1:length(andata)
        annotations{i} = andata{i}{1};
        times(i) = andata{i}{2};
    end
    annot.set_dataset('data',annotations);
    annot.set_dataset('timestamps', times);
    f.close()
end

test_append()
fprintf('%s PASSED\n', script_name);
end


