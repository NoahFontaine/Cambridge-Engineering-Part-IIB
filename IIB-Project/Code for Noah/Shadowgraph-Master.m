clc
clear all
%%
% Define the paths for the input files and output
backgroundImagePath = 'ShadowgraphBackground.png';
videoPath = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_43_C001H001S0001\2024_Schlieren_43_C001H001S0001.mp4';
outputImagePath = 'output_image.png';

% Read the background image
backgroundImage = imread(backgroundImagePath);
backgroundImage = double(backgroundImage); % Convert to double for processing

% Create a video reader object
videoReader = VideoReader(videoPath);

% Initialize a variable to accumulate frames
accumulatedImage = zeros(videoReader.Height, videoReader.Width);

% Read and process each frame
frameCount = 0;
while hasFrame(videoReader)
    frame = readFrame(videoReader);
    frame = double(frame); % Convert frame to double for processing
    
    % Subtract the background image from the frame
    % Ensure the background is resized or cropped appropriately if it doesn't match frame size
    processedFrame = frame - backgroundImage;
    
    % Accumulate the processed frames
    accumulatedImage = accumulatedImage + processedFrame;
    
    frameCount = frameCount + 1;
end

% Average the accumulated frames
if frameCount > 0
    averagedImage = accumulatedImage / frameCount;
else
    error('No frames were processed.');
end

% Convert to grayscale (if the image is not already in grayscale)
if size(averagedImage, 3) == 3
    averagedImage = rgb2gray(averagedImage);
end

% Display the result
imshow(averagedImage, []);
title('Time-Averaged Processed Image');

% Save the output image
imwrite(uint8(averagedImage), outputImagePath);
