function start_coding_closedloop(connectServer)

% a simple closed-looping coding with the REC-GUI
% in GUI, use start_coding_closedloop.conf to configure GUI to make it work with this
% script.
% please enbable 'Feedback' option in the monitoring panel
% whenever mouse clicked (left button) on the monitoring panel,
% mouse location is reported to the MATLAB and this script returns reported
% location of mouse back to the GUI and it will show up in the receiving
% panel
% to abolt this script "Cntl+c" and type "sca" + enter

% connectServer : connect GUI or not

% before start this script, make it sure that GUI has correct screen size
% , distance and inter occular distance that are required to calculate
% conversion factors.


% runtime error as below, pleace close MATLAB and close terminal (if MATLAB
% started in terminal) and restart MATLAB
% Error using icinterface/fopen (line 83)
% Unsuccessful open: Address already in use (Bind failed)

close all;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% initial network parameters
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
GUI_IP = '100.1.1.3'; %% IP address of the GUI machine
ServerPort = 5001;
LocalPort = 5002;
packetSize = 1024;  % UDP packet size
bufferLength = packetSize*2;  % prepare network buffer size

if connectServer
    Myudp = udp(GUI_IP, ServerPort, 'LocalPort', LocalPort);
    if ~isempty(Myudp)
        set(Myudp,'ReadAsyncMode','continuous');
        set(Myudp,'InputBufferSize',bufferLength);
        set(Myudp,'OutputBufferSize',bufferLength);
        set(Myudp,'DatagramTerminateMode','on');
        try
            fopen(Myudp);
            FinishUP = onCleanup(@() CleanUDP(Myudp));
            readasync(Myudp);  % start async. reading to control flow and check eye pos            
        catch
            disp('Fatal erro in establishing UDP connection');
            disp('MATLAB needs to restart');
            disp('Press any key....');
            pause;
            exit;
        end
    end           
end


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% establish UDP channel to the GUI
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if connectServer
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % here two UDP channels established 
    % Myudp - for sending/recieving events and control info
    % Myudp_eye - for sending/recieving eye movement related events
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    if ~isempty(Myudp)        
        SendUDPGui(Myudp, '-1 8256');   %% send probe packet to establish initial UDP connection
        tempEnd = 1; IsESC = 0;
        while tempEnd && ~IsESC
            [keydown, ~, keyCode] = KbCheck;
            if keydown
                keyCode = find(keyCode,1);
                if keyCode==10
                    IsESC = 1;
                end
            end
            
            if Myudp.BytesAvailable >= packetSize
                tempUDP = fread(Myudp,packetSize);
                for i=1:length(tempUDP)
                    UDP_Pack(i) = char(tempUDP(i));
                end
                tempIndex = strfind(UDP_Pack,'/');
                if ~isempty(tempIndex)
                    for i=1:length(tempIndex)
                        if i>1
                            tempStr = UDP_Pack(tempIndex(i-1)+1:tempIndex(i)-1);
                        else
                            tempStr = UDP_Pack(1:tempIndex(i)-1);
                        end
                        p=find(tempStr=='q');
                        if ~isempty(p)
                            tempStr(p)='';
                        end
                        [CMD, tempWord] = strtok(tempStr, ' ');
                        CMD_Word = str2double(strrep(tempWord,' ','')); 
                        switch CMD
                            case '-1'
                                if CMD_Word == 81257
                                    SendUDPGui(Myudp,'-1 8257');
                                    SendUDPGui(Myudp,['7 ' num2str(VP.screenWidth)]);
                                    SendUDPGui(Myudp,['8 ' num2str(VP.screenHeight)]);
                                    disp('Success in connection GUI run first');
                                elseif CMD_Word == 8256
                                    SendUDPGui(Myudp,'-1 8257');
                                    SendUDPGui(Myudp,['7 ' num2str(VP.screenWidth)]);
                                    SendUDPGui(Myudp,['8 ' num2str(VP.screenHeight)]);
                                    disp('Success in connection Matlab run first');
                                end
                        end
                    end
                    tempEnd = 0;
                end
                disp('Received initializing parameters');
            end
        end
    end
