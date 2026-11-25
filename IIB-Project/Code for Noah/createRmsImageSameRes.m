function createRmsImageSameRes(videoPath, outputPath)
    % Create a VideoReader object to read MP4 video
    vidObj = VideoReader(videoPath);

    % Initialize an array to store RMS values
    numFrames = floor(vidObj.Duration * vidObj.FrameRate);
    videoWidth = vidObj.Width;
    
    % Prepare a matrix to store RMS values per frame
    rmsMatrix = zeros(vidObj.Height, videoWidth);

    % Read and process each frame
    frameIndex = 1;
    while hasFrame(vidObj)
        frame = readFrame(vidObj);
        grayFrame = rgb2gray(frame);  % Convert to grayscale if it's a color video

        % Compute RMS of the pixel intensities
        frameRMS = sqrt(mean(grayFrame.^2, 'all'));

        % Assign the RMS value to the entire corresponding column
        rmsMatrix(:, frameIndex) = frameRMS;

        % Increment the frame index, wrap around if it exceeds video width
        frameIndex = mod(frameIndex, videoWidth) + 1;
    end

    % Normalize RMS values to 0-255 scale
    rmsMatrix = uint8(255 * (rmsMatrix - min(rmsMatrix(:))) / (max(rmsMatrix(:)) - min(rmsMatrix(:))));

    % Write the image to a PNG file
    imwrite(rmsMatrix, outputPath);
end
