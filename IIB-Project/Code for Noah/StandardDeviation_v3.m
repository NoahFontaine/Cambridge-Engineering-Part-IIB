clc
clear all
%% Standard deviation v3
%% 

% This part of the code takes the most time as it has to iterate through
% each frame. Image manipulation (rotating, trimming, and plotting etc) is
% done in the next section. Once you have the data from the loop just use
% the next part to get the image how  you want it :)

% Read the video file
v = VideoReader('F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\Rolls Lip\Rolls_1_C001H001S0040\Rolls_1_C001H001S0040.mp4');

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

% Calculate the mean and standard deviation
meanFrames = sumFrames / frameCount;
stdDeviations = sqrt((sumSquares / frameCount) - meanFrames.^2);

% Normalize the standard deviation values to [0, 1] for visualization
normalizedStdDev = mat2gray(stdDeviations);

% Create an image where high values (dark) indicate high std deviation
% This is the direct visualization, not inverted
stdDevImage = 1 - normalizedStdDev;

%% Image manipulation

% Rotate the image by a specified angle (e.g., 45 degrees)
rotationAngle = -50; % Adjust this angle as needed
rotatedImage = imrotate(stdDevImage, rotationAngle);

% Crop the image to a specified rectangle (e.g., [xmin, ymin, width, height])
% cropRect takes the rotated image and then crops it down to whatever you
% want
% Default res: 1443x1443

cropRect = [400, 480, 787, 500]; % Adjust these values as needed
croppedImage = imcrop(rotatedImage, cropRect);

%% Plotting the final image

% For use in papers save the image in a vectorised form, such as .PDF. This
% essentially allows the resolution to scale with zooming in etc. A simple
% .png may end up looking blurry.

% Display and save the image with correct colormap interpretation
figure;
%imshow(stdDevImage);
%imshow(rotatedImage)
imshow(croppedImage)
colormap((gray)); % Flips the gray scale to make dark high, light low
cb = colorbar; % Adds a color bar to indicate the scale of standard deviation
cb.Ticks = []; % Remove tick marks from the color bar
caxis([0 1]); % Sets the limits of the color scale to match the normalized data
set( cb, 'YDir', 'reverse' );


% Save the image as a .pdf vectorized image
print(gcf, 'Test1.pdf', '-dpdf', '-bestfit');






