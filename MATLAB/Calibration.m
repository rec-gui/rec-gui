function Calibration(connectServer)
% Eye Calibration procedure 
% in GUI, use Calibration.conf to configure GUI to make it work with this
% script.
% to abort this script "Cntl+c" and type "sca" + enter

% connectServer : connect GUI or not

% before start this script, make it sure that GUI has correct screen size
% , distance and inter occular distance that are required to calculate
% conversion factors.

% runtime error as below, pleace close MATLAB and close terminal (if MATLAB
% started in terminal) and restart MATLAB
%%%%%
% Error using icinterface/fopen (line 83)
% Unsuccessful open: Address already in use (Bind failed)

close all;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% initial network parameters
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
GUI_IP = '100.1.1.3'; %% IP address of the GUI machine
ServerPort = 5001;
LocalPort = 5002;
ServerPort_eye = 5003;
LocalPort_eye = 5004;
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
            readasync(Myudp);  % start async. reading to control flow and check eye pos
        catch
            disp('Fatal erro in establishing UDP connection');
            exit;
        end
        
        Myudp_eye = udp(GUI_IP, ServerPort_eye, 'LocalPort', LocalPort_eye);
        if ~isempty(Myudp_eye)
            set(Myudp_eye,'ReadAsyncMode','continuous');
            set(Myudp_eye,'InputBufferSize',bufferLength*2);
            set(Myudp_eye,'OutputBufferSize',bufferLength);
            set(Myudp_eye,'DatagramTerminateMode','on');
            try
                fopen(Myudp_eye);
                readasync(Myudp_eye);  % start async. reading to control flow and check eye pos    
            catch
                disp('Fatal error in establishing UDP connection');
                exit;
            end                        
        end
        FinishUP = onCleanup(@() CleanUDP(Myudp, Myudp_eye));
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% VP is a structure that contains all parameters of drawind window of
% Psychtoolbox. The rest of parameters will be defined later
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
skipSync = 1;  % make Pshchtoolbox skip Sync test. 
VP.stereoMode = 1;  % stereomode supported in Psychtoolbox 
% please check StereoDemo in Psychtoolbox
% 0 == Mono display - No stereo at all.
% 1 == Flip frame stereo (temporally interleaved) - You�ll need shutter
% glasses that are supported by the operating system, e.g., the
% CrystalEyes-Shutterglasses.
% 2 == Top/bottom image stereo with lefteye=top also for use with special
% CrystalEyes-hardware.
% 3 == Same, but with lefteye=bottom.
% 4 == Free fusion (lefteye=left, righteye=right): This - together wit a
% screenid of zero - is what you�ll want to use on MS-Windows dual-display
% setups for stereo output.
% 5 == Cross fusion (lefteye=right �)
% 6-9 == Different modes of anaglyph stereo for color filter glasses:
% 6 == Red-Green
% 7 == Green-Red
% 8 == Red-Blue
% 9 == Blue-Red
% 10 == Dual-Window stereo: Open two onscreen windows, first one will
% display left-eye view, 2nd one right-eye view. Direct all drawing and
% flip commands to the first window, PTB will take care of the rest. This
% mode is mostly useful for dual-display stereo on MacOS/X. It only works
% on reasonably modern graphics hardware, will abort with an error on
% unsupported hardware.
% 11 == Like mode 1 (frame-sequential) but using Screen�s built-in method,
% instead of the native method supported by your graphics card.
VP.multiSample = 8;   % number for multi-sampling to make edge of stimulus smooth

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% load default parameters for stimulus and experimental control
% if needed, it can be changed in runtime
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
StiPF = 'Calibration_Conf.mat';
if exist(StiPF)    
    try
        load(StiPF); % load default stimulus parameters        
        disp([StiPF ' is loaded']);
        % VP is a structure that contains all parameters of drawing screen
        % of Psychtoolbox.
        VP.backGroundColor = StiP.backGroundColor;  % [R G B] [0-255 0-255 0-255]
        VP.fixColor = StiP.dotColor; % [R G B] [0-255 0-255 0-255]
    catch
        disp('fail to load stimulus parameter file');
    end
