function [ ds, md ] = crcns_alm_1( source_dir, session_id )
%Convert sample file from CRCNS.org alm-1 data set to NWB format.
%  source_dir (optional) - path to location of source MatLab files
%  session_id (optional) - session_id part of MatLab file name, e.g.:
% "NL_example20140905_ANM219037_20131117"  The strings:
% "data_structure_" and "meta_data_" are prepended to the session_id to
% and the extension ".mat" is added to make the full file names.
% Returns structures for both source matlab files (md=meta_data,
% ds=data_structure).  This useful for testing references to structure.
% in the matlab command window. To use this, call with [ds, md] = crcns_alm_1()


% paths to default source files
default_source_dir = '../source_data/crcns_alm-1/';
default_session_id = 'NL_example20140905_ANM219037_20131117';
script_base_name = mfilename();
script_name = strcat(script_base_name, '.m');

if nargin<1 || isempty(source_dir)
    source_dir = default_source_dir;
end
if nargin<2 || isempty(session_id)
    session_id = default_session_id;
end

ds_infile = fullfile(source_dir, strcat('data_structure_', session_id, '.mat'));
md_infile = fullfile(source_dir, strcat('meta_data_', session_id, '.mat'));

if exist(ds_infile, 'file') ~= 2 || exist(md_infile, 'file') ~= 2
    fprintf('Source files for script "%s" not found', script_name)
    fprint('If using default sample data, download and put them in directory')
    fprintf('"matlab_examples/source_data" as instructed in file')
    fprintf('matlab_examples/0_README.txt');
    return
end

OUTPUT_DIR = '../created_nwb_files/crcns_alm-1/';
if ~exist(OUTPUT_DIR, 'dir')
    mkdir(OUTPUT_DIR);
end

nwb_file_name = strcat(session_id, '.nwb');

% [~,name,~] = fileparts(base_name);
% output_file_name = fullfile(path, strcat(name, '_nwb.h5'));

ds = load(ds_infile);
md = load(md_infile);
% shorten abbrev to just ds and md:
ds = ds.obj;
md = md.meta_data;

% following to get structures in command line, without processing
% return

function [vals, desc] = getHashValuesDesc(hash, key)
    % returns value array corresponding to key in hash
    idx = find(strcmp(hash.keyNames, key));
    vals = hash.value{idx};
    desc = hash.descr{idx};
end

% function [vals, desc] = getTimeSeriesValuesDesc(idStr)
%     % returns description and values for timeSeriesArrayHash
%     hash = ds.timeSeriesArrayHash.value{1};
%     idx = find(strcmp(hash.idStr, idStr));
%     desc = hash.idStrDetailed{idx};
%     vals = hash.valueMatrix(:,idx);
% end
        

function create_trials(f, epoch_tags, epoch_units)
    % initialize trials with basic fields and behavioral data
    % f - nwb file handle
    trial_id = ds.trialIds;
    trial_t = ds.trialStartTimes;
    [good_trials, good_trials_desc] = getHashValuesDesc(ds.trialPropertiesHash, 'GoodTrials');
    ival = (trial_t(end) - trial_t(1)) / (length(trial_t) - 1);
    trial_t(end+1) = trial_t(end) + 2 * ival;
    ep = f.make_group('epochs');
    for i = 1:length(trial_id)
        tid = trial_id(i);
        trial = sprintf('Trial_%03i', tid);
        % fprintf('%i ', tid); % DEBUG
        % if mod(tid, 50) == 0
        %     fprintf('\n');
        % end
        start = trial_t(i);
        stop = trial_t(i+1);
        e = ep.make_group('<epoch_X>', trial);
        e.set_dataset('start_time', start);
        e.set_dataset('stop_time', stop);
        e.set_dataset('tags', epoch_tags{tid});
