clc
clear all

% Set rotation angle and cropping rectangle
rotationAngle = -50; % Adjust this angle as needed
%cropRect = [488, 410, 420, 250]; % Value for 2024 Campaign (250/1000fps videos)
cropRect = [150, 150, 250, 180]; % Value needed for the zoomed unsteady settings

% Specify the input folder and the output folder
inputFolder = 'F:\PhD\Thesis data\Data master\Shadowgraph & Schlieren\Instantaneous snapshots\Unsteadiness\Raw2';
outputFolder = 'F:\PhD\Thesis data\Data master\Shadowgraph & Schlieren\Instantaneous snapshots\Unsteadiness';

% List all image files in the input folder
imageFiles = dir(fullfile(inputFolder, '*.jpg')); % Change '*.jpg' to the appropriate file extension if necessary

% Loop through each image file
for k = 1:length(imageFiles)
    % Construct the full file name
    baseFileName = imageFiles(k).name;
    fullFileName = fullfile(inputFolder, baseFileName);
    
    % Display file being processed
    fprintf('Now reading %s\n', fullFileName);
    
    % Read the image
    image = imread(fullFileName);
    
    % Rotate and crop the image
    rotatedImage = imrotate(image, rotationAngle);
    croppedImage = imcrop(rotatedImage, cropRect);
    
    % Save the processed image
    outputFileName = fullfile(outputFolder, ['cropped_' baseFileName]);
    imwrite(croppedImage, outputFileName);
    
    fprintf('Processed and saved %s\n', outputFileName);
end
