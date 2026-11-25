clc
clear all
close all
%% Standard deviation and Time-Averaged Image

% Read the video file
v = VideoReader('F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_48_C001H001S0001\2024_Schlieren_48_C001H001S0001.mp4');
    % Change the file name after each run
%v = VideoReader('F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\Rolls Lip\Rolls_1_C001H001S0038\Rolls_1_C001H001S0038.mp4')

% Initialize matrices to store the sum and sum of squares
numFrames = floor(v.Duration * v.FrameRate);
frameSize = [v.Height, v.Width];
sumFrames = zeros(frameSize);
sumSquares = zeros(frameSize);

% Process each frame to compute the sum and sum of squares
frameCount = 0;
while hasFrame(v)
    frame = readFrame(v);
    if size(frame, 3) == 3
        frame = rgb2gray(frame); % Convert to grayscale if it's a color video
    end
    frame = double(frame);
    
    % Update sum and sum of squares
    sumFrames = sumFrames + frame;
    sumSquares = sumSquares + frame.^2;
    frameCount = frameCount + 1;
end

% Calculate the mean (time-averaged) and standard deviation
meanFrames = sumFrames / frameCount;
stdDeviations = sqrt((sumSquares / frameCount) - meanFrames.^2);

% Normalize the standard deviation values to [0, 1] for visualization
normalizedStdDev = mat2gray(stdDeviations);

% Create an image where high values (dark) indicate high std deviation
% This is the direct visualization, not inverted
stdDevImage = 1 - normalizedStdDev;

% Normalize the time-averaged image to [0, 1] for visualization
normalizedMeanFrames = mat2gray(meanFrames);

%% Image manipulation

% Rotate and crop the images using the specified parameters
rotationAngle = -50; % Adjust this angle as needed
%cropRect = [400, 480, 787, 500]; % Value for Rolls Lip Campaign
    % Makes a resolution of 1198 x 730, 1.641
cropRect = [488, 410, 420, 250]; % Value for 2024 Campaign

% Rotate and crop standard deviation image
rotatedStdDevImage = imrotate(stdDevImage, rotationAngle);
croppedStdDevImage = imcrop(rotatedStdDevImage, cropRect);

% Rotate and crop time-averaged image
rotatedMeanImage = imrotate(normalizedMeanFrames, rotationAngle);
croppedMeanImage = imcrop(rotatedMeanImage, cropRect);

Name_TA = 'Test'
Name_STD = 'TestSTD'

% Display and save the standard deviation image
figure;
imshow(croppedStdDevImage);
colormap((gray)); % Flips the gray scale to make dark high, light low
cb = colorbar; % Adds a color bar to indicate the scale of standard deviation
cb.Ticks = []; % Remove tick marks from the color bar
caxis([0 1]); % Sets the limits of the color scale to match the normalized data
set(cb, 'YDir', 'reverse');
print(gcf,Name_STD, '-dsvg');
print(gcf, Name_STD, '-dpdf', '-bestfit');

% Save the standard deviation image as a .pdf vectorized image
%print(gcf, 'stddev_image.pdf', '-dpdf', '-bestfit');
%exportgraphics(gcf, 'STD_2024_28-42-42.pdf', 'ContentType', 'vector');


% Display and save the time-averaged image
figure;
imshow(croppedMeanImage);
print(gcf,Name_TA, '-dsvg');
print(gcf, Name_TA, '-dpdf', '-bestfit');



% colormap((gray)); % Flips the gray scale to make dark high, light low
% cb = colorbar; % Adds a color bar to indicate the scale of the time-averaged intensity
% cb.Ticks = []; % Remove tick marks from the color bar
% caxis([0 1]); % Sets the limits of the color scale to match the normalized data
% set(cb, 'YDir', 'reverse');
% Save the time-averaged image as a .pdf vectorized image
%print(gcf, 'mean_image.pdf', '-dpdf', '-bestfit');

% exportgraphics(gcf, 'TA_2024_28-42-42.pdf', 'ContentType', 'vector');
% exportgraphics(gcf, 'TA_2024_28-42-42.svg', 'ContentType', 'vector');