%         if isempty(epoch_units{tid})
%             units = {};  % to save empty list, use empty cell array
%             units_dtype = ''; % 'S1';
%         else
%             units = epoch_units{tid};
%             units_dtype = '';
%         end
        % e.set_custom_dataset('units', units, 'dtype', units_dtype);
        e.set_custom_dataset('units', epoch_units{tid});
        raw_file = ds.descrHash.value{tid};
        if isempty(raw_file)
            raw_file = 'na';
        else
            % convert from cell array to string
            raw_file = raw_file{1};
        end
        description = sprintf('Raw Voltage trace data files used to acuqire spike times data: %s', raw_file);
        e.set_dataset('description', description);
        % add links to timeseries
%         nwb_utils.add_epoch_ts(e, start, stop, 'lick_trace', lick_trace_ts);
%         nwb_utils.add_epoch_ts(e, start, stop, 'aom_input_trace', aom_input_trace_ts);
        ut = nwb_utils;
        epoch = e;
        ts = '/stimulus/presentation/auditory_cue';
        ut.add_epoch_ts(epoch, start, stop, 'auditory_cue', ts);
        ts = '/stimulus/presentation/pole_in';
        ut.add_epoch_ts(epoch, start, stop, 'pole_in', ts);
        ts = '/stimulus/presentation/pole_out';
        ut.add_epoch_ts(epoch, start, stop, 'pole_out', ts);
        ts = '/acquisition/timeseries/lick_trace';
        ut.add_epoch_ts(epoch, start, stop,'lick_trace', ts);
        ts = '/stimulus/presentation/aom_input_trace';
        ut.add_epoch_ts(epoch, start, stop,'aom_input_trace', ts);
        ts = '/stimulus/presentation/simple_optogentic_stimuli';
        %ts = '/stimulus/presentation/laser_power'
% DEBUG -- don't add this right now -- too many smaples make building file take too long
        % epoch.add_timeseries('laser_power', ts)
        ut.add_epoch_ts(epoch, start, stop, 'simple_optogentic_stimuli', ts)
    end
end

function [epoch_tags] = get_trial_types()
    % add trial types to epoch for indexing
    epoch_tags = {};
    trial_id = ds.trialIds;
    trial_type_string = ds.trialTypeStr;
    trial_type_mat = ds.trialTypeMat;
    [good_trials, good_trials_desc] = getHashValuesDesc(ds.trialPropertiesHash, 'GoodTrials');
    [photostim_types, ptypes_desc] = getHashValuesDesc(ds.trialPropertiesHash, 'PhotostimulationType');
    for i = 1:length(trial_id)
        tid = trial_id(i);
        found_types = {};
        if good_trials(i)
            found_types{end+1} = 'Good trial';
        else
            found_types{end+1} = 'Non-performing';
        end
        for j = 1:8
            if trial_type_mat(j,i) == 1
                found_types{end+1} = trial_type_string{j};
            end
        end
        ps_type_value = photostim_types(i);
        if ps_type_value == 0
            photostim_type = 'non-stimulation trial';
        elseif ps_type_value == 1
            photostim_type = 'PT axonal stimulation';
        elseif ps_type_value == 2
            photostim_type = 'IT axonal stimulation';
        else
            photostim_type = 'discard';
        end
        found_types{end+1} = photostim_type;
        epoch_tags{tid} = found_types;
    end
end

function [epoch_units] = get_trial_units(num_of_units)
    % collect unit information for a given trial
    % pre-fill cell array with empty list of units for each trial
    trial_id = ds.trialIds;
    epoch_units = {};
    for i = 1:length(trial_id)
        tid = trial_id(i);
        epoch_units{tid} = {};
    end
    for unit_id = 1:num_of_units
        unit_name = sprintf('unit_%02i', unit_id);
        trial_ids = ds.eventSeriesHash.value{unit_id}.eventTrials;
        trial_ids = unique(trial_ids);
        for j = 1:length(trial_ids)
            tid = trial_ids(j);
            if ~ismember(unit_name, epoch_units{tid})
                % append unit
                epoch_units{tid} = [ epoch_units{tid}, unit_name];
            end
        end
    end
