%% Misentropic new code (trying to make it cleaner)
clc
clear all

%%

% Save the original directory
originalDir = pwd;


%% 

% Use this function to trim the data 

filename = 'F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced\2024_p_0024.csv';
window_size = 100; % Number of samples in the moving window
std_threshold_start = 50; % Threshold for standard deviation to consider as stable for start detection
mean_change_threshold_start = 100; % Threshold for change in mean to consider as stable for start detection
std_threshold_end = 100; % Threshold for standard deviation to consider as unstable for end detection
mean_change_threshold_end = 50; % Threshold for change in mean to consider as unstable for end detection
ignore_time = 10; % Time to ignore at the beginning (in seconds)
end_buffer_time = 3; % Time buffer before detected end (in seconds)


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

%% Plots Misen against normalised x

% Change the directory to the location of your pressure file. Probably best
% to also keep the x locations in the same directory.
cd('F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced');

width = 1000;
height = 1000;

% Create a new figure with the specified size
fig = figure('Position', [100, 100, width, height]);

x_pos= table2array(readtable("RRLip_x_newtapsused.csv")); % For the second tapping setup (2024 campaign)
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

%% change back to the original directory
cd(originalDir);

