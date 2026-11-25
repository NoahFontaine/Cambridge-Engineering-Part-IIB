clear all
clc
%% Script to time-average MP4 Schlieren/Shadowgraph files

% Read the input video file
videoFile = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\Rolls Lip\Rolls_1_C001H001S0044\Rolls_1_C001H001S0044.mp4';
videoObj = VideoReader(videoFile);

% Get video properties
numFrames = videoObj.NumberOfFrames;
frameHeight = videoObj.Height;
frameWidth = videoObj.Width;

% Initialize variables to store sum of pixel intensities
sumIntensities = zeros(frameHeight, frameWidth, 3);

% Iterate through frames and sum up pixel intensities
for i = 1:numFrames
    % Read current frame
    frame = read(videoObj, i);
    
    % Convert frame to double precision for accurate intensity calculation
    frame = double(frame);
    
    % Sum up pixel intensities
    sumIntensities = sumIntensities + frame;
end

% Calculate average pixel intensities
averageIntensities = sumIntensities / numFrames;

% Convert back to uint8
averageIntensities = uint8(averageIntensities);

% Save the averaged frame as a PNG image
outputFileName = 'Rolls_24-42-42.png';
imwrite(averageIntensities, outputFileName);

disp('Time-averaging completed. Averaged image saved as average_image.png');