clc
clear all
%%
% Define the paths for the input files and output
backgroundImagePath = 'ShadowgraphBackground.png';
videoPath = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_43_C001H001S0001\2024_Schlieren_43_C001H001S0001.mp4';
outputVideoPath = 'output_video.avi';

% Read the background image
backgroundImage = imread(backgroundImagePath);
backgroundImage = double(rgb2gray(backgroundImage)); % Convert to double and to grayscale for processing

% Create a video reader object
videoReader = VideoReader(videoPath);
videoWriter = VideoWriter(outputVideoPath, 'Grayscale AVI');
open(videoWriter);

% Initialize a variable to accumulate frames
accumulatedImage = zeros(videoReader.Height, videoReader.Width);
frameCount = 0;

% Read and process each frame
while hasFrame(videoReader)
    frame = readFrame(videoReader);
    frame = double(rgb2gray(frame)); % Convert frame to double and to grayscale
    
    % Subtract the background image from the frame
    processedFrame = frame - backgroundImage;
    
    % Accumulate the processed frames
    accumulatedImage = accumulatedImage + processedFrame;
    
    % Remap frame data between 0 and 1 and convert to uint8
    remappedFrame = mat2gray(processedFrame);
    remappedFrame = im2uint8(remappedFrame);
    
    % Ensure the frame is 2D before writing
    remappedFrame = squeeze(remappedFrame); % Squeeze to remove singleton dimensions
    
    % Write the frame to the new video
    writeVideo(videoWriter, remappedFrame);
    
    frameCount = frameCount + 1;
end

% Average the accumulated frames
averagedImage = accumulatedImage / frameCount;

% Normalize the averaged image to fit the grayscale range
normalizedImage = mat2gray(averagedImage);
normalizedImage = im2uint8(normalizedImage);

% Display and save the histogram of the averaged image
figure;
histogram(averagedImage(:), 256); % Display histogram
title('Histogram of Averaged Image Differences');

% Display the normalized image
figure;
imshow(normalizedImage);
title('Normalized Averaged Image');

% Close the video writer
close(videoWriter);

% Optional: Save the normalized averaged image if needed
imwrite(normalizedImage, 'normalized_averaged_image.png');

%% V2

% Define the paths for the input files and output
backgroundImagePath = 'ShadowgraphBackground.png';
videoPath = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_43_C001H001S0001\2024_Schlieren_43_C001H001S0001.mp4';
outputVideoPath = 'output_video.avi';

% Read the background image
backgroundImage = imread(backgroundImagePath);
backgroundImage = double(rgb2gray(backgroundImage)); % Convert to double and to grayscale for processing

% Create a video reader and writer object
videoReader = VideoReader(videoPath);
videoWriter = VideoWriter(outputVideoPath, 'Grayscale AVI');
open(videoWriter);

% Initialize a variable to accumulate frames
accumulatedImage = zeros(videoReader.Height, videoReader.Width);
frameCount = 0;

% Read and process each frame
while hasFrame(videoReader)
    frame = readFrame(videoReader);
    frame = double(rgb2gray(frame)); % Convert frame to double and to grayscale
    
    % Adaptive background subtraction
    processedFrame = frame - backgroundImage;

    % Apply a Gaussian filter to smooth out the differences
    processedFrame = imgaussfilt(processedFrame, 2); % Experiment with the sigma value
    
    % Accumulate the processed frames
    accumulatedImage = accumulatedImage + processedFrame;
    
    % Remap frame data between 0 and 1 and convert to uint8
    remappedFrame = mat2gray(processedFrame);
    remappedFrame = im2uint8(remappedFrame);
    
    % Ensure the frame is 2D before writing
    remappedFrame = squeeze(remappedFrame); % Squeeze to remove singleton dimensions
    
    % Write the frame to the new video
    writeVideo(videoWriter, remappedFrame);
    
    frameCount = frameCount + 1;
end

% Average the accumulated frames
averagedImage = accumulatedImage / frameCount;

% Normalize the averaged image to fit the grayscale range
normalizedImage = mat2gray(averagedImage);
normalizedImage = im2uint8(normalizedImage);

% Enhance contrast
normalizedImage = imadjust(normalizedImage);

% Display and save the histogram of the averaged image
figure;
histogram(averagedImage(:), 256); % Display histogram
title('Histogram of Averaged Image Differences');

% Display the normalized image
figure;
imshow(normalizedImage);
title('Normalized Averaged Image');

% Close the video writer
close(videoWriter);

% Optional: Save the normalized averaged image if needed
imwrite(normalizedImage, 'normalized_averaged_image.png');