else
   disp('no defalut stimulus parameter information');
   disp('set all parameters from default');
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Setup our display and get some intial parameters
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if 1 == skipSync %skip Sync to deal with sync issues
    Screen('Preference','SkipSyncTests',1);
end
AssertOpenGL;
InitializeMatlabOpenGL(0);

Screen('Preference', 'Verbosity', 0); % Increase level of verbosity for debug purposes:
Screen('Preference','VisualDebugLevel', 0); % control verbosity and debugging, level:4 for developing, level:0 disable errors

VP.screenID = max(Screen('Screens'));    %Screen for display.
[VP.window,VP.Rect] = PsychImaging('OpenWindow',VP.screenID,[VP.backgroundColor],[],[],[], VP.stereoMode, VP.multiSample);

[VP.windowCenter(1),VP.windowCenter(2)] = RectCenter(VP.Rect); %Window center
VP.windowWidthPix = VP.Rect(3)-VP.Rect(1);
VP.windowHeightPix = VP.Rect(4)-VP.Rect(2);

HideCursor(VP.screenID);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% set priority of main thread
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
priorityLevel=MaxPriority(VP.window); 
Priority(priorityLevel);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Initialization
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


packetSize = 1024;
bufferLength = packetSize*2;
CMD=[]; CMD_Word=[]; updated_CMDs = [];
IsLEyeIn=0; IsREyeIn=0; IsVergenceIn = 0;
IsESC = 0;
Version = 2; Vergence = 1; VergenceOption = 3;
FirstRun = 1;
xPosFixation=0; yPosFixation=0; zPosFixation=0;
oldX = xPosFixation; oldY = yPosFixation; oldZ = zPosFixation;
FinishedT= 0;

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% set priority of main thread
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
priorityLevel=MaxPriority(VP.window); 
Priority(priorityLevel);

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
                                
                            % GUI send actual size of screen and distance                             
                            case '-4'
                                VP.screenDistance = CMD_Word; % mm
                            case '-6'
                                VP.IOD = CMD_Word; % mm
                            case '-5'
                                VP.screenWidthMm = CMD_Word; %mm
                            case '-3'
                                VP.screenHeightMm = CMD_Word; %mm
                        end
                    end
                    tempEnd = 0;
                end
                disp('Received initializing parameters');
            end
        end
    end
end

if VP.stereoMode == 4
    VP.screenWidthPix = 2*VP.windowWidthPix;
else
    VP.screenWidthPix = VP.windowWidthPix;
end
VP.screenHeightPix = VP.windowHeightPix;

glBlendFunc(GL.SRC_ALPHA,GL.ONE_MINUS_SRC_ALPHA); %Alpha blending for antialising
Screen('BlendFunction', VP.CopyBuffer, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

VP.ifi = Screen('GetFlipInterval', VP.window);
VP.frameRate = Screen('FrameRate',VP.window);
if VP.stereoMode
    VP.stereoViews = 1;
else
    VP.stereoViews = 0;
end
% Calculate the width of one eye's view (in deg)
% actual size of screen (mm) is recieved from GUI
VP.screenWidthDeg = 2*atand(0.5*VP.screenWidthMm/VP.screenDistance);
VP.pixelsPerDegree = VP.screenWidthPix/VP.screenWidthDeg % calculate pixels per degree
VP.pixelsPerMm = VP.screenWidthPix/VP.screenWidthMm; %% pixels/Mm
VP.MmPerDegree = VP.screenWidthMm/VP.screenWidthDeg;
VP.degreesPerMm = 1/VP.MmPerDegree;
VP.aspect = VP.screenWidthPix/VP.screenHeightPix;
VP.CopyBuffer = Screen('OpenOffScreenWindow',-1, []); %, [], [], [], VP.multiSample);

if connectServer
    StateID = 110; % wait until Python GUI changes it to 100
    FirstStep = 1;
else
    StateID = 100;
    FirstStep = 1;
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% MAIN WHILE-LOOP
% 'ESC' - user abort
% it stops when it recieves 'Stop' or 'Exit' signals from GUI
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

