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

filename = ('F:\Dropbox Data\Data\Data\Pressure - Master\2024_p_0052.csv')
[run_start,run_end]=selectStartEnd(filename)
data = readmatrix(filename);
data_trimmed = data(run_start:run_end,:);
data = data_trimmed;


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
rr_data(:,2) = table2array(readtable("CFD_M_30knots.csv"));

%rr_data(:,3) = table2array(readtable("CFD_M_27knots.csv"));
%rr_data(:,4) = table2array(readtable("CFD_M_30knots.csv"));

% rr_data(:,2) =  flip(rr_data(:,2));


% rr_data1 = table2array(readtable("CFD_x.csv"));
% rr_data1 = rr_data1(1:100);
% rr_data2 = table2array(readtable("CFD_M_22knots.csv"));
% rr_data2 = flip(rr_data2);

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
hold on
%plot(x_pos(1:12),M_isen(2:13),'k--square','LineWidth',2)
plot(x_pos(1:13),M_isen(2:14),'ksquare','LineWidth',3)
plot(rr_data(10:200,1),rr_data(10:200,2),'bx','LineWidth',1.3)
%plot(rr_data(10:200,1),rr_data(10:200,3),'kx','LineWidth',1.3)
%plot(rr_data(10:200,1),rr_data(10:200,4),'rx','LineWidth',1.3)
%plot(rr_data(10:100,1)./1.3,rr_data(100:190,2),'b','LineWidth',1.3)
%plot(rr_data1,rr_data2,'b','LineWidth',1.3)
box on
pbaspect([1 1 1])
ylim([0.2 1.7])
xlim([-0.01 0.43])
set(gca,'linewidth',1.3)
set(gca,'TickLabelInterpreter','latex')
set(gca,'fontsize', 26) 
ylabel('Isentropic Mach number','interpreter','latex')
xlabel('x/D','interpreter','latex')
hold off


cd(pwd);



