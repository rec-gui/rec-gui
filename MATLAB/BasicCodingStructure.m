function TemplateCode

packetSize = 1024;
bufferLength = packetSize;

Myudp = udp(GUI_MACHINE_IPADDRESS, 5001, 'LocalPort', 5002);
if ~isempty(Myudp)
    set(Myudp,'ReadAsyncMode','continuous');  % UDP connection in asynchronous mode
    set(Myudp,'InputBufferSize',bufferLength*2);
    set(Myudp,'OutputBufferSize',bufferLength*2);
    set(Myudp,'DatagramTerminateMode','on');
    SendUDPGui(Myudp, '-1 8256');   %% send probe packet to establish initial UDP connection
    readasync(Myudp);  % start async. reading to control flow and check eye pos
    tempEnd = 1; IsESC = 0;
    while tempEnd && ~IsESC  % wait until GUI is ready
        [keydown, ~, keyCode] = KbCheck;  % handling user interruption
        if keydown
            keyCode = find(keyCode,1);
            if keyCode==10
                IsESC = 1;
            end
        end
        
        if Myudp.BytesAvailable >= packetSize  % if UDP packet is ready to read
            tempUDP = fread(Myudp,packetSize); % read UDP packet
            for i=1:length(tempUDP)
                UDP_Pack(i) = char(tempUDP(i));
            end
            tempIndex = strfind(UDP_Pack,'/'); % check of packet
            if ~isempty(tempIndex)
                for i=1:length(tempIndex)
                    if i>1 % if there are multiple packets
                        tempStr = UDP_Pack(tempIndex(i-1)+1:tempIndex(i)-1);
                    else
                        tempStr = UDP_Pack(1:tempIndex(i)-1);
                    end
                    p=find(tempStr=='q');  % remove filler 'q'
                    if ~isempty(p)
                        tempStr(p)='';
                    end
                    [CMD, tempWord] = strtok(tempStr, ' ');  % separate identifier and command word
                    CMD_Word = strrep(tempWord,' ','');
                    
                    switch CMD
                        case '-1'
                            if CMD_Word == 8257
                                SendUDPGui(Myudp,'-1 8257');
                                SendUDPGui(Myudp,['7 ' num2str(VP.windowWidthPix)]);
                                SendUDPGui(Myudp,['8 ' num2str(VP.windowHeightPix)]);
                            end
                        case '-4'
                            VP.screenDistance = CMD_Word;
                        case '-6'
                            VP.IOD = CMD_Word;
                        case '-5' %mm
                            VP.screenWidthMm = CMD_Word;
                        case '-3'
                            VP.screenHeightMm = CMD_Word;
                    end
                end
                tempEnd = 0;
            end
            disp('Received initializing parameters');
        end
    end
end

%%% establish second UDP connection to check violation of eye movement
Myudp_eye = udp(GUI_MACHINE_IPADDRESS, 5003, 'LocalPort', 5004);
if ~isempty(Myudp_eye)
    set(Myudp_eye,'ReadAsyncMode','continuous');
    set(Myudp_eye,'InputBufferSize',bufferLength*2);
    set(Myudp_eye,'OutputBufferSize',bufferLength);
    set(Myudp_eye,'DatagramTerminateMode','on');
    readasync(Myudp_eye);  % start async for check violation of eye movement
end

while OnGoing
    
    %   [keydown, ~, keyCode] = KbCheck;
    %   if keydown
    %       keyCode = find(keyCode,1);
    %       if keyCode==10
    %           IsESC = 1;
    %       end
    %   end
    
    %%%%%% separated thread for communicating GUI
    if Myudp_eye.BytesAvailable >= packetSize  % check violation of eye movements
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
                    case '-14'  % evaluation result of version error in Left eye
                        % 1 = no violation
                        % 0 = violation
                        % add code %
                    case '-15'  % evaluation result of version error in Left eye
                        % 1 = no violation
                        % 0 = violation
                        % add code %
                    case '-16'  % evaluation result of vergence error in Left eye
                        % 1 = no violation
                        % 0 = violation
                        % add code %
                end
            end
        end
    end
    
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
                
                [CMD, tempWord] = strtok(rawStr, ' ');
                CMD_Word = strrep(tempWord,' ','');
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
                
                switch CMD
                    %%% add your code here
                end
            end
        end
    end
    %%%%%% separated thread for communicating GUI
    
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