OnGoing = 1; IsESC = 0;

while ~IsESC && OnGoing    
    
    % check 'ESC' key pressed or not
    % 'ESC' for user abort
    [keydown, ~, keyCode] = KbCheck;
    if keydown
        keyCode = find(keyCode,1);
        if keyCode==10
            IsESC = 1;
        end
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % continouse checking UDP packet for update parameters 
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    if connectServer
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
                        case '-14'
                            IsLEyeIn = str2double(CMD_Word);
                        case '-15'
                            IsREyeIn = str2double(CMD_Word);
                        case '-16'
                            IsVergenceIn = str2double(CMD_Word);
                    end
                end
            end
        end
        
        if Myudp.BytesAvailable >= packetSize
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
                        tempStr = UDP_Pack(tempIndex(i-1)+1:tempIndex(i)-1);
                    else
                        tempStr = UDP_Pack(1:tempIndex(i)-1);
                    end
                    [CMD, tempWord] = strtok(tempStr, ' ');
                    CMD_Word = strrep(tempWord,' ','');
                    switch CMD
                        case '-2'
                            switch CMD_Word
                                case '100' % 'start' signal from the GUI
                                    StateID = 100;
                                    FirstStep = 1;
                                case '101' % 'stop' signal from the GUI
                                    OnGoing = 0;
                                case '103' % 'exit' signal from the GUI
                                    OnGoing = 0;
                                case '102' % 'pause' signal from the GUI
                                    StateID = 110;
                                    FirstStep = 1;
                                
                            end                       
                        case '-17'
                            StateID = 6;
                            FirstStep = 1;
                        case '-102'
                            StiP.rewardDura = str2double(CMD_Word);
                        case '-103'
                            StiP.fixationAcqDura = str2double(CMD_Word);
                        case '-104'
                            StiP.fixationDura = str2double(CMD_Word);
                        case '-106'
                            StiP.ITI = str2double(CMD_Word);
                        case '-107'
                            Version = str2double(CMD_Word);
                        case '-108'
                            Vergence = str2double(CMD_Word);
                        case '-109'
                            VergenceOption = str2double(CMD_Word);  %%% 1-HV, 2-H
                        case '-11'
                            xPosFixation = str2double(CMD_Word)*VP.pixelsPerMm;
                        case '-12'
                            yPosFixation = str2double(CMD_Word)*VP.pixelsPerMm;
                        case '-13'
                            zPosFixation = str2double(CMD_Word);
                    end
                end
            end
        end
    else
        IsLEyeIn = 1; IsREyeIn = 1; IsVergenceIn = 1;
    end
    
    if connectServer && ~FirstRun && ~isequal([xPosFixation, yPosFixation, zPosFixation],[oldX, oldY, oldZ])
        StateID = 100;
        FirstStep = 1;
    end
    
    switch StateID
        case 110  %% initial state when server is in use and connected
            if FirstStep==1
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, VP.backgroundColor);
                end
                VP.vbl = Screen('Flip', VP.window,[],1);
                FirstStep = 0;
            else
                StateID = 110;                
            end
            
        case 100 %% inter trial interval
            if FirstStep==1
                oldX = xPosFixation;
                oldY = yPosFixation;
                oldZ = zPosFixation;
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, VP.backgroundColor);
                end
                VP.vbl = Screen('Flip', VP.window,[],1);
                StateTime = GetSecs;
                FirstStep = 0;
                FirstRun = 0;
            else
                EndT = GetSecs - StateTime;
                if EndT >= StiP.ITI
                    StateID = 99;
                    FirstStep = 1;
                end
            end
            
        case 99   %% draw check acquiring fixation point
            if FirstStep==1
                if connectServer
                    tempStr = ['50 1 ' num2str(xPosFixation) ' ' num2str(yPosFixation) ' ' num2str(zPosFixation) ' ' num2str(Version) ' ' LColor ' ' RColor];
                    SendUDPGui(Myudp,tempStr);  % send 'Trial_Start' signal
                    SendUDPGui(Myudp,'51'); %% start eye window
                    %SendUDPGui(Myudp,'53'); %% start vergence window
                end
                IsLEyeIn = 0; IsREyeIn = 0; IsVergenceIn=0;
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, [VP.backgroundColor(1:3)]);
                    Screen('DrawDots', VP.window, [xPosFixation+(VP.Rect(3)/2), -yPosFixation + (VP.Rect(4)/2)],VP.fixationDotSize, VP.fixationColor, [],2);
                end
                VP.vbl = Screen('Flip', VP.window,[],1);
                StateTime = GetSecs;
                if connectServer
                    SendUDPGui(Myudp,['6 113 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fix_On' signal
                end
                FirstStep = 0;
            else
                if connectServer
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(xPosFixation) ' ' num2str(yPosFixation) ' ' num2str(zPosFixation) ' ' num2str(Vergence) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                EndT = GetSecs - StateTime;
                
                if IsLEyeIn==1 && IsREyeIn==1 && IsVergenceIn==1 && EndT<= StiP.fixationAcqDura
                    StateID = 0;
                    FirstStep = 1;
                    if connectServer
                        SendUDPGui(Myudp,['6 114 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation acquired' signal
                    end
                else
                    if EndT > StiP.fixationAcqDura % fail to acquire fixation window
                        StateID = 10;
                        FirstStep = 1;
                        if connectServer
                            SendUDPGui(Myudp,['6 115 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation fail to acquired' signal
                        end
                    end
                end
                
            end
            
        case 0  %% check fixation holding time
            if FirstStep==1
                StateTime = GetSecs;
                FirstStep = 0;
            else
                if connectServer
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(xPosFixation) ' ' num2str(yPosFixation) ' ' num2str(zPosFixation) ' ' num2str(Vergence) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                
                EndT = GetSecs - StateTime;
                
                if IsLEyeIn~=1 || IsREyeIn~=1 || IsVergenceIn~=1  % break fixation window
                    StateID = 10;
                    FirstStep =1;
                    if connectServer
                        SendUDPGui(Myudp,['6 116 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation broken' signal
                    end
                else
                    if IsLEyeIn==1 && IsREyeIn==1 && IsVergenceIn==1 && EndT >= StiP.fixationDura % hold fixation window
                        StateID = 6;
                        FirstStep = 1;
                        if connectServer
                            SendUDPGui(Myudp,['6 117 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation hold' signal
                        end
                    end
                end
            end
            
        case 6  %% reward for holding fixation
            if FirstStep==1
                StateTime = GetSecs;
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    Datapixx('SetDoutValues', 1);
                    Datapixx('RegWrRd');
                end
                FinishedT = FinishedT+1;
                if connectServer
                    SendUDPGui(Myudp,['1 202 ' num2str(FinishedT)]);
                    SendUDPGui(Myudp,['6 140 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'rewarding juice' signal
                end
                FirstStep = 0;
            else
                
                EndT = GetSecs - StateTime;
                
                if EndT >= StiP.rewardDura 
                    if connectServer                        
                        if Datapixx('IsReady')
                            Datapixx('RegWrRd');
                            Datapixx('SetDoutValues', 0);
                            Datapixx('RegWrRd');
                        end
                        SendUDPGui(Myudp,['6 112 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Trial_End' signal
                    end
                    StateID = 100;
                    FirstStep = 1;
                end
            end
    end
end

if connectServer
    if ~isempty(Myudp)
        fclose(Myudp);
    end
    if ~isempty(Myudp_eye)
        fclose(Myudp_eye);
    end
end

ShowCursor; %show the cursor
Screen('CloseAll'); %close the display window
close all
Priority(0);

end


function CleanUDP(temp1, temp2)
    if ~isempty(temp1)
        fclose(temp1);
    end
    
    if ~isempty(temp2)
        fclose(temp2);    
    end
end

function SendUDPGui(Dest, tempStr)
    packetSize = 1024;
    SendStr(1:packetSize) = 'q'; % add fillers to match packet size
    SendStr(1:length(tempStr)+1) = [tempStr '/']; % add terminating charactor
    fwrite(Dest, SendStr);    % send UDP packet
end
