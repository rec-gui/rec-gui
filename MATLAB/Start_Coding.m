function Start_Coding

% this script establish two UDP connections (one for general communicaiton and
% second one for receving the result of evaluation of eye tracking: voilation of version and vergence) 
% without out eye tracking system, please remove lines for eye tracking 

packetSize = 1024;
bufferLength = packetSize;

%%% establishing connection to the GUI by sending a preserved word '-1 8256'
%%% and receiving a preserved word '-1 8257'
Myudp = udp(GUI_MACHINE_IPADDRESS, 5001, 'LocalPort', 5002);  % establishing main connection for communication with the GUI
if ~isempty(Myudp)
    set(Myudp,'ReadAsyncMode','continuous');
    set(Myudp,'InputBufferSize',bufferLength*2);
    set(Myudp,'OutputBufferSize',bufferLength*2);
    set(Myudp,'DatagramTerminateMode','on');
    fopen(Myudp);
    readasync(Myudp);  % start async. reading to control flow and check eye pos
    
    SendUDPGui(Myudp, '-1 8256');   %% send probe packet to establish initial UDP connection
    StateTime = GetSecs;
    
    tempEnd = 1; IsESC = 0;
    while tempEnd && ~IsESC
        CurrentTime = GetSecs - StateTime;
        if CurrentTime >=2
            if ~isempty(Myudp)
                fclose(Myudp);
            end
            sca;
            error('********** Please Start GUI first ************');
            tempEnd = 0;
        end
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
                        case '-1'  %% check whether it receives a preserved word '-1 8257'
                            if CMD_Word == 8257
                                SendUDPGui(Myudp,'-1 8257');
                                SendUDPGui(Myudp,['7 ' num2str(VP.windowWidthPix)]);
                                SendUDPGui(Myudp,['8 ' num2str(VP.windowHeightPix)]);
                            end                    
                    end
                end
                tempEnd = 0;
            end
            disp('Received initializing parameters');
        end
    end
end

%%% connection is established 

%%% establish secend connection for eye tracking
Myudp_eye = udp(GUI_MACHINE_IPADDRESS, 5003, 'LocalPort', 5004);
if ~isempty(Myudp_eye)
    set(Myudp_eye,'ReadAsyncMode','continuous');
    set(Myudp_eye,'InputBufferSize',bufferLength*2);
    set(Myudp_eye,'OutputBufferSize',bufferLength);
    set(Myudp_eye,'DatagramTerminateMode','on');
    readasync(Myudp_eye);  % start async for check violation of eye movement
end
%%% add initialize display routine here %%%%%%%%


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

OnGoing = 1;
IsESC = 0;

while OnGoing && ~IsESC
    
    % checking user abortation by ESC key
    [keydown, ~, keyCode] = KbCheck;
    if keydown
    	keyCode = find(keyCode,1);
    	if keyCode==10
    		IsESC = 1;
    	end
    end
    % checking user abortation by ESC key
    
    
    % check result of evalution of eye movements
    if Myudp_eye.BytesAvailable >= packetSize  
        UDP_Pack = char(fread(Myudp_eye,packetSize))';
        flushinput(Myudp_eye);
        p=find(UDP_Pack=='q');
        if ~isempty(p)
            UDP_Pack(p)='';
        end
        tempIndex = strfind(UDP_Pack,'/');
        if ~isempty(tempIndex)
            for i=1:length(tempIndex)
                if i>1
                    tempStr = UDP_Pack(tempIndex(i-1)+1:tempIndex(i)-1);
                else
                    tempStr = UDP_Pack(1:tempIndex(i)-1);
                end
                
                [CMD, tempWord] = strtok(tempStr, ' ');
                CMD_Word = strrep(tempWord,' ','');
                switch CMD
                    case '-14'  % evalution result of version error in Left eye
			% the GUI returns this values whenever it receives '51'
                        % 1 = no violation
                        % 0 = violation
                        % add code %
                    case '-15'  % evalution result of version error in Left eye
			% the GUI returns this values whenever it receives '51'
                        % 1 = no violation
                        % 0 = violation
                        % add code %
                    case '-16'  % evalution result of vergence error in Left eye
			% the GUI returns this values whenever it receives '51'
                        % 1 = no violation
                        % 0 = violation
                        % add code %
                end
            end
        end
    end
    % check result of evalution of eye movements
    
    if Myudp.BytesAvailable >= packetSize  % check incoming parameters from GUI
        UDP_Pack = char(fread(Myudp,packetSize))';
        flushinput(Myudp);
        p=find(UDP_Pack=='q');
        if ~isempty(p)
            UDP_Pack(p)='';
        end
        tempIndex = strfind(UDP_Pack,'/');
        if ~isempty(tempIndex)
            for i=1:length(tempIndex)
                if i>1
                    rawStr = UDP_Pack(tempIndex(i-1)+1:tempIndex(i)-1);
                else
                    rawStr = UDP_Pack(1:tempIndex(i)-1);
                end
                % checking button status in task control panel in the GUI
                switch rawStr
                    case '-2 100'  % start button pressed in GUI
                        StateID = 100;
                        FirstStep = 1;
                    case '-2 101'  % Stop button pressed in GUI
                        OnGoing = 0;
                    case '-2 103'  % Exit button pressed in GUI
                        OnGoing = 0;
                    case '-2 102'  % Pause button pressed in GUI
                        StateID = 110;
                        FirstStep = 1;
                end
                % checking button status in task control panel in the GUI
                
                [CMD, tempWord] = strtok(rawStr, ' ');
                CMD_Word = strrep(tempWord,' ','');
                switch CMD
                    %%% add your code here                         
                end
            end
        end
    end
    %%%%%% separated thread for communicating GUI

    xPosFixation = 0; yPosFixation = 0; zPosFixation = 0;  %% fixation point location
    tempStr = ['50 1 ' num2str(xPosFixation) ' ' num2str(yPosFixation) ' ' num2str(zPosFixation) ' ' num2str(Version) ' ' LColor ' ' RColor];
    SendUDPGui(Myudp,tempStr);  % send 'setup fixation window around fixation point' signal
    % before asking evaluation '51' or '53'. Checking window should be setup before as above lines		
    SendUDPGui(Myudp,'51'); %% start checking fixation window 
    SendUDPGui(Myudp,'53'); %% start vergence window

    
    %%%%%% Main control routines for task
    switch StateID
        case 100 % start button pressed in GUI
            if FirstStep==1                
                FirstStep = 0;
            end
        case 101 % stop button pressed in GUI
            if FirstStep==1
                FirstStep = 0;
            end
    end
    %%%%%% Main control routines for task
end

end


function SendUDPGui(Dest, tempStr)
packetSize = 1024;
SendStr(1:packetSize) = 'q';
SendStr(1:length(tempStr)+1) = [tempStr '/'];
fwrite(Dest, SendStr);    %% send UDP packet
end
