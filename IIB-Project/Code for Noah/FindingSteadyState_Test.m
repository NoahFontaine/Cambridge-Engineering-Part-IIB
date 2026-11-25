% Save the original directory
originalDir = pwd;

% Change the directory to the location of your pressure file. Probably best
% to also keep the x locations in the same directory.
cd('F:\Dropbox Data\Data\Data\Pressure - Master\Pressure - Synced');
%%

% Load the data
data = readtable('2024_p_0024.csv'); % Assuming the pressure data is in the second column

% Display the column names to identify the correct name for the time column
disp(data.Properties.VariableNames);

% Extract the pressure data as a numeric array
pressure = table2array(data(:,2));

% Define parameters for steady state detection
windowSize = 100; % Initial size of the moving window to calculate the moving standard deviation
threshold = 0.01; % Initial threshold for the moving standard deviation to consider pressure constant

% Calculate the moving standard deviation
movingStdDev = movstd(pressure, windowSize);

% Plot the moving standard deviation to help adjust the threshold
figure;
plot(movingStdDev);
xlabel('Index');
ylabel('Moving Standard Deviation');
title('Moving Standard Deviation of Pressure Data');

% Adjust windowSize and threshold if needed
% For example, if the plot shows that a threshold of 0.01 is too low or too high,
% try setting it to a value that better separates the steady state period from the rest.

% Find the indices where the moving standard deviation is below the threshold
steadyStateIndices = find(movingStdDev < threshold);

% Check if we have found a steady state region
if isempty(steadyStateIndices)
    error('No steady state period found. Adjust the window size or threshold.');
end

% Identify the start and end of the steady state period
steadyStateStart = steadyStateIndices(1);
steadyStateEnd = steadyStateIndices(end);

% Extract the steady state data
steadyStatePressure = pressure(steadyStateStart:steadyStateEnd);

% Assuming you have a time column, use the correct name
% Replace 'YourTimeColumnName' with the actual column name from the display output
timeColumnName = 'YourTimeColumnName'; % Update this based on the actual column name from disp output
steadyStateTime = data.(timeColumnName)(steadyStateStart:steadyStateEnd);

% Plot the original and steady state data for visualization
figure;
plot(data.(timeColumnName), pressure);
hold on;
plot(steadyStateTime, steadyStatePressure, 'r', 'LineWidth', 2);
xlabel('Time');
ylabel('Pressure');
legend('Original Data', 'Steady State Data');
title('Steady State Detection in Pressure Data');
hold off;

% Change back to the original directory
cd(originalDir);
