currentDir = pwd;
cd('F:\PhD\Thesis data\Data master\Boundary layer\Displacement thicknesses')

figure

width = 20;  % Width in centimeters (160 mm)
height = 12.5; % Height in centimeters (100 mm)

% Step 1: Load the CSV file
filename = 'displacementthickness_alpha.csv'; % Replace 'yourfile.csv' with your actual CSV file name
data = readmatrix(filename);

% Plot the data
plot(data,'ko--', 'LineWidth', 1.5); % Adjust LineWidth for better visibility

% Customize the plot appearance
box on;
pbaspect([1 1 1]);
% ylim([0.3 1.6]);
% xlim([-0.01 0.5]);
set(gca, 'LineWidth', 1.3);
set(gca, 'TickLabelInterpreter', 'latex');
set(gca, 'FontSize', 10); % Set font size for tick labels

% Set font size for labels
xlabel('Entry Mach number', 'Interpreter', 'latex', 'FontSize', 12);
ylabel('Displacement thickness (mm)', 'Interpreter', 'latex', 'FontSize', 12);

% Define the x values for the x-axis
%xValues = {'0.17','0.165','0.16','0.155','0.15','0.145','0.14','0.135','0.13','0.125','0.12'}; % Reversed yValues
xValues = {'0.105','0.110','0.115','0.120','0.125','0.130','0.135','0.140','0.145','0.150','0.155','0.160','0.165','0.17'}

% Set the x-axis tick positions and labels
set(gca, 'XTick', 1:length(xValues)); % Positions for the ticks
set(gca, 'XTickLabel', xValues); % Labels for the ticks

% Optional: Set legend
% legend({'Closed', 'Half-open','open'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.635, 0.8, 0.1, 0.1]);
% legend({'Attached: High-speed', 'Attached: Low-speed','Separated: High-speed'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.585, 0.8, 0.1, 0.1]);
% legend({'Pre-separation', 'Post-separation'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.615, 0.8, 0.1, 0.1]);
% legend({'42/42', '31.5/42', '21/42'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.3, 0.8, 0.1, 0.1]);

% Ensure the figure remains the specified size
set(gcf, 'PaperUnits', 'centimeters');
set(gcf, 'PaperPosition', [0, 0, width, height]); % [left, bottom, width, height]

% Save the current directory
cd(currentDir);