end

MPos_X = 0;
MPos_Y = 0;
MPos_XOld = MPos_X;
MPos_YOld = MPos_X;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% set start condition
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

StateID = 100; % go to inter trial interval to start experiment
FirstStep = 1; 

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% MAIN WHILE-LOOP
% Control + C - user abort
% it stops when it recieves 'Stop' or 'Exit' signals from GUI
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
OnGoing = 1; TotalSec = 0;
FeedBackNum = 0;  % total trial number presented
while OnGoing
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % continouse checking UDP packet for update parameters 
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    if connectServer        
        % check UDP buffer has recieved packet or not        
       if Myudp.BytesAvailable >= packetSize
           
           tempUDP = fread(Myudp,packetSize);
           flushinput(Myudp);
           for i=1:length(tempUDP)
               UDP_Pack(i) = char(tempUDP(i));
           end
           tempIndex = strfind(UDP_Pack,'/');
           if ~isempty(tempIndex)
               for i=1:length(tempIndex)
                   if i>1
                       tempStr = UDP_Pack(tempIndex(i-1)+1:tempIndex(i)-1);
                   else
                       tempStr = UDP_Pack(1:tempIndex(i)-1);
                   end
                   
                   p=find(tempStr=='q');
                   if ~isempty(p)
                       tempStr(p)='';
                   end
                   
                   [CMD, tempWord] = strtok(tempStr, ' ');
                   CMD_Word = strrep(tempWord,' ','');
                   tempI = str2double(CMD);
                   switch tempI
                       case -2
                           tempCMD = str2double(CMD_Word);
                           switch tempCMD
                               case 101   % 'stop' signal from the GUI
                                   OnGoing = 0;
                               case 103   % 'exit' signal from the GUI
                                   OnGoing = 0;                               
                           end                       
                       case -11
                           MPos_X = str2double(CMD_Word); % update horizontal position of fixation point
                           if MPos_X ~= MPos_XOld % if it is new position, trial will be restarted                               
                               MPos_XOld = MPos_X;
                               StateID = 110;
                               FirstStep=1;
                           end
                       case -12
                           MPos_Y = -1* str2double(CMD_Word); % update vertical position of fixation point
                           if MPos_Y ~= MPos_YOld % if it is new position, trial will be restarted
                               MPos_YOld = MPos_Y;
                               StateID = 110;
                               FirstStep=1;
                           end                       
                   end
               end
           end
       end   
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % main control 
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    switch StateID
        case 100 % idling 
            if FirstStep==1
                StartTime = tic;                
                FirstStep = 0;
            else
                StateTime = toc(StartTime);
                if StateTime>1
                    TotalSec = TotalSec+1;
                    %disp(['Time passing (sec): ' num2str(TotalSec)]);
                    StartTime = tic;
                end                
            end
        case 110 %% it receive mouse position information
            FeedBackNum = FeedBackNum +1;
            disp(['Mouse Position Received: ' num2str(FeedBackNum)]);
            disp(['X: ' num2str(MPos_X,5) ' Y: ' num2str(MPos_Y,5)]);
            
            % return back to the GUI
            tempStr = ['1 110 ' num2str(MPos_X,3)]; 
            SendUDPGui(Myudp, tempStr);  
            tempStr = ['1 120 ' num2str(MPos_Y,3)]; 
            SendUDPGui(Myudp, tempStr);  
            
            StateID = 100;
            FirstStep = 1;
    end
end

disp('Finished');

% clean up UDP connection 
if connectServer
    if ~isempty(Myudp)
        fclose(Myudp);
    end    
end
    
Priority(0);

end

function CleanUDP(temp1)
    if ~isempty(temp1)
        fclose(temp1);
    end
end

function SendUDPGui(Dest, tempStr)
    packetSize = 1024;
    SendStr(1:packetSize) = 'q'; % add fillers to match packet size
    SendStr(1:length(tempStr)+1) = [tempStr '/']; % add terminating charactor
    fwrite(Dest, SendStr);    % send UDP packet
end

