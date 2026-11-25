function [run_start, run_end] = selectStartEnd(filename)
    % Load the pressure values from a CSV file
    pressureValues = readmatrix(filename);  % Read data from CSV file
    
    % Check if the loaded data is a vector or a matrix
    if ismatrix(pressureValues) && size(pressureValues, 2) > 1
        % If the data has more than one column, we assume the pressure values
        % are in the first column
        pressureValues = pressureValues(:, 5);
    end
    
    % Plot the pressure values
    figure;
    plot(pressureValues);
    title('Pressure Values');
    xlabel('Time');
    ylabel('Pressure');
    hold on;
    
    % Display instructions
    disp('Click on the plot to select the start and end points of the run.');
    
    % Allow user to select start and end points
    [x, ~] = ginput(2);
    
    % Ensure the points are within valid range
    x = round(x);
    x(x < 1) = 1;
    x(x > length(pressureValues)) = length(pressureValues);

    run_start = min(x);
    run_end = max(x);
    
    % Highlight the selected points on the plot
%     plot(startPoint, pressureValues(startPoint), 'go', 'MarkerSize', 10, 'LineWidth', 2);
%     plot(endPoint, pressureValues(endPoint), 'ro', 'MarkerSize', 10, 'LineWidth', 2);
%     line([startPoint, startPoint], ylim, 'Color', 'g', 'LineStyle', '--');
%     line([endPoint, endPoint], ylim, 'Color', 'r', 'LineStyle', '--');
    
    % Display the selected points
    disp(['Start point: ', num2str(run_start), ', Pressure: ', num2str(pressureValues(run_start))]);
    disp(['End point: ', num2str(run_end), ', Pressure: ', num2str(pressureValues(run_end))]);
    
    hold off;
end