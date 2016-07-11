function t_modification_time(verbosity)

% creates file and modifies it multiple times

script_base_name = mfilename();
script_name = [script_base_name '.m'];
fname = [regexprep(script_base_name, '^t_', 's_') '.nwb'];
if nargin < 1
    % default, display all information. Other options are: 'none', 'summary'
    verbosity = 'all';
end

settings = {'file_name', fname, 'mode', 'w', 'verbosity', verbosity, ...
    'start_time', 'Sat Jul 04 2015 3:14:16' ...
    'identifier', nwb_utils.create_identifier('Modification example'), ...
    'description','Modified empty file'};

f = nwb_file(settings{:});         
f.close()


settings = {'file_name', fname, 'mode', 'r+', 'verbosity', verbosity};
f = nwb_file(settings{:});
% need to change the file for SLAPI to update file_create_date
f.set_dataset('species', 'SPECIES');
f.close()


settings = {'file_name', fname, 'mode', 'r+', 'verbosity', verbosity};
f = nwb_file(settings{:});
% need to change the file for SLAPI to update file_create_date
f.set_dataset('genotype', 'GENOTYPE');
f.close()

% read data using matlab hdf5 api
dates = hdf5read(fname,'file_create_date');
% f = py.h5py.File(fname);
% dates = f['file_create_date']
if length(dates) ~= 3
    test_utils.error(filename, sprintf('Expected 3 entries in file_create_date; found %d', length(dates)))
end

fprintf('%s PASSED\n', script_name);
end