end
     
            

% load general metadata
fprintf('Reading meta data\n');
% start time
% dateOfExperiment = md.dateOfExperiment{1};
dateOfExperiment = char(md.dateOfExperiment);
% timeOfExperiment = md.timeOfExperiment{1};
timeOfExperiment = char(md.timeOfExperiment);
[year, month, day] = deal(dateOfExperiment(1:4),dateOfExperiment(5:6),dateOfExperiment(7:8));
[hour, min, sec] = deal(timeOfExperiment(1:2), timeOfExperiment(3:4), timeOfExperiment(5:6));
start_time = sprintf('%s-%s-%s %s:%s:%s', year,month,day,hour,min,sec);
exp_description = strcat('Extracellular ephys recording of mouse doing', ...
    ' discrimination task (lick left/right), with optogenetic ', ...
    ' stimulation plus pole and auditory stimulus');

% create nwb file

settings = { ...
    'file_name', fullfile(OUTPUT_DIR, nwb_file_name), ...
    'identifier', char(py.nwb.nwb_utils.create_identifier('crcns_alm-1')), ...
    'mode', 'w', ...
    'start_time', start_time, ...
    'description', exp_description
    };
f = nwb_file(settings{:});

f.set_dataset('session_id', session_id);

% f.set_custom_dataset('test_empty_list', []);
% f.close()
% return

g = f.make_group('subject');

subject_description = sprintf('Animal Strain: %s;\nAnimal source: %s;\nDate of birth: %s', ...
    char(md.animalStrain), char(md.animalSource), char(md.dateOfBirth));

g.set_dataset('description', subject_description);

genotype = sprintf('Animal gene modification: %s;\nAnimal genetic background: %s;\nAnimal gene copy: %s',...
    md.animalGeneModification{1}, md.animalGeneticBackground{1}, num2str(md.animalGeneCopy{1}));
g.set_dataset('genotype', genotype);
g.set_dataset('sex', md.sex);
g.set_dataset('age', '>P60');
g.set_dataset('species', md.species{1});
g.set_dataset('weight', 'Before: 20, After: 21');
f.set_dataset('related_publications', md.citation{1});

experimentType = ['Experiment type: ' strjoin(md.experimentType, ', ')]; %% was string array in borg

f.set_dataset('notes',experimentType);
f.set_dataset('experimenter', md.experimenters{1});
f.set_custom_dataset('reference_atlas', md.referenceAtlas{1});

% f.set_dataset('surgery', fileread(fullfile(source_dir,'surgery.txt')));
% f.set_dataset('data_collection', fileread(fullfile(source_dir,'data_collection.txt')));
% f.set_dataset('experiment_description', ...
%     fileread(fullfile(source_dir,'experiment_description.txt')));
f.set_dataset('surgery', py.nwb.nwb_utils.load_file(fullfile(source_dir,'surgery.txt')));
f.set_dataset('data_collection', py.nwb.nwb_utils.load_file(fullfile(source_dir,'data_collection.txt')));
f.set_dataset('experiment_description', ...
    py.nwb.nwb_utils.load_file(fullfile(source_dir,'experiment_description.txt')));

f.set_custom_dataset('whisker_configuration', md.whiskerConfig{1});


% probe = [...
%         0,   0,  0 ;     0, 100,  0 ;     0, 200,  0 ;     0, 300,  0; ...
%         0, 400,  0 ;     0, 500,  0 ;     0, 600,  0 ;     0, 700,  0; ...
%       200,   0,  0 ;   200, 100,  0 ;   200, 200,  0 ;   200, 300,  0; ...
%       200, 400,  0 ;   200, 500,  0 ;   200, 600,  0 ;   200, 700,  0; ...
%       400,   0,  0 ;   400, 100,  0 ;   400, 200,  0 ;   400, 300,  0; ...
%       400, 400,  0 ;   400, 500,  0 ;   400, 600,  0 ;   400, 700,  0; ...
%       600,   0,  0 ;   600, 100,  0 ;   600, 200,  0 ;   600, 300,  0; ...
%       600, 400,  0 ;   600, 500,  0 ;   600, 600,  0 ;   600, 700,  0];
  
  
sites = md.extracellular.siteLocations;
nsites = length(sites);
if nsites ~= 32
    error('Expected 32 electrode locations, found %i', nsites)
