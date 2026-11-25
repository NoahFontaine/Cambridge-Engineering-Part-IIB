clear all
clc
%% Script to get the standard deviation of pixel intensity from Shadowgraph/Schlieren MP4

% Define input video file
videoFile = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_1_C001H001S0001\2024_Schlieren_1_C001H001S0001.mp4';

% Open video file to get video properties
videoObj = VideoReader(videoFile);
numFrames = videoObj.NumberOfFrames;
frameHeight = videoObj.Height;
frameWidth = videoObj.Width;

% Initialize arrays to store sum of pixel intensities and sum of squared pixel intensities
sumPixelIntensities = zeros(frameHeight, frameWidth);
sumSquaredPixelIntensities = zeros(frameHeight, frameWidth);

% Loop through each frame in the video
for frameIndex = 1:numFrames
    % Read frame from video
    frame = read(videoObj, frameIndex);
    
    % Convert frame to grayscale
    frameGray = rgb2gray(frame);
    
    % Update sum of pixel intensities and sum of squared pixel intensities arrays
    sumPixelIntensities = sumPixelIntensities + double(frameGray);
    sumSquaredPixelIntensities = sumSquaredPixelIntensities + double(frameGray).^2;
end

% Calculate mean pixel intensity and standard deviation for each pixel location
meanPixelIntensity = sumPixelIntensities / numFrames;
meanSquaredPixelIntensity = sumSquaredPixelIntensities / numFrames;
stdDeviation = sqrt(meanSquaredPixelIntensity - meanPixelIntensity.^2);

% Save the final standard deviation values as PNG
imwrite(uint8(stdDeviation), 'final_std_deviation.png');

