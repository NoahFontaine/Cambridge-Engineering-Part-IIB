clc
clear all
%% Code for subtracting the background image from Shadowgraph & Schlieren videos

% Define filenames
videoFile = 'F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_29_C001H001S0001\2024_Schlieren_29_C001H001S0001.mp4';
backgroundImageFile = 'ShadowgraphBackground.png';
outputVideoFile = 'output_video.mp4';

% Read the background image
backgroundImage = imread(backgroundImageFile);

% Create video reader object
videoReader = VideoReader(videoFile);

% Get video properties
numFrames = videoReader.NumberOfFrames;
frameRate = videoReader.FrameRate;

% Create video writer object
videoWriter = VideoWriter(outputVideoFile, 'MPEG-4');
open(videoWriter);

% Loop through each frame of the input video
for frameIdx = 1:numFrames
    % Read the next frame
    frame = read(videoReader, frameIdx);
    
    % Perform background subtraction
    subtractedFrame = imsubtract(frame, backgroundImage);
    
    % Write the subtracted frame to the output video
    writeVideo(videoWriter, subtractedFrame);
end

% Close the video writer object
close(videoWriter);
