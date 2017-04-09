function run_all_examples()
  % runs all examples.  Created nwb files are stored
  % in directory ../created_nwb_files
    
%     if nargin < 1
%         % default 'none' to display no validation information (other than if the test
%         % passes). Other options are: 'all', 'summary'
%         verbosity = 'none';
%     end

    % directory for text output
    create_dir = '../text_output_files/create';
    if ~exist(create_dir, 'dir')
        mkdir(create_dir);
    end
    
    % find all examples
    mfiles = dir('*.m');
    script_name = mfilename();
    % run each example
    for i = 1:length(mfiles)
        mfile = mfiles(i).name;
        [trash, name] = fileparts(mfile);  % strip off .m extension
        if ~strcmp(name, script_name)
            % not this script, so run it
            log_file = [create_dir '/' name '.txt' ];
            cmd = [ name, '();' ];
            fprintf('\n========= Running %s\n', cmd)
            [T] = evalc(cmd);
            % save output
            fileID = fopen(log_file,'w');
            fprintf(fileID, T);
            fclose(fileID);
            % diary(log_file)
            % run(cmd)
            % diary off
        end
    end
  
%   fprintf('\n========= Running abstract_feature()\n')
%   abstract_feature()
%   fprintf('\n========= Running analysis-e()\n')
%   analysis-e()
%   fprintf('\n========= Running crcns_alm_1()\n')
%   crcns_alm_1()

end

