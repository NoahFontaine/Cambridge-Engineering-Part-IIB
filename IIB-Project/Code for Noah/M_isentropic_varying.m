%% Code to find the isentropic Mach number for a run with varying tunnel parameters
    % Please use "M_isentropic_steadyrun" for tunnel runs in which no
    % Mentry and MFS are constant. This script is a bit more hands on and
    % the other will save you some time. 
clc
clear all
close all

%% Use this function to trim the data using the pressure trace.

filename = ('F:\Dropbox Data\Data\Data\Pressure - Master\2024_p_0006.csv')
[run_start,run_end]=selectStartEnd(filename)
data = readmatrix(filename);
data_trimmed = data(run_start:run_end,:);
data = data_trimmed;

%% Works out Misen

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