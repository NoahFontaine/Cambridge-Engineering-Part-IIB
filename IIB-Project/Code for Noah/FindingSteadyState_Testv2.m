%% Finding when the tunnel is fully established - test v2

originalDir = pwd; % Save the original directory

% Change the directory to the location of your pressure file. Probably best
% to also keep the x locations in the same directory.
cd('F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced');
%%

cd(originalDir); % Change back to the original directory

%% Calling the function test

clear
filename = 'F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced\2024_p_0024.csv';
window_size = 100; % Number of samples in the moving window
std_threshold_start = 50; % Threshold for standard deviation to consider as stable for start detection
mean_change_threshold_start = 100; % Threshold for change in mean to consider as stable for start detection
std_threshold_end = 100; % Threshold for standard deviation to consider as unstable for end detection
mean_change_threshold_end = 50; % Threshold for change in mean to consider as unstable for end detection
ignore_time = 10; % Time to ignore at the beginning (in seconds)
end_buffer_time = 3; % Time buffer before detected end (in seconds)


[start_time, end_time, trimmed_data] = RunStartEnd(filename, window_size, std_threshold_start, mean_change_threshold_start, std_threshold_end, mean_change_threshold_end, ignore_time, end_buffer_time);


%[start_time, end_time, trimmed_data] = RunStartEnd(filename, window_size, std_threshold_start, mean_change_threshold_start, std_threshold_end, mean_change_threshold_end, ignore_time, end_buffer_time)



%data = readtable('F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced\2024_p_0024.csv');