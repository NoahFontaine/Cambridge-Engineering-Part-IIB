%% Code to find the isentropic Mach number for a steady run
    % A steady run is one during which both Mentry & MFS are constant.
    % For runs with varying tunnel parameters please use
    % "M_isentropic_varying".
clc
clear all

%%

% Save the original directory
originalDir = pwd;


%% 

% Use this function to trim the data 

filename = 'F:\Dropbox Data\Data\Data\Pressure - Master\2024_p_0051.csv'
window_size = 100; % Number of samples in the moving window
std_threshold_start = 50; % Threshold for standard deviation to consider as stable for start detection
mean_change_threshold_start = 100; % Threshold for change in mean to consider as stable for start detection
std_threshold_end = 100; % Threshold for standard deviation to consider as unstable for end detection
mean_change_threshold_end = 50; % Threshold for change in mean to consider as unstable for end detection
ignore_time = 10; % Time to ignore at the beginning (in seconds)
end_buffer_time = 3; % Time buffer before detected end (in seconds)


% Not to be confued wiwth "selectStartEnd". This function automatically
% works out a start and end time of the run and trims between them.
[start_time, end_time, data] = RunStartEnd(filename, window_size, std_threshold_start, mean_change_threshold_start, std_threshold_end, mean_change_threshold_end, ignore_time, end_buffer_time);

data = table2array(data);


%% Works out isentropic Mach number at each tapping
%data = table2array(readtable("F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced\2024_p_0024.csv"));

%plot(data(:,1),data(:,4)) % Plot the pressure trace to find when the tunnel is fully started.



data(:,1) = [];
size_data = size(data);
num_columns = size_data(2);
num_rows = size_data(1);
for i = 1:num_columns
       data_average(:,i) = mean(data(:,i));
end
p0 = data_average(:,16)
for i = 1:num_columns
M_isen{i} = sqrt(((p0./data_average(:,i)).^((1.4-1)/1.4)-1).*(2./(1.4-1)));
end
M_isen(1)
M_isen = cell2mat(M_isen);

%% Import the RR CFD data

cd('F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced')

rr_data(:,1) = table2array(readtable("CFD_x.csv"));
rr_data(:,2) = table2array(readtable("CFD_M.csv"));

%% Plots Misen against normalised x

% Change the directory to the location of your pressure file. Prbably best
% to also keep the x locations in the same directory.
%cd('F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced');

width = 1000;
height = 1000;

% Create a new figure with the specified size
fig = figure('Position', [100, 100, width, height]);

x_pos= table2array(readtable("F:\Dropbox Data\Data\Data\Pressure - Master\RRLip_x_newtapsused.csv")); % For the second tapping setup (2024 campaign)
%x_pos= table2array(readtable("RRLip_x_tappingset1")); % For the first tapping setup.

%x_nondim = x_pos/140;

%plot(x_pos(1:12),M_isen(2:13),'k--square','LineWidth',2)
plot(x_pos(1:12),M_isen(2:13),'k--square','LineWidth',2)
box on
pbaspect([1 1 1])
ylim([0.3 1.6])
set(gca,'linewidth',1.3)
set(gca,'TickLabelInterpreter','latex')
set(gca,'fontsize', 26) 
ylabel('Isentropic Mach number','interpreter','latex')
xlabel('x/D','interpreter','latex')

%% Save peak M and location to a variable

% % Find the maximum Mach number in the array
% [PeakMis, PeakMis_x] = max(M_isen);
% 
% PeakMis_x = x_pos(PeakMis_x)
% 
% % Display the maximum Mach number
% disp(['The highest Mach number is: ', num2str(PeakMis)]);
% disp(['The location of the peak Mis is: x/D=', num2str(PeakMis_x)]);
% 
% % Create the .mat file name based on the .csv file name
% [~, name, ~] = fileparts(filename);  % Extract the file name without extension
% 
% % Create a structure to save the data
% peakM.Name = name
% peakM.MachNumber = PeakMis;
% peakM.Location = PeakMis_x;
% 
% % Save the data to the .mat file
% save(name, 'peakM');
% 
% % Display a message indicating the data was saved
% disp(['Peak data saved to ', name]);

% %% Save to the Peak M .csv
% 
% 
% % Specify the name of the CSV file to append the data to
% outputCsvFileName = 'PeakIsentropicM.csv';  % Replace with your desired output CSV file name
% 
% % Prepare the new data to append
% newData = {peakM.Name, peakM.MachNumber, peakM.Location};
% 
% % Check if the file exists
% if isfile(outputCsvFileName)
%     % Append new data as a new row
%     fid = fopen(outputCsvFileName, 'a');
% else
%     % If file doesn't exist, create a new one and write the header and data
%     fid = fopen(outputCsvFileName, 'w');
%     headers = {'OriginalCSVFileName', 'MaxMachNumber', 'IndexOfMaxMachNumber'};
%     fprintf(fid, '%s,%s,%s\n', headers{:});
% end
% 
% % Write the new data
% fprintf(fid, '%s,%f,%d\n', newData{:});
% fclose(fid);
% 
% % Display a message indicating the data was saved
% disp(['Peak data saved to ', outputCsvFileName]);

cd(pwd);

%% change back to the original directory
cd(originalDir);

