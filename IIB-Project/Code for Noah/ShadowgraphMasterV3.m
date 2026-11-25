clc;
clear all;
close all;

%% Calculate Global Min and Max Std Dev

% List of video files to process
videoFiles = {
    'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_22_C001H001S0001\2024_Schlieren_22_C001H001S0001.mp4'
    % Unsteady case
    %'F:\PhD\Thesis data\Data master\Shadowgraph & Schlieren\Trimmed videos for MFS\2024_28_42.mp4',
    % 42-42
    %'F:\PhD\Thesis data\Data master\Shadowgraph & Schlieren\Trimmed videos for MFS\2024_28_315.mp4',
    % 31.5-42
    %'F:\PhD\Thesis data\Data master\Shadowgraph & Schlieren\Trimmed videos for MFS\2024_28_21.mp4',
    % 21-42
    %'F:\PhD\Thesis data\Data master\Shadowgraph & Schlieren\Trimmed videos for MFS\2024_28_105.mp4';
    % 10.5-42
    %'F:\PhD\Thesis data\Data master\Shadowgraph & Schlieren\Trimmed videos for MFS\2024_28_0.mp4';
    % 0-42
};

globalMinStd = Inf;
globalMaxStd = -Inf;

for k = 1:length(videoFiles)
    if exist(videoFiles{k}, 'file') ~= 2
        error(['The file "', videoFiles{k}, '" was not found. Please check the path and try again.']);
    end
    
    v = VideoReader(videoFiles{k});

    sumFrames = zeros(v.Height, v.Width);
    sumSquares = zeros(v.Height, v.Width);
    frameCount = 0;
    
    while hasFrame(v)
        frame = readFrame(v);
        if size(frame, 3) == 3
            frame = rgb2gray(frame); % Convert to grayscale if it's a color video
        end
        frame = double(frame);
        
        sumFrames = sumFrames + frame;
        sumSquares = sumSquares + frame.^2;
        frameCount = frameCount + 1;
    end
    
    meanFrames = sumFrames / frameCount;
    stdDeviations = sqrt((sumSquares / frameCount) - meanFrames.^2);
    
    % Update global min and max std deviation values
    globalMinStd = min(globalMinStd, min(stdDeviations(:)));
    globalMaxStd = max(globalMaxStd, max(stdDeviations(:)));
end

%% Process and Normalize Each Video

% Adjust this section to process and save each video file
for k = 1:length(videoFiles)
    if exist(videoFiles{k}, 'file') ~= 2
        error(['The file "', videoFiles{k}, '" was not found. Please check the path and try again.']);
    end
    
    v = VideoReader(videoFiles{k});
    
    sumFrames = zeros(v.Height, v.Width);
    sumSquares = zeros(v.Height, v.Width);
    frameCount = 0;
    
    while hasFrame(v)
        frame = readFrame(v);
        if size(frame, 3) == 3
            frame = rgb2gray(frame); % Convert to grayscale if it's a color video
        end
        frame = double(frame);
        
        sumFrames = sumFrames + frame;
        sumSquares = sumSquares + frame.^2;
        frameCount = frameCount + 1;
    end
    
    meanFrames = sumFrames / frameCount;
    stdDeviations = sqrt((sumSquares / frameCount) - meanFrames.^2);
    
    % Normalize std deviation values using global min and max
    normalizedStdDev = (stdDeviations - globalMinStd) / (globalMaxStd - globalMinStd);
    
    % Create an image where high values (dark) indicate high std deviation
    stdDevImage = 1 - normalizedStdDev;
    
    % Normalize the time-averaged image to [0, 1] for visualization
    normalizedMeanFrames = mat2gray(meanFrames);
    
    %% Image manipulation
    
    % Rotate and crop the images using the specified parameters
    rotationAngle = -50; % Adjust this angle as needed
    %cropRect = [488, 410, 420, 250]; % Value for 2024 Campaign
    cropRect = [150, 150, 250, 180]; % Value needed for the zoomed unsteady settings
    
    % Rotate and crop standard deviation image
    rotatedStdDevImage = imrotate(stdDevImage, rotationAngle);
    croppedStdDevImage = imcrop(rotatedStdDevImage, cropRect);
    
    % Rotate and crop time-averaged image
    rotatedMeanImage = imrotate(normalizedMeanFrames, rotationAngle);
    croppedMeanImage = imcrop(rotatedMeanImage, cropRect);
    
    % Set file names for output
    Name_TA = ['TA_', num2str(k)];
    Name_STD = ['STD_', num2str(k)];
    
    % Display and save the standard deviation image
    figure;
    imshow(croppedStdDevImage);
    colormap((gray)); % Flips the gray scale to make dark high, light low
    cb = colorbar; % Adds a color bar to indicate the scale of standard deviation
    cb.Ticks = []; % Remove tick marks from the color bar
    caxis([0 1]); % Sets the limits of the color scale to match the normalized data
    set(cb, 'YDir', 'reverse');
    print(gcf, Name_STD, '-dsvg');
    print(gcf, Name_STD, '-dpdf', '-bestfit');
    
    % Display and save the time-averaged image
    figure;
    imshow(croppedMeanImage);
    print(gcf, Name_TA, '-dsvg');
    print(gcf, Name_TA, '-dpdf', '-bestfit');
end
