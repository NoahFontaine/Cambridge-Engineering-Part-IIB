%% M_isentropic comparison
% Use this script to compare different cases. Use the other scripts  to
% trim and save the .mats. Then load them into this script and plot them. 

%% Plots Misen against normalised x

currentDir = pwd;
cd('F:\PhD\Thesis data\Data master\Isentropic Mach number\Distribution around the lip\Isentropic Mach number values')


%alpha32 = load("M_isen_32_42.mat");
%alpha28 = load("M_isen_28_42.mat");
%alpha34 = load("M_isen_34_42.mat");
%alpha24 = load("M_isen_24_42.mat");
alpha268 = load("M_isen_268_42.mat")
alpha24 = load("M_isen_24_42.mat")

cd(pwd);


x_pos= table2array(readtable("F:\Dropbox Data\Data\Data\Pressure - Master\RRLip_x_newtapsused.csv"));

% Create a new figure
figure;

% Set the size of the figure for an A4 page
width = 20;  % Width in centimeters (160 mm)
height = 12.5; % Height in centimeters (100 mm)
set(gcf, 'Units', 'centimeters', 'Position', [5, 5, width, height]); % Position: [left, bottom, width, height]

% Plot the first data set
hold on;

% Plot the second data set
% plot(x_pos(1:12), alpha28.M_isen(2:13), 'k--square', 'LineWidth', 1.2);
% plot(x_pos(1:12), alpha24.M_isen(2:13), 'r--x', 'LineWidth', 1.2);
% plot(x_pos(1:12), alpha34.M_isen(2:13), 'b--o', 'LineWidth', 1.2);

plot(x_pos(1:12), alpha268.M_isen(2:13), 'k--square', 'LineWidth', 1.2);
plot(x_pos(1:12), alpha24.M_isen(2:13), 'r--x', 'LineWidth', 1.2);

% Customize the plot appearance
box on;
pbaspect([1 1 1]);

% ylim([0.3 1.6]);
% xlim([-0.01 0.5])

% ylim([0.4 1.45]);
% xlim([-0.01 0.5])
% 
ylim([0.8 1.5]);
xlim([-0.005 0.15])


set(gca, 'linewidth', 1.3);
set(gca, 'TickLabelInterpreter', 'latex');
set(gca, 'FontSize', 14); % Set font size for tick labels

% Set font size for labels
ylabel('Isentropic Mach number', 'interpreter', 'latex', 'FontSize', 14);
xlabel('x/D', 'interpreter', 'latex', 'FontSize', 14);

%legend({'Closed', 'Half-open','open'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.635, 0.8, 0.1, 0.1]);
%legend({'Attached: High-speed', 'Separated: High-speed','Attached: Low-speed'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.585, 0.8, 0.1, 0.1]);
legend({'Pre-separation', 'Post-separation'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.615, 0.8, 0.1, 0.1]);

% Ensure the figure remains the specified size
set(gcf, 'PaperUnits', 'centimeters');
set(gcf, 'PaperPosition', [0, 0, width, height]); % [left, bottom, width, height]

% Export the figure as an SVG file
print(gcf, 'test2.svg', '-dsvg');

%%
% % Create a new figure
% figure;
% 
% % Set the size of the figure for an A4 page
% width = 20;  % Width in centimeters (160 mm)
% height = 12.5; % Height in centimeters (100 mm)
% set(gcf, 'Units', 'centimeters', 'Position', [5, 5, width, height]); % Position: [left, bottom, width, height]
% 
% % Plot the first data set
% hold on;
% 
% % Plot the second data set
% plot(x_pos(1:12), alpha28.M_isen(2:13), 'k--square', 'LineWidth', 1.2);
% plot(x_pos(1:12), alpha34.M_isen(2:13), 'b--o', 'LineWidth', 1.2);
% plot(x_pos(1:12), alpha24.M_isen(2:13), 'r--x', 'LineWidth', 1.2);
% 
% % close up plot
% box on;
% pbaspect([1 1 1]);
% ylim([0.6 1.4]);
% xlim([-0.01 0.15])
% set(gca, 'linewidth', 1.3);
% set(gca, 'TickLabelInterpreter', 'latex');
% set(gca, 'FontSize', 10); % Set font size for tick labels
% 
% % Set font size for labels
% ylabel('Isentropic Mach number', 'interpreter', 'latex', 'FontSize', 12);
% xlabel('x/D', 'interpreter', 'latex', 'FontSize', 12);
% 
% %legend({'Closed', 'Half-open','open'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.635, 0.8, 0.1, 0.1]);
% legend({'Attached: High-speed', 'Attached: Low-speed','Separated: High-speed'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.585, 0.8, 0.1, 0.1]);
% %legend({'Pre-separation', 'Post-separation'}, 'Interpreter', 'latex', 'FontSize', 10, 'Position', [0.615, 0.8, 0.1, 0.1]);
% 
% % Ensure the figure remains the specified size
% set(gcf, 'PaperUnits', 'centimeters');
% set(gcf, 'PaperPosition', [0, 0, width, height]); % [left, bottom, width, height]
% 
% % Export the figure as an SVG file
% print(gcf, 'alpha_test_close.svg', '-dsvg');
% 


cd(currentDir)