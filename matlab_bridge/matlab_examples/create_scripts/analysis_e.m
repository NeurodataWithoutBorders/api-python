function analysis_e()

% This example illustrates using an extension to store data in the the /analysis group.  
% The /analysis group is reserved for results of lab-specific analysis.
% 
% The extension definition is in file "extensions/e-analysis.py".
% 
% The example is based on the contents of the Allen Institute for Brain Science
% Cell Types database NWB files.


OUTPUT_DIR = '../created_nwb_files/';
script_base_name = mfilename();
nwb_file_name = [script_base_name '.nwb'];
nwb_file_path = [OUTPUT_DIR nwb_file_name];

% create a new NWB file
settings = { ...
    'file_name', nwb_file_path, ...
    'identifier', ...
        char(py.nwb.nwb_utils.create_identifier('abstract-feature example')), ...
    'mode', 'w', ...
    'start_time', 'Sat Jul 04 2015 3:14:16', ...
    'description',['Test file demonstrating storing data in the /analysis' ...
        ' group that is defined by an extension.'] ...
    'extensions', {'../../../examples/create_scripts/extensions/e-analysis.py'} ...
    };

fprintf('Creating %s', nwb_file_path);
f = nwb_file(settings{:});

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% This example, stores spike times for multiple sweeps
% create the group for the spike times
% The group ("aibs_spike_times") is defined in the extension

ast = f.make_group('aibs_spike_times');

% some sample data
times = [1.1, 1.2, 1.3, 1.4, 1.5];

% create some sample sweeps
for i = 1:5
    sweep_name = sprintf('sweep_%03i', i);
    ast.set_dataset('<aibs_sweep>', times, 'name', sweep_name);
end

% all done; close the file
f.close()

