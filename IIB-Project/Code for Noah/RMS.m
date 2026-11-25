% Clear all variables, close all figures, and clear the command window
clear all
clc

%% Script to get the RMS of pixel intensity from Shadowgraph/Schlieren MP4

% Load the video file
video = VideoReader('F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_17_C001H001S0001\2024_Schlieren_17_C001H001S0001.mp4');

% Initialize matrices to store the sum of squares of pixel values
sumIntensitySquared = zeros(video.Height, video.Width);
numFrames = 0;

% Process each frame individually
while hasFrame(video)
    frame = readFrame(video);
    % Convert frame to grayscale
    grayFrame = double(rgb2gray(frame));

    % Update the sum of squares
    sumIntensitySquared = sumIntensitySquared + grayFrame.^2;
    numFrames = numFrames + 1;
end

% Calculate the mean squared intensity
meanSquaredIntensity = sumIntensitySquared / numFrames;

% Calculate the root mean squared intensity
rootMeanSquaredIntensity = sqrt(meanSquaredIntensity);

% Invert the RMS values
invertedRMS = max(rootMeanSquaredIntensity(:)) - rootMeanSquaredIntensity;

% Normalize the inverted RMS values to the range [0, 1]
invertedRMSNormalized = (invertedRMS - min(invertedRMS(:))) / (max(invertedRMS(:)) - min(invertedRMS(:)));

% Display the RMS image
imshow(invertedRMSNormalized, []);
title('Root Mean Squared Intensity of Pixel Intensities (Inverted)');

% Save the image as a PNG
imwrite(invertedRMSNormalized, 'pixel_rms_intensity_inverted.png');
