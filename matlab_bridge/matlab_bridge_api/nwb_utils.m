classdef nwb_utils
    % Utility functions for matlab nwb api using Python h5gate
    
    properties
    end
    
    methods(Static)
        function [id] = create_identifier(base_string)
            id = char(py.nwb.nwb_utils.create_identifier(base_string));
        end
        function [value] = load_file(file_name)
            value = py.nwb.nwb_utils.load_file(file_name);
        end
        function add_epoch_ts(e, start_time, stop_time, name, ts)
            % Add timeseries_X group to nwb epoch.
            % e - h5g8.Group containing epoch
            % start_time - start time of epoch
            % stop_time - stop time of epoch
            % name - name of <timeseries> group to be added to epoch
            % ts - timeseries to be added, must be a h5g8.Group
            %    object or path to timeseries
            if isa(ts, 'h5g8.group')
                % timeseries is h5g8.group object.  Retrieve corresponding
                % python h5gate.Group object
                timeseries = ts.fg_node;
            elseif ischar(ts)
                % timesers is path, use that
                timeseries = ts;
            else
                error('Invalid type for timeseries, must be char or h5g8.group: %s', ...
                    class(ts))
            end
            % call python util
            py.nwb.nwb_utils.add_epoch_ts(e.fg_node, start_time, stop_time, name, timeseries);
        end
        function [row_major] = h5reshape(col_major)
            % convert matrix from col major format (used in matlab) to
            % row-major format (used in hdf5)
            % row_major = reshape(col_major', size(col_major)); % for matrix
            shape = size(col_major);
            one_by_n = length(shape) == 2 && shape(1) == 1;
            if one_by_n
                row_major = col_major;
            else
                row_order = fliplr(1:length(shape));
                % row_major = reshape(permute(col_major, row_order), size(col_major));
                row_major = permute(col_major, row_order);
            end
        end
        function [dtype] = min_idtype(iarr)
            % return smallest possible integer dtype that can hold all
            % values in integer array iarr
            min_val = min(iarr);
            max_val = max(iarr);
            unsigned = min_val >= 0;
            if unsigned
                types = {'uint8', 'uint16', 'uint32', 'uint64'};
            else
                types = {'int8', 'int16', 'int32', 'int64'};
            end
            dtype = '';
            for i = 1:4
                if max_val <= intmax(types{i})
                    dtype = types{i};
                    return
                end
            end
            error('unable to find dtype, max_val=%i', max_val);
        end
        function [ml_data] = convert_py_data(py_data)
            % converts data from type passed by python to
            % type used by matlab
            ptype = class(py_data);
            if ~strcmp(ptype(1:3), 'py.')
                % no need to convert, is not python type
                ml_data = py_data;
            else
                if startsWith(ptype,'py.numpy.float') || ...
                   startsWith(ptype,'py.numpy.int') || ...
                   startsWith(ptype,'py.numpy.uint')
                   ptype = 'py.numpy.number';  % for switch case below
                end
                switch ptype
                    case {'py.str', 'py.numpy.string_'}
                        ml_data = char(py_data);
                    case {'py.list' }
                        ml_data = nwb_utils.convert_py_list(py_data);
                    case {'py.numpy.ndarray', 'py.numpy.number'}
                        ml_data = nwb_utils.convert_py_ndarray(py_data);
                    otherwise
                        fprintf('data cannot convert is:');
                        py_data
                        error('Unable to convert Python type "%s" to matlab', ptype)
                end
            end
        end
        function [cellP] = convert_py_list(pylist)
            % convert python list of strings to cell array
            cP = cell(pylist);
            cellP = cell(1, numel(cP));
            for n = 1:numel(cP)
                strP = char(cP{n});
                cellP(n) = {strP};
            end
        end
        function [ml_data] = convert_pycell(fitype, cell_1d)
            % convert cell array containing python integer values to type
            % specified by function fitype.  fitype should be function
            % like: @int32, @uint32, @uint8
            % this needed because Python 3 returns integer data as int64
            % eventhough numpy ndarray dtype for the data may be different.
            % So, in for Python 3 data, need to convert first to int64
            % then to the more specialized integer type.
            try
                ml_data = cellfun(fitype, cell_1d);
            catch ME
                % above failed.  Must by Python 3.  Need to convert to
                % int64 first, then the more specialized type
                ml_data = fitype(cellfun(@int64, cell_1d));
            end
        end
        function [ml_data] = convert_py_ndarray(pydata)
            dtype = char(pydata.dtype.name);
            % cps = cell(pydata.shape);
            shape = nwb_utils.convert_pycell(@int32, cell(pydata.shape));
%             % get shape, need to allow for both Python 2 and Python 3
%             try
%                 % Python 2 returns 32 bit integers for shape
%                 shape = cellfun(@int32, cps);
%             catch ME
%                 % Python 3 returns 64 bit integers for shape
%                 shape = cellfun(@int64, cps);
%             end  
            % shape = cellfun(@int32, cell(pydata.shape));
            is_int = any(strfind(dtype, 'int'));
            is_float = any(strfind(dtype, 'float'));
            is_numeric = is_int || is_float;
            if ~is_numeric
                % assume 1-d array of strings
                ml_data = nwb_utils.convert_py_list(pydata.tolist());
                return
            end
            cell_1d = cell(pydata.flatten().tolist());
            switch dtype
                case {'float64'}
                    ml_data = cellfun(@double, cell_1d);
                case {'float32'}
                    ml_data = cellfun(@single, cell_1d);
                case {'int64'}
                    % ml_data = cellfun(@int32, cell_1d);
                    ml_data = nwb_utils.convert_pycell(@int64, cell_1d);
                case {'int32'}
                    % ml_data = cellfun(@int32, cell_1d);
                    ml_data = nwb_utils.convert_pycell(@int32, cell_1d);
                case {'uint32'}
                    % ml_data = cellfun(@uint32, cell_1d);
                    ml_data = nwb_utils.convert_pycell(@uint32, cell_1d);
                case {'int16'}
                    % ml_data = cellfun(@int16, cell_1d);
                    ml_data = nwb_utils.convert_pycell(@int16, cell_1d);
                case {'uint16'}
                    % ml_data = cellfun(@uint16, cell_1d);
                    ml_data = nwb_utils.convert_pycell(@uint16, cell_1d);
                case {'int8'}
                    % ml_data = cellfun(@int8, cell_1d);
                    ml_data = nwb_utils.convert_pycell(@int8, cell_1d);
                case {'uint8'}
                    % ml_data = cellfun(@uint8, cell_1d);
                    ml_data = nwb_utils.convert_pycell(@uint8, cell_1d);
                otherwise
                    error('unrecognized dtype: %s', dtype)
            end
            if length(shape) > 1
                % only reshape if two or more dimensions
                % ml_data = reshape(ml_data, shape);
                ml_data = reshape(ml_data, flip(shape));
                ml_data = nwb_utils.h5reshape(ml_data);
            end
        end


        function add_epoch_ts_old(e, start_time, stop_time, name, ts)
            % Add timeseries_X group to nwb epoch.
            % e - h5gate.Group containing epoch
            % start_time - start time of epoch
            % stop_time - stop time of epoch
            % name - name of <timeseries> group to be added to epoch
            % ts - timeseries to be added, must be a h5g8.Group
            % object or path to timeseries
            if ischar(ts)
                % ts is path to node rather than node.  Get the node
                error('add_epoch_ts using path not yet implemented');
                % ts = e.file.get_node(ts)
            end
            [start_idx, cnt] = nwb_utils.get_ts_overlaps(ts, start_time, stop_time);
            if isempty(start_idx)
                % no overlap, don't add timeseries
                return
            end
            f = e.make_group('<timeseries_X>', name);
            f.set_dataset('idx_start', int64(start_idx));
            f.set_dataset('count', int64(cnt));
            % f.make_group('timeseries', ts);  % makes a link to ts group
            timeseries_link = sprintf('link:%s/timestamps', char(ts.fg_node.full_path));
            f.make_group('timeseries', 'link', timeseries_link);  % makes a link to ts group
        end
    
        function [start_idx, cnt] = get_ts_overlaps(tsg, start_time, stop_time)
            % Get starting index and count of overlaps between timeseries timestamp
            % and interval between t_start and t_stop.  This is adapted from
            % borg_epoch.py add_timeseries.
            % Inputs:
            %  tsg - h5g8.Group object containing timeseries timestamp.
            %  start_time - starting time of interval (epoch)
            %  stop_time - ending time of interval
            % returns tuple with:
            %  start_idx - starting index of interval in time series, [] if no overlap
            %  cnt - number of elements in timeseries overlapping, zero 0 if no overlap
            timestamps_path = sprintf('%s/timestamps', char(tsg.fg_node.full_path));
            fid = tsg.ml_file.file_pointer;  % pointer to hdf5 file
            dset_id = H5D.open(fid,timestamps_path);
            timestamps = H5D.read(dset_id);
            H5D.close(dset_id);
            [start_idx,upper_index] = nwb_utils.myFindDrGar(timestamps,start_time,stop_time);
            if ~isempty(start_idx)
                cnt = upper_index - start_idx + 1;
            end
        end
        
function [lower_index,upper_index] = myFindDrGar(x,LowerBound,UpperBound)
% From: http://stackoverflow.com/questions/20166847/faster-version-of-find-for-sorted-vectors-matlab
% fast O(log2(N)) computation of the range of indices of x that satify the
% upper and lower bound values using the fact that the x vector is sorted
% from low to high values. Computation is done via a binary search.
%
% Input:
%
% x-            A vector of sorted values from low to high.       
%
% LowerBound-   Lower boundary on the values of x in the search
%
% UpperBound-   Upper boundary on the values of x in the search
%
% Output:
%
% lower_index-  The smallest index such that
%               LowerBound<=x(index)<=UpperBound
%
% upper_index-  The largest index such that
%               LowerBound<=x(index)<=UpperBound

if LowerBound>x(end) || UpperBound<x(1) || UpperBound<LowerBound
    % no indices satify bounding conditions
    lower_index = [];
    upper_index = [];
    return;
end

lower_index_a=1;
lower_index_b=length(x); % x(lower_index_b) will always satisfy lowerbound
upper_index_a=1;         % x(upper_index_a) will always satisfy upperbound
upper_index_b=length(x);

%
% The following loop increases _a and decreases _b until they differ 
% by at most 1. Because one of these index variables always satisfies the 
% appropriate bound, this means the loop will terminate with either 
% lower_index_a or lower_index_b having the minimum possible index that 
% satifies the lower bound, and either upper_index_a or upper_index_b 
% having the largest possible index that satisfies the upper bound. 
%
while (lower_index_a+1<lower_index_b) || (upper_index_a+1<upper_index_b)

    lw=floor((lower_index_a+lower_index_b)/2); % split the upper index

    if x(lw) >= LowerBound
        lower_index_b=lw; % decrease lower_index_b (whose x value remains \geq to lower bound)   
    else
        lower_index_a=lw; % increase lower_index_a (whose x value remains less than lower bound)
        if (lw>upper_index_a) && (lw<upper_index_b)
            upper_index_a=lw;% increase upper_index_a (whose x value remains less than lower bound and thus upper bound)
        end
    end

    up=ceil((upper_index_a+upper_index_b)/2);% split the lower index
    if x(up) <= UpperBound
        upper_index_a=up; % increase upper_index_a (whose x value remains \leq to upper bound) 
    else
        upper_index_b=up; % decrease upper_index_b
        if (up<lower_index_b) && (up>lower_index_a)
            lower_index_b=up;%decrease lower_index_b (whose x value remains greater than upper bound and thus lower bound)
        end
    end
end

if x(lower_index_a)>=LowerBound
    lower_index = lower_index_a;
else
    lower_index = lower_index_b;
end
if x(upper_index_b)<=UpperBound
    upper_index = upper_index_b;
else
    upper_index = upper_index_a;
end
          
end
        
end
end