end
probe = double(zeros(nsites, 3));
for i = 1:length(sites)
    probe(i,:) = sites{i} * 1.0e-6;
end

shank = [repmat({'shank0'},1,8), repmat({'shank1'},1,8), ...
         repmat({'shank2'},1,8), repmat({'shank3'},1,8) ];
     
ee = f.make_group('extracellular_ephys');

% electrode_map and electrode_group
ee.set_dataset('electrode_map', nwb_utils.h5reshape(probe));
ee.set_dataset('electrode_group', shank);
ee.set_dataset('filtering', 'Bandpass filtered 300-6K Hz');

% add empty ElectricalSeries to acquisition
function create_empty_acquisition_series(name, num)
    vs = f.make_group('<ElectricalSeries>', name, 'path', '/acquisition/timeseries');
    data = {int32(0)};  % specify int32 so stored as int32 rather than float32
    vs.set_attr('comments','Acquired at 19531.25Hz');
    vs.set_attr('source', 'Device ''ephys-acquisition''');
    vs.set_dataset('data', data, 'attrs', {'unit', 'none', 'conversion', 1.0, 'resolution', NaN});
    timestamps = {int32(0)};  % use cell array to create array of on one element in hdf5
    vs.set_dataset('timestamps', timestamps);
    % el_idx = 8 * num + np.arange(8)
    el_idx = 8 * num + (0:7);
    vs.set_dataset('electrode_idx', el_idx);
    vs.set_attr('description', 'Place-holder time series to represent ephys recording. Raw ephys data not stored in file');
end
    
    
ephys_device_txt = '32-electrode NeuroNexus silicon probes recorded on a PCI6133 National Instrimunts board. See ''general/experiment_description'' for more information';
f.set_dataset('<device_X>', ephys_device_txt, 'name', 'ephys-acquisition');
f.set_dataset('<device_X>', 'Stimulating laser at 473 nm', 'name', 'optogenetic-laser');


% TODO fix location info. also check electrode coordinates
fprintf('Warning: shank locations hardcoded in script and are likely incorrect\n');
shank_info = {...
    'shank0', 'P: 2.5, Lat:-1.2. vS1, C2, Paxinos. Recording marker DiI'; ...
    'shank1', 'P: 2.5, Lat:-1.4. vS1, C2, Paxinos. Recording marker DiI'; ...
    'shank2', 'P: 2.5, Lat:-1.6. vS1, C2, Paxinos. Recording marker DiI'; ...
    'shank3', 'P: 2.5, Lat:-1.8. vS1, C2, Paxinos. Recording marker DiI'};

% extracellular_ephys/electrode_group_N
for i = 1:4
    shank_name = shank_info{i,1};
	eg = ee.make_group('<electrode_group_X>', shank_name);
    eg.set_dataset('location',shank_info{i,2});
    create_empty_acquisition_series(shank_name, i-1);
	% g2.set_dataset('description', shank_info{i,2});
	% g.set_dataset('location',eg_info.location)
	% g.set_dataset('device', eg_info.device)
end

% 
% % behavior
task_kw = md.behavior.task_keyword;
f.set_custom_dataset('task_keyword', task_kw);

% virus
inf_coord = md.virus.infectionCoordinates;
inf_loc = md.virus.infectionLocation{1};
inj_date = md.virus.injectionDate;
inj_volume = md.virus.injectionVolume;
virus_id = md.virus.virusID{1};
virus_lotNr = md.virus.virusLotNumber;
virus_src = md.virus.virusSource{1};
virus_tit = md.virus.virusTiter{1};

