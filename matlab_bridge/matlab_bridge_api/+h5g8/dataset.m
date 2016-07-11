classdef dataset < h5g8.node
    %Class for nwb dataset objects    
    methods
        function obj = dataset(ml_f, fg_dataset)
            % create a matlab nwb_dataset that wraps the Python fg_dataset
            obj = obj@h5g8.node(ml_f, fg_dataset);
        end
    end
end
