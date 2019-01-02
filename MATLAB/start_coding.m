function start_coding(connectServer)

% Use this script as a template to start coding. 
% However we highly recommand you to check 'Fixation.m' together
% 'Fixation.m' is fully functioning script. 
% to abolt this script "Cntl+c" and type "sca" + enter

% connectServer : connect GUI or not

% for vision research, which requires screen information 
% before start this script, make it sure that GUI has correct screen size
% , distance and inter occular distance that are required to calculate
% conversion factors.

% for non-vision research, please ignore all Psychtoolbox function and
% related variables 

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
            disp('MATLAB needs to restart');
            disp('Press any key....');
            pause;
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
                disp('MATLAB needs to restart');
                disp('Press any key....');
                pause;
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
StiPF = 'stim_default.mat';
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

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%% Setup Display for Psychtoolbox
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if 1 == skipSync %skip Sync to deal with sync issues
    Screen('Preference','SkipSyncTests',1);
end
AssertOpenGL;
InitializeMatlabOpenGL(0);
global GL; %Global GL Data Structure,

Screen('Preference', 'Verbosity', 0); % Increase level of verbosity for debug purposes:
Screen('Preference','VisualDebugLevel', 0); % control verbosity and debugging, level:4 for developing, level:0 disable errors

VP.screenID = max(Screen('Screens'));    %Screen for display.
[VP.window,VP.Rect] = PsychImaging('OpenWindow',VP.screenID, VP.backGroundColor,[],[],[], VP.stereoMode, VP.multiSample);
[VP.windowCenter(1),VP.windowCenter(2)] = RectCenter(VP.Rect); %Window center

VP.windowWidthPix = VP.Rect(3)-VP.Rect(1);
VP.windowHeightPix = VP.Rect(4)-VP.Rect(2);

HideCursor(VP.screenID);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% initialize system variables
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


IsLEyeIn=0; IsREyeIn=0; IsVergenceIn = 0;
% fail safe default values. these parameters are updated when GUI is connected
VersionThreshold = 2; VergenceThreshold = 1; % default values for version, vergence error
VergenceOption = 2; % check vergence error only in horizontal positions of both eyes 

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


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Now calculate proper conversion factors for screen
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if VP.stereoMode == 4
    VP.screenWidthPix = 2*VP.windowWidthPix;
else
    VP.screenWidthPix = VP.windowWidthPix;
end
VP.screenHeightPix = VP.windowHeightPix;
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

% convert visual angle of fixation dot to pixel for drawing function of Psychtoolbox. 
% VP.fixationDotSize is in pixel
% StiP.dotSize is in degree
VP.fixationDotSize = round(StiP.dotSize * VP.pixelsPerDegree); 
if VP.fixationDotSize > 100
   VP.fixationDotSzie = 100; 
end
% VP.fixationDotSize = StiP.dotSize; 

glBlendFunc(GL.SRC_ALPHA,GL.ONE_MINUS_SRC_ALPHA); %Alpha blending for antialising
Screen('BlendFunction', VP.CopyBuffer, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

% define colors on left right eye 
LColor = 'green'; RColor = 'blue';


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% set start condition
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if connectServer
    StateID = 110; % wait until 'start' signal from the GUI
else
    StateID = 100; % go to inter trial interval to start experiment
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% MAIN WHILE-LOOP
% 'ESC' - user abort
% it stops when it recieves 'Stop' or 'Exit' signals from GUI
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
IsESC = 0; OnGoing = 1;

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
        % check UDP buffer has recieved packet or not
        if Myudp_eye.BytesAvailable >= packetSize
            % read buffer
            UDP_Pack = char(fread(Myudp_eye,packetSize))';
            flushinput(Myudp_eye);
            
            p=find(UDP_Pack=='q'); % remove filler
            if ~isempty(p)
                UDP_Pack(p)='';
            end
            
            %check terminating charactor 
            tempIndex = strfind(UDP_Pack,'/');
            if ~isempty(tempIndex)
                % check multiple commands from GUI
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
                            IsLEyeIn = str2double(CMD_Word);  % reporting of version error of Left eye
                        case '-15'
                            IsREyeIn = str2double(CMD_Word); % reporting of version error of right eye
                        case '-16'
                            IsVergenceIn = str2double(CMD_Word); % reporting of vergence error 
                    end
                end
            end
       end
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
                               case 100   % 'start' signal from the GUI
                                   StateID = 100;
                                   FirstStep = 1;
                               case 101   % 'stop' signal from the GUI
                                   OnGoing = 0;
                               case 103   % 'exit' signal from the GUI
                                   OnGoing = 0;
                               case 102   % 'pause' signal from the GUI
                                   StateID = 110;
                                   FirstStep = 1;
                           end
                       case -100   % indentifier -100 from GUI
                           % handling routine for message from GUI
                           
                       case -200  % indentifier -100 from GUI
                           % handleing routine for message from GUI
                           
                           
                   end
               end
           end
       end
    else
        % running without GUI connection. 
        IsLEyeIn = 1; IsREyeIn = 1; IsVergenceIn = 1;
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % main experimental control 
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    
    switch StateID
        case 100 %% inter trial interval period
            if FirstStep==1
                %
                % (add codes)
                FirstStep = 0;
            else
                % (add codes)
            end
        case 110   %% draw fixation and check acquiring fixation point
            if FirstStep==1
                % (add code)
                FirstStep = 0;
            else
                % (add code)
            end        
    end
end

% clean up UDP connection 
if connectServer
    if ~isempty(Myudp)
        fclose(Myudp);
    end
    if ~isempty(Myudp_eye)
        fclose(Myudp_eye);
    end
end
    
ShowCursor; %show the cursorsca

Screen('CloseAll'); %close all display windows used by Psychtoolbox
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