virus_text = sprintf(['Infection Coordinates: %s' ...
  '\nInfection Location: %s\nInjection Date: %s\nInjection Volume: %s' ... 
  '\nVirus ID: %s\nVirus Lot Number: %s\nVirus Source: %s\nVirus Titer: %s'],...
  [mat2str(inf_coord{1}) mat2str(inf_coord{2})],...
  inf_loc, inj_date, [mat2str(inj_volume(1)) mat2str(inj_volume(2))], virus_id, ...
  char(virus_lotNr), virus_src, virus_tit);
 
f.set_dataset('virus', virus_text);


%fiber


% fiber
ident_meth = md.photostim.identificationMethod;
ident_text = ['Identification method: ', strjoin(ident_meth, ', ')];

location = md.photostim.photostimLocation;
location_str = strjoin(location, ', ');
loc_text = ['Location: ', location_str];


% impl_date = md.fiber.implantDate{1};
% tip_coord = md.fiber.tipCoordinates{1};
% tip_loc   = md.fiber.tipLocation{1};
% fiber_text = sprintf('Implant Date: %s\nTip Coordinates: %s', ...
%   impl_date, mat2str(tip_coord));
phst_wavelength = md.photostim.photostimWavelength{1};
% g = f.make_group('optophysiology');
opto = f.make_group('optogenetics');
s1 = opto.make_group('<site_X>', 'site 1');
s1.set_dataset('description', sprintf('%s\n%s', loc_text, ident_text));
% stim_loc = parse_h5_obj(check_entry(meta_h5,"photostim/photostimLocation"))[0]
% stim_coord = parse_h5_obj(check_entry(meta_h5,"photostim/photostimCoordinates"))[1]
% stim_lambda = parse_h5_obj(check_entry(meta_h5,"photostim/photostimWavelength"))[0]
% stim_text = "Stim location: %s\nStim coordinates: %s" % (str(stim_loc), str(stim_coord))
% stim_loc = location{1};  % why just first element?
stim_coord = md.photostim.photostimCoordinates{2};  % why just second element?
stim_lambda = md.photostim.photostimWavelength{1};
%  stim_text = sprintf('Stim location: %s\nStim coordinates: %s',  stim_loc, mat2str(stim_coord));
stim_text = sprintf('Stim location: %s\nStim coordinates: %s',  location_str, mat2str(stim_coord));
s1.set_dataset('location', stim_text);
s1.set_dataset('excitation_lambda', sprintf('%i nm', stim_lambda));
s1.set_dataset('device', 'optogenetic-laser');


% 
% s1.set_dataset('description', fiber_text);
% s1.set_dataset('location', tip_loc);
% s1.set_dataset('excitation_lambda', strcat(mat2str(phst_wavelength), ' nm'));
% s1.set_dataset('device', 'optogenetic-laser');

% #photostim
phst_id_method = md.photostim.identificationMethod;
phst_coord = md.photostim.photostimCoordinates;
phst_loc = md.photostim.photostimLocation;
% phst_wavelength = md.photostim.photostimWavelength{1};
stim_method = md.photostim.stimulationMethod;
 
photostim_text = {};
for i = 1:length(phst_id_method)
    pt_text = sprintf(['Identification Method: %s'...
      '\nPhotostimulation Coordinates: %s' ...
      '\nPhotostimulation Location: %s'...
      '\nPhotostimulation Wavelength: %s' ...
      '\nStimulation Method: %s'],...
      phst_id_method{i},  mat2str(phst_coord{i}), phst_loc{i},...
      mat2str(phst_wavelength), stim_method{i});
  photostim_text{end+1} = pt_text;
end
photostim_text = strjoin(photostim_text, ';\n');

% photostim_text = sprintf(['Identification Method: %s'...
%   '\nPhotostimulation Coordinates: %s' ...
%   '\nPhotostimulation Location: %s'...
%   '\nPhotostimulation Wavelength: %s' ...
%   '\nStimulation Method: %s'],...
%   phst_id_method,  mat2str(phst_coord), phst_loc,...
%   mat2str(phst_wavelength), stim_method);

