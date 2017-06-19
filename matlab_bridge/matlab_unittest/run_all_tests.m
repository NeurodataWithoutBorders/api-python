function run_all_tests( verbosity )
    %Run all the tests,  Set input verbosity == 'all' to display
    % validation output for each NWB file created
    
    if nargin < 1
        % default 'none' to display no validation information (other than if the test
        % passes). Other options are: 'all', 'summary'
        verbosity = 'none';
    end
    
    fprintf('pyversion is;')
    pyversion
  
    % directory for text output
    output_dir = '../matlab_examples/text_output_files';
    if ~exist(output_dir, 'dir')
        mkdir(output_dir);
    end
    
    % write log of running all tests to the following file
    log_file='../matlab_examples/text_output_files/unittest_results.txt';
    % delete   '../matlab_examples/text_output_files/unittest_results.txt'
    if exist(log_file, 'file')==2
        delete(log_file);
    end
    diary(log_file)
    
    % find all test
    tests = dir('t_*.m');
    script_name = mfilename();
    % run each test
    for i = 1:length(tests)
        test = tests(i).name;
        [trash, name] = fileparts(test);  % strip off .m extension
        if ~strcmp(name, script_name)
            % file is not this script, run it
            feval(name, verbosity);
        end
    end
    diary off
end

