%%
%load logs

mon_f='../logs/mon_20180227-182216.csv';
wl_f='../logs/wl_20180227-182236.csv';

fid = fopen(mon_f);
mon_data = textscan(fid, '%s%d%d%d%d%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f%f', ...
                    'delimiter', ',','emptyvalue', NaN);
[~] = fclose(fid);

fid = fopen(wl_f);
wl_data = textscan(fid, '%s%s%f%d', ...
                    'delimiter', ',','emptyvalue', NaN);
[~] = fclose(fid);

t_mon=datenum(mon_data{1}(:),'yyyy-mm-ddTHH:MM:SS.FFF')*24*3600;
t_wl=datenum(wl_data{1}(:),'yyyy-mm-ddTHH:MM:SS.FFF')*24*3600;

t_wl=t_wl-wl_data{3};

t0=min([t_mon;t_wl]);

t_mon=t_mon-t0;
t_wl=t_wl-t0;

free = mon_data{2};
busy = mon_data{3};
na = mon_data{4};

time_wl=wl_data{3};

vms=free+busy+na;

wait_time=wl_data{3};
queue_length=wl_data{4};

t_rs=min(t_wl):max(t_wl);

queue_length_rs = resample(timeseries(queue_length,t_wl),t_rs);

[jobs_per_minute,edges]=hist(t_wl,0:60:max(t_wl));



figure(1);clf;hold on;
subplot(2,1,1);hold on;
yyaxis left
plot(t_wl,wait_time,'bx')
ylabel('Job wait time [s]')
yyaxis right
plot(edges,jobs_per_minute,'r-')
ylabel('Jobs started per minute')
xlabel('Time [s]')
xlim([0,6000])

subplot(2,1,2);hold on;
yyaxis right
%plot(t_wl,queue_length,'xr');
plot(t_rs,queue_length_rs.Data,'r');
ylabel('Queue length')
yyaxis left
plot(t_mon,busy,'b');
plot(t_mon,vms,'b--');
ylabel('VMs')
xlabel('Time [s]')
legend('Working VMs', 'Running VMs')
xlim([0,6000])

