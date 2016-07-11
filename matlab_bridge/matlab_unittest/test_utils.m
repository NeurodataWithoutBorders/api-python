classdef test_utils
    % Utility functions for matlab unit tests
    %   These call the functions in Python file test_utils.py
    
    properties
    end
    
    methods(Static)
        function error(context, err_string)
            py.test_utils.error(context, err_string);
        end
        function [val] = verify_present(hfile, group, field)
            pval = py.test_utils.verify_present(hfile, group, field);
            val = nwb_utils.convert_py_data(pval);
        end
        function [val] = verify_attribute_present(hfile, obj, field)
            pval = py.test_utils.verify_attribute_present(hfile, obj, field);
            val = nwb_utils.convert_py_data(pval);
        end
        function verify_timeseries(hfile, name, location, ts_type)
            py.test_utils.verify_timeseries(hfile, name, location, ts_type);
        end
        function verify_absent(hfile, group, field)
            py.test_utils.verify_absent(hfile, group, field);
        end
        function [match] = search_for_substring(h5_str, value)
            if iscell(h5_str)
                % convert cell array to list
                h5_str = py.list(h5_str);
            end
            match = py.test_utils.search_for_substring(h5_str, value);
        end
        
%         function [cellP] = list2cell(pylist)
%             % convert python list of strings to cell array
%             cP = cell(pylist);
%             cellP = cell(1, numel(cP));
%             for n = 1:numel(cP)
%                 strP = char(cP{n});
%                 cellP(n) = {strP};
%             end
%         end      
    end
end

