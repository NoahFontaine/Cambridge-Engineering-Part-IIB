%% Peak Mach number (varying Alpha)

clear all
close all

%%

currentDir = pwd;
cd('F:\PhD\Thesis data\Data master\Isentropic Mach number\Distribution around the lip\Isentropic Mach number values')

% Step 1: Load the CSV file
filename = 'M_isen_peak.csv'; % Replace 'yourfile.csv' with your actual CSV file name
data = readmatrix(filename);

% Flip the data matrix in the y direction
data = flipud(data);

M_42 = data(:,1)
M_42 = flip(M_42)

%% Plotting

plot(M_42,'ko--', 'LineWidth', 1.5)
hold on

% Customize the plot appearance
box on;
pbaspect([1 1 1]);
% ylim([0.3 1.6]);
%xlim([0.115 0.175]);
set(gca, 'LineWidth', 1.3);
set(gca, 'TickLabelInterpreter', 'latex');
set(gca, 'FontSize', 12); % Set font size for tick labels

% Set font size for labels
xlabel('Entry Mach number', 'Interpreter', 'latex', 'FontSize', 12);
ylabel('Peak Isentropic Mach number', 'Interpreter', 'latex', 'FontSize', 12);

% Define the x values for the x-axis
%xValues = {'0.170','0.165','0.160','0.155','0.150','0.145','0.140','0.135','0.130','0.25','0.120'}; % Reversed yValues
xValues = {'0.120','0.125','0.130','0.135','0.140','0.145','0.150','0.155','0.160','0.165','0.170'}
% Set the x-axis tick positions and labels
set(gca, 'XTick', 1:length(xValues)); % Positions for the ticks
set(gca, 'XTickLabel', xValues); % Labels for the ticks

hold off


cd(pwd)

% Create the figure and plot the data
figure;
plot(M_42, 'ko--', 'LineWidth', 1.5);
hold on;

% Plot the specific point
plot(8.5, 1.4381, 'bx', 'MarkerSize', 12, 'LineWidth', 1.5);

% Customize the plot appearance
box on;
pbaspect([1 1 1]);
% ylim([0.3 1.6]);
%xlim([0.115 0.175]);
set(gca, 'LineWidth', 1.3);
set(gca, 'TickLabelInterpreter', 'latex');
set(gca, 'FontSize', 12); % Set font size for tick labels

% Set font size for labels
xlabel('Entry Mach number', 'Interpreter', 'latex', 'FontSize', 12);
ylabel('Peak Isentropic Mach number', 'Interpreter', 'latex', 'FontSize', 12);

% Define the x values for the x-axis
%xValues = {'0.170','0.165','0.160','0.155','0.150','0.145','0.140','0.135','0.130','0.25','0.120'}; % Reversed yValues
xValues = {'0.120','0.125','0.130','0.135','0.140','0.145','0.150','0.155','0.160','0.165','0.170'};
% Set the x-axis tick positions and labels
set(gca, 'XTick', 1:length(xValues)); % Positions for the ticks
set(gca, 'XTickLabel', xValues); % Labels for the ticks

hold off;