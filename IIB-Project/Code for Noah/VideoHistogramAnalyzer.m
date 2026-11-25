% Load the video file
video = VideoReader('F:\Dropbox Data\Data\Data\Schlieren & Shadowgraph\2024  Campaign\2024_Schlieren_17_C001H001S0001\2024_Schlieren_17_C001H001S0001.mp4');

% Initialize histogram storage for the average histogram
histogramBins = 256;
averageHistogram = zeros(histogramBins, 1);

% Initialize a counter for the number of frames
frameCount = 0;

% Process each frame individually
while hasFrame(video)
    frame = readFrame(video);
    grayFrame = rgb2gray(frame);  % Convert to grayscale
    [counts, ~] = imhist(grayFrame, histogramBins);  % Calculate histogram
    
    % Update the average histogram
    averageHistogram = averageHistogram + counts;
    frameCount = frameCount + 1;
end

% Normalize the average histogram by the number of frames
averageHistogram = averageHistogram / frameCount;

% Plot the average histogram
figure;
bar((0:histogramBins-1), averageHistogram, 'BarWidth', 1);
title('Average Histogram of Video Pixel Intensities');
xlabel('Pixel Intensity');
ylabel('Average Count');

% Save the plot as a PNG image
saveas(gcf, 'average_histogram.png');

% Optionally, save histogram data to a MAT file for later use
save('average_histogram_data.mat', 'averageHistogram');
