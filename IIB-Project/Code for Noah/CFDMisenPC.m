%% Plotting CFD Misen
clc
clear all

data= table2array(readtable("F:\PhD\Thesis data\Powerpoint figures\Designing the rig\CFDMisen\M015.csv"));

xD = data(:,1);
Misen = data(:,2)

plot(xD,Misen,'o')

plot(xD,Misen,'ko')
box on
pbaspect([1 1 1])
ylim([0.3 1.4])
xlim([-0.01 0.42])
set(gca,'linewidth',1.3)
set(gca,'TickLabelInterpreter','latex')
set(gca,'fontsize', 26) 
ylabel('Isentropic Mach number','interpreter','latex')
xlabel('x/D','interpreter','latex')

%legend({'0.15'}, 'Interpreter', 'latex', 'FontSize', 10);