f.set_dataset('stimulus', photostim_text);
    
    
% raw data section
% lick trace is stored in acquisition
% photostimulation wave forms is stored in stimulus/processing
fprintf('Reading raw data\n');
% get times
timestamps = ds.timeSeriesArrayHash.value{1}.time;
% calculate sampling rate
% rate = (length(timestamps)-1)/(timestamps(end) - timestamps(1));
% get data
valueMatrix = ds.timeSeriesArrayHash.value{1}.valueMatrix;
lick_trace = valueMatrix(:,1);
aom_input_trace = valueMatrix(:,2);
laser_power = valueMatrix(:,3);
% get descriptions
comment1 = ds.timeSeriesArrayHash.keyNames{1};
comment2 = ds.timeSeriesArrayHash.descr{1};
comments = sprintf('%s: %s', comment1, comment2);
descr = ds.timeSeriesArrayHash.value{1}.idStrDetailed;
% create timeseries for lick_trace
g = f.make_group('<TimeSeries>', 'lick_trace', 'path', '/acquisition/timeseries', 'attrs',...
    {'comments', comments, 'description', char(descr(1))});
g.set_dataset('data', lick_trace', 'attrs',...  % tranpose lick_trace, so 1xn
    {'conversion', 1, 'resolution', NaN, 'unit', 'unknown'}, 'compress', true );
