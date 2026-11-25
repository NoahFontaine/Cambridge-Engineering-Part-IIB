function [start_time, end_time, trimmed_data] = RunStartEnd(filename, window_size, std_threshold_start, mean_change_threshold_start, std_threshold_end, mean_change_threshold_end, ignore_time, end_buffer_time)
    % Load the data from the CSV file
    data = readtable(filename); % Adjust the filename accordingly
    time = data{:,1}; % Assuming time is the first column
    pressure_data = data{:,2:end}; % Assuming the remaining columns are pressure data

    % Find the index to start after ignoring initial time
    start_index = find(time > ignore_time, 1);

    % Initialize variables
    num_points = length(pressure_data(:,1));
    moving_std = zeros(num_points - window_size + 1, 1);
    moving_mean = zeros(num_points - window_size + 1, 1);

    % Use the first pressure column for detecting stabilization and end
    pressure = pressure_data(:,1);

    % Calculate moving statistics, ignoring the initial period
    for i = start_index:(num_points - window_size + 1)
        window_data = pressure(i:i + window_size - 1);
        moving_std(i) = std(window_data);
        moving_mean(i) = mean(window_data);
    end

    % Detect when the tunnel is fully established
    established_index = -1; % Initialize as -1 (not found)
    for i = (start_index + 1):length(moving_std)
        if moving_std(i) < std_threshold_start && abs(moving_mean(i) - moving_mean(i-1)) < mean_change_threshold_start
            established_index = i + window_size - 1; % Adjust for the window offset
            break;
        end
    end

    % Detect when the tunnel run is ending
    ending_index = -1; % Initialize as -1 (not found)
    buffered_ending_index = -1; % Initialize as -1 (not found)
    if established_index ~= -1
        for i = (established_index + 1):length(moving_std)
            if moving_std(i) > std_threshold_end || abs(moving_mean(i) - moving_mean(i-1)) > mean_change_threshold_end
                ending_index = i + window_size - 1; % Adjust for the window offset

                % Find the index 3 seconds before the detected end
                end_time_point = time(ending_index) - end_buffer_time;
                buffered_ending_index = find(time <= end_time_point, 1, 'last');
                break;
            end
        end
    end

    % Assign output times
    if established_index ~= -1
        start_time = time(established_index);
    else
        start_time = NaN;
    end

    if buffered_ending_index ~= -1
        end_time = time(buffered_ending_index);
    else
        end_time = NaN;
    end

    % Trim the data
    if ~isnan(start_time) && ~isnan(end_time)
        trimmed_indices = (time >= start_time) & (time <= end_time);
        trimmed_time = time(trimmed_indices);
        trimmed_pressure_data = pressure_data(trimmed_indices, :);
        trimmed_data = array2table([trimmed_time trimmed_pressure_data], 'VariableNames', data.Properties.VariableNames);
    else
        trimmed_data = table();
    end

    % Display the result
    if ~isnan(start_time)
        fprintf('The tunnel is fully established at time %.2f seconds.\n', start_time);
    else
        fprintf('The tunnel stabilization point was not found within the data.\n');
    end

    if ~isnan(end_time)
        fprintf('The tunnel run ends at time %.2f seconds.\n', end_time);
    else
        fprintf('The tunnel run end point was not found within the data.\n');
    end

    % Plot the data for visualization
    figure;
    subplot(2,1,1);
    plot(time, pressure);
    hold on;
    if ~isnan(start_time)
        plot(start_time, pressure(time == start_time), 'ro');
    end
    if ~isnan(end_time)
        plot(end_time, pressure(time == end_time), 'go');
        if ~isnan(start_time)
            legend('Pressure Trace', 'Stabilization Point', 'End Point');
        else
            legend('Pressure Trace', 'End Point');
        end
    else
        if ~isnan(start_time)
            legend('Pressure Trace', 'Stabilization Point');
        end
    end
    title('Pressure Trace');
    xlabel('Time');
    ylabel('Pressure');
    grid on;

    subplot(2,1,2);
    plot(time(start_index:length(moving_std)), moving_std(start_index:end));
    title('Moving Standard Deviation of Pressure (Ignoring First 10 Seconds)');
    xlabel('Time');
    ylabel('Standard Deviation');
    grid on;
end
