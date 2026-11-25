%% Heatmap script

currentDir = pwd;
cd('F:\PhD\Thesis data\Data master\Isentropic Mach number\Distribution around the lip\Isentropic Mach number values')

% Step 1: Load the CSV file
filename = 'M_isen_peak.csv'; % Replace 'yourfile.csv' with your actual CSV file name
data = readmatrix(filename);

% Flip the data matrix in the y direction
data = flipud(data);

figure;

% Set the size of the figure for an A4 page
width = 15;  % Width in centimeters (160 mm)
height = 12.5; % Height in centimeters (100 mm)
set(gcf, 'Units', 'centimeters', 'Position', [5, 5, width, height]); % Position: [left, bottom, width, height]

xValues = {'1', '0.75', '0.5', '0.25', '0'};
yValues = {'0.17','0.165','0.16','0.155','0.15','0.145','0.14','0.135','0.13','0.125','0.12'}; % Reversed yValues

% Step 2: Create the heatmap
h = heatmap(data);

h.XDisplayLabels = xValues;
h.YDisplayLabels = yValues;

% Step 3: Customize the heatmap to remove cell labels
h.CellLabelColor = 'none';

% Step 4: Set the colormap
colormap('hot');

% Step 5: Adjust color scaling and set a specific color for value 1
minValue = min(data(:));
maxValue = max(data(:));
caxis([minValue maxValue]); % Adjust the color axis limits

% Optional: Further customize the heatmap
h.YLabel = 'Entry Mach number'; % Replace with your actual X-axis label
h.XLabel = 'Choke setting'; % Replace with your actual Y-axis label

fig = gcf; % Get the current figure handle
fig.PaperPositionMode = 'auto'; % Ensure the figure size is as displayed on screen
print('heatmap2.svg', '-dsvg'); % Save the figure as an SVG file

cd(currentDir)