t1 = g.set_dataset('timestamps', timestamps', 'compress', true);      % transpose time_stamps, so 1xn
g.set_dataset('num_samples', int64(length(lick_trace)));

lick_trace_ts = g;  % save for referencing when making epochs
% laser_power
g = f.make_group('<OptogeneticSeries>', 'simple_optogentic_stimuli', ...
    'path', '/stimulus/presentation', ...
    'attrs', {'comments', comments, 'description', char(descr(3)) });
g.set_dataset('site', 'site 1');
g.set_dataset('data', laser_power', 'attrs' ,...
    {'unit', 'Watts', 'conversion', 1000.0, 'resolution', NaN});
g.set_dataset('timestamps', t1);  % sets link to other timestamp dataset
g.set_dataset('num_samples', int64(length(lick_trace)));
lasar_power_ts = g;  % save for referencing when making epochs

% aom_input_trace
g = f.make_group('<TimeSeries>', 'aom_input_trace', 'path', '/stimulus/presentation');
g.set_attr('comments', comments);
g.set_attr('description', char(descr(2)));
d = g.set_dataset('data', aom_input_trace', 'attrs', {'resolution', NaN});
d.set_attr('unit', 'Volts');
d.set_attr('conversion', 1.0);
g.set_dataset('timestamps', t1);
g.set_dataset('num_samples', int64(length(lick_trace)));
aom_input_trace_ts = g; % save for referencing when making epochs

trial_start_times = ds.trialStartTimes;

key='PoleInTime';
pole_in_ts = f.make_group('<TimeSeries>', 'pole_in', 'path', '/stimulus/presentation');
[pole_in_time, pole_in_time_descr] = getHashValuesDesc(ds.trialPropertiesHash, key);
pole_in_timestamps = pole_in_time' + trial_start_times;
% create dummy data: 1 for 'on', -1 for 'off'
% pole_in_data = [1]*len(pole_in_timestamps)
pole_in_data(1:length(pole_in_timestamps)) = int32(1);
pole_in_ts.set_dataset('data', pole_in_data, ...
    'attrs', {'resolution', NaN, 'unit', 'unknown', 'conversion',1.0});
pole_in_ts.set_attr('comments', pole_in_time_descr);
pole_in_ts.set_attr('description', key);
pole_in_ts.set_dataset('timestamps', pole_in_timestamps);
pole_in_ts.set_attr('source', 'Times and intervals are as reported in Nuo''s data file, but relative to session start');

key='PoleOutTime';
pole_out_ts = f.make_group('<TimeSeries>', 'pole_out', 'path', '/stimulus/presentation');
[pole_out_time, pole_out_time_descr] = getHashValuesDesc(ds.trialPropertiesHash, key);
pole_out_timestamps = pole_out_time' + trial_start_times;
% create dummy data: 1 for 'on', -1 for 'off'
% pole_out_data = [1]*len(pole_out_timestamps)
pole_out_data(1:length(pole_out_timestamps)) = int32(1);
pole_out_ts.set_dataset('data', pole_out_data, ...
    'attrs', {'resolution', NaN, 'unit','unknown','conversion',1.0});
pole_out_ts.set_attr('comments', pole_out_time_descr);
pole_out_ts.set_attr('description', key);
pole_out_ts.set_dataset('timestamps', pole_out_timestamps);
pole_out_ts.set_attr('source', 'Times and intervals are as reported in Nuo''s data file, but relative to session start');

key='CueTime';
aud_cue_ts = f.make_group('<TimeSeries>', 'auditory_cue', 'path', '/stimulus/presentation');
% time = grp['3/3'].value
[cue_time, cue_time_descr] = getHashValuesDesc(ds.trialPropertiesHash, key);
cue_timestamps = cue_time' + trial_start_times;
% create dummy data: 1 for 'on', -1 for 'off'
% cue_data = [1]*len(cue_timestamps)
cue_data(1:length(cue_timestamps)) = int32(1);
aud_cue_ts.set_dataset('data', cue_data, 'attrs', {'resolution', NaN,'unit', 'unknown','conversion', 1.0});
aud_cue_ts.set_attr('comments', cue_time_descr);
aud_cue_ts.set_attr('description', key);
aud_cue_ts.set_dataset('timestamps', cue_timestamps);
aud_cue_ts.set_attr('source', 'Times are as reported in Nuo''s data file, but relative to session time');



% Create module 'Units' for ephys data
% Interface 'UnitTimes' contains spike times for the individual units
% Interface 'EventWaveform' contains waveform data and electrode information
% Electrode depths and cell types are collected in string arrays at the top level
% of the module
fprintf('Reading Event Series Data\n');

% create module units
mod_name = 'Units';
m = f.make_group('<Module>', mod_name);
m.set_custom_dataset('description', 'Spike times and waveforms');
% below set_attr call causes matlab to crash.  source is not
% an attribute of module.
% m.set_attr('source', 'Data as reported in Nuo''s data file');
% make UnitTimes and EventWaveform interfaces
spk_waves_iface = m.make_group('EventWaveform');
spk_waves_iface.set_attr('source', 'Data as reported in Nuo''s file');
spk_times_iface = m.make_group('UnitTimes');
spk_times_iface.set_attr('source', 'EventWaveform in this module');
% unit_ids = {};
% top level folder
unit_num = length(ds.eventSeriesHash.value);
% initialize cell_types and electrode_depth arrays with default values
cell_types = repmat({'unclassified'}, 1, unit_num);
% electrode_depths = NaN(1, unit_num);
electrode_depths = zeros(1, unit_num);
% unit_descr = ds.eventSeriesHash.descr;  % not used.  Should it be?
for i = 1:unit_num
    unit = sprintf('unit_%02i',i);
    % unit_ids{end+1} = unit;
    % get data
    grp_top_folder = ds.eventSeriesHash.value{i};
    timestamps = grp_top_folder.eventTimes;
    trial_ids = grp_top_folder.eventTrials;
    % calculate sampling rate
    % rate = (timestamps(end) - timestamps(1))/(length(timestamps)-1);
    waveforms = grp_top_folder.waveforms;
    dims = size(waveforms); % e.g. 10227, 29
    sample_length = dims(2);  % e.g. 29
    channel = grp_top_folder.channel; % shape is 10227, 1
    % read in cell types and update cell_type array
    cell_type = grp_top_folder.cellType;
    cell_type = strjoin(cell_type, ' and ');
    cell_types{i} =  [unit, ' - ', cell_type];
    % read in electrode depths and update electrode_depths array
    depth = grp_top_folder.depth;
    electrode_depths(i) = 0.001 * depth;
    
    % create SpikeEventSeries (waveforms) group
    spk = spk_waves_iface.make_group('<SpikeEventSeries>', unit);
    spk.set_custom_dataset('sample_length', int32(sample_length));
    spk.set_attr('source', '---');
    spk.set_dataset('timestamps', timestamps');
    spk.set_dataset('data', nwb_utils.h5reshape(waveforms), ...
        'attrs', {'resolution', NaN, 'unit', 'Volts', 'conversion', 0.1});  % volts plural to match Python version from AIBSs
    spk.set_dataset('electrode_idx', {channel(1)} );  % include in cell array to make array in hdf5
    spk.set_attr('description', cell_type);

%     gw.set_dataset('data', waveforms', 'attrs',...
%           {'unit', 'Volt', 'conversion', 0.1, 'resolution', 1}, 'compress', true);
%     gw.set_dataset('timestamps', ts);
%     gw.set_dataset('num_samples', int64(nevents));
%     gw.set_custom_dataset('sample_length', int64(nsamples));
%     gw.set_dataset('source', '---');
    nevents = dims(1);
    if nevents ~= length(timestamps)
        error('nevents=%i, len(timestamps)=%i',nevents, length(timestamps));
    end

%     # fill in values for the timeseries
%     spk.set_value("sample_length", sample_length)
%     spk.set_time(timestamps)
%     spk.set_data(waveforms, "Volts", 0.1,1)
%     spk.set_value("electrode_idx", [channel[0]])
%     spk.set_description("single unit %d with cell-type information and approximate depth, waveforms sampled at 19531.25Hz" %i)
%     spk_waves_iface.set_timeseries("waveform_timeseries", spk)
%     # add spk to interface
%     description = unit_descr[i-1]
%     spk_times_iface.add_unit(unit, timestamps, description)
%     spk_times_iface.append_unit_data(unit, trial_ids, "trial_ids")

    % create UnitTimes group
    ug = spk_times_iface.make_group('<unit_N>', unit);
    ts = ug.set_dataset('times', timestamps');
    ug.set_dataset('unit_description', cell_type);
    ug.set_dataset('source', 'Data from processed matlab file');
    ug.set_custom_dataset('trial_ids', trial_ids', 'dtype', nwb_utils.min_idtype(trial_ids));
    
    % gw.set_dataset('electrode_idx', int32([channel(1), channel(1)]) );  % make array to prevent error
end
% spk_times_iface.set_dataset('unit_list', unit_ids);
spk_times_iface.set_custom_dataset('CellTypes', cell_types);
spk_times_iface.set_custom_dataset('ElectrodeDepths', electrode_depths);


fprintf('Creating epochs\n');
epoch_tags = get_trial_types();
unit_num = length(ds.eventSeriesHash.value);
epoch_units = get_trial_units(unit_num);
create_trials(f, epoch_tags, epoch_units);

fprintf('Collecting Analysis Information');
trial_start_times = ds.trialStartTimes;
trial_types = ds.trialTypeStr;
trial_type_mat = ds.trialTypeMat;
[good_trials, good_trials_desc] = getHashValuesDesc(ds.trialPropertiesHash, 'GoodTrials');
grp = f.make_group('analysis', 'abort', false);
grp.set_custom_dataset('trial_start_times', trial_start_times);
grp.set_custom_dataset('trial_type_string', trial_types');
% grp.set_custom_dataset('trial_type_mat', reshape(trial_type_mat', size(trial_type_mat)), 'dtype', 'uint8');
grp.set_custom_dataset('trial_type_mat', nwb_utils.h5reshape(trial_type_mat), 'dtype', 'uint8');
grp.set_custom_dataset('good_trials', uint8(good_trials'), 'dtype', 'uint8');  % first uint8 needede to convert logical to integer


f.close();


end
