clc
clear all
%% RMS V2

% Load the video
videoFile = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\Rolls Lip\Rolls_1_C001H001S0040\Rolls_1_C001H001S0040.mp4'; % Change this to your video file path
videoObject = VideoReader(videoFile);

% Initialize a matrix to accumulate the squares of pixel values
numFrames = videoObject.NumFrames;
frameSize = [videoObject.Height, videoObject.Width];
sumSquares = zeros(frameSize);

% Read frames and compute the sum of squares
while hasFrame(videoObject)
    frame = readFrame(videoObject);
    if size(frame, 3) == 3
        grayFrame = rgb2gray(frame); % Convert to grayscale if the video is in color
    else
        grayFrame = frame; % Use the frame directly if it is already in grayscale
    end
    sumSquares = sumSquares + double(grayFrame).^2;
end

% Calculate RMS
rmsImage = sqrt(sumSquares / numFrames);

% Normalize the RMS image to the range [0, 1] and invert it
rmsImageNormalized = mat2gray(rmsImage);
rmsImageInverted = 1 - rmsImageNormalized;  % Inverting the image

% Save the inverted RMS image as PNG
outputFile = 'rms_inverted_output28.png';
imwrite(rmsImageInverted, outputFile);

% Optionally, display the image
imshow(rmsImageInverted);
title('Inverted RMS of Video Pixels');

%%

% Load the video
videoFile = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\Rolls Lip\Rolls_1_C001H001S0040\Rolls_1_C001H001S0040.mp4'; % Change this to your video file path
videoObject = VideoReader(videoFile);

% Initialize a matrix to accumulate the squares of pixel values
numFrames = videoObject.NumFrames;
frameSize = [videoObject.Height, videoObject.Width];
sumSquares = zeros(frameSize);

% Read frames and compute the sum of squares
while hasFrame(videoObject)
    frame = readFrame(videoObject);
    if size(frame, 3) == 3
        grayFrame = rgb2gray(frame); % Convert to grayscale if the video is in color
    else
        grayFrame = frame; % Use the frame directly if it is already in grayscale
    end
    sumSquares = sumSquares + double(grayFrame).^2;
end

% Calculate RMS
rmsImage = sqrt(sumSquares / numFrames);

% Enhance contrast of the RMS image
% Normalize the image and then scale the pixel values to stretch the contrast
rmsImageNormalized = mat2gray(rmsImage);
rmsImageEnhanced = imadjust(rmsImageNormalized);

% Save the enhanced RMS image as PNG
outputFile = 'rms_enhanced_output.png';
imwrite(rmsImageEnhanced, outputFile);

% Optionally, display the image
imshow(rmsImageEnhanced);
title('Enhanced RMS of Video Pixels');

%%

% Load the video
videoFile = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\Rolls Lip\Rolls_1_C001H001S0040\Rolls_1_C001H001S0040.mp4'; % Change this to your video file path
videoObject = VideoReader(videoFile);

% Initialize a matrix to accumulate the squares of pixel values
numFrames = videoObject.NumFrames;
frameSize = [videoObject.Height, videoObject.Width];
sumSquares = zeros(frameSize);

% Read frames and compute the sum of squares
while hasFrame(videoObject)
    frame = readFrame(videoObject);
    if size(frame, 3) == 3
        grayFrame = rgb2gray(frame); % Convert to grayscale if the video is in color
    else
        grayFrame = frame; % Use the frame directly if it is already in grayscale
    end
    sumSquares = sumSquares + double(grayFrame).^2;
end

% Calculate RMS
rmsImage = sqrt(sumSquares / numFrames);

% Normalize the RMS image to the range [0, 1] for better visualization
rmsImageNormalized = mat2gray(rmsImage);

% Save the RMS image as PNG
outputFile = 'rmstest.png';
imwrite(rmsImageNormalized, outputFile);

% Optionally, display the image
imshow(rmsImageNormalized);
title('RMS of Video Pixels');
