clear all
clc
%% Script to get the standard deviation of pixel intensity from Shadowgraph/Schlieren MP4 (v2)

% Load the video file
video = VideoReader('F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\Rolls Lip\Rolls_1_C001H001S0037\Rolls_1_C001H001S0037.mp4');

% Initialize matrices to store the sum and sum of squares of pixel values
sumPixels = zeros(video.Height, video.Width);
sumSquares = zeros(video.Height, video.Width);
numFrames = 0;

% Process each frame individually
while hasFrame(video)
    frame = readFrame(video);
    % Convert frame to grayscale
    grayFrame = double(rgb2gray(frame));

    % Update the sums and sum of squares
    sumPixels = sumPixels + grayFrame;
    sumSquares = sumSquares + grayFrame.^2;
    numFrames = numFrames + 1;
end

% Calculate the mean and standard deviation for each pixel position
meanPixels = sumPixels / numFrames;
stdPixels = sqrt((sumSquares / numFrames) - meanPixels.^2);

% Normalize the standard deviation values to the range [0, 1]
stdPixelsNormalized = (stdPixels - min(stdPixels(:))) / (max(stdPixels(:)) - min(stdPixels(:)));

% Invert the image so that high standard deviation values appear dark
invertedImage = 1 - stdPixelsNormalized;

% Display the inverted image
imshow(invertedImage, []);
title('Inverted Standard Deviation of Pixel Intensities');

% Save the image as a PNG
imwrite(invertedImage, 'STD_Rolls_31-42-42.png');
