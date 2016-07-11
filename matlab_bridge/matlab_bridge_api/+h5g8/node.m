classdef node < handle
    % This class (node) is group or dataset object in matlab
    % Corresponds to Node in h5gate (Python)
    
    properties
        ml_file    % matlat file object
        fg_node    % file gate (Python, h5gate) node object
    end
    
    methods
        function obj = node(ml_file, fg_node)
            % save reference matlab file and h5gate (python) node
            obj.ml_file = ml_file;
            obj.fg_node = fg_node;
        end
        function [robj] = set_attr(obj, aid, value, varargin)
            % Set attribute with key aid to value 'value'
            % if custom true, don't give warning about custom attribute
            % parameters for h5gate set_attr:
            % (self, aid, value, custom=''):
            arg_names = { 'custom'};
            arg_types = { 'logical' };
            arg_default={ false };
            arg_vals = obj.ml_file.parse_arguments(varargin, arg_names, arg_types, arg_default);
            custom = arg_vals.custom;
            % call python code in h5g8
            obj.fg_node.set_attr(aid, value, custom);
            % this call the matlab group constructor
            % obj.ml_file.process_h5commands()
            % return original node object to allow stacking calls to this
            robj = obj;
        end
    end
    
end

