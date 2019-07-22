function Fixation(connectServer, connectRipple)

% GAZE FIXATION TRAINING 
% in GUI, use fixation.conf to configure GUI to make it work with this
% script.
% to abolt this script "Cntl+c" and type "sca" + enter

% connectServer : connect GUI or not
% connectRipple : connect Ripple system or not

% default fixation point is 0,0,0 and it can be updated by GUI with 
% 'feedback' or 'dragging' options

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

FirstStep = 1;  
PresentedTNum = 0;  % total trial number presented
FinishedTNum = 0; % total finished trial (correct + wrong)
CorrectTNum = 0; % total rewarded trails
WrongTNum = 0; % total missed trials
TrialPass = 0; % system flag for correct trial

IsLEyeIn=0; IsREyeIn=0; IsVergenceIn = 0;

% fail safe default values. these parameters are updated when GUI is connected
VersionThreshold = 2; VergenceThreshold = 1; % default values for version, vergence error
VergenceOption = 2; % check vergence error only in horizontal positions of both eyes 


%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% is Ripple system connected?
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if connectRipple   % to use Ripple
	xippmex('close');
	if xippmex
		disp('Ripple device found!');
    else
        disp('Ripple device not found!');
        connectRipple = 0;
	end
end

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

% default position of fixation point (mm)
% when GUI send new position of fixation point
% these values will be updated in runtime
xPosFixation = 0; % horizontal position
yPosFixation = 0; % vertical position
zPosFixation = 0; % distance from the eye (depth)

% temporary buffer for checking updated position
yPosOld = yPosFixation; 
xPosOld = xPosFixation; 
zPosOld = zPosFixation; 

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
                       case -17
                           StateID = 6;
                           FirstStep = 1;
                       case -106
                           StiPF = CMD_Word;
                           try
                               load(StiPF);
                           catch
                               SendUDPGui(Myudp, ['1 fail to load ' StiPF]);
                           end
                       case -101
                           StiP.ITI = str2double(CMD_Word);  % update inter trial interval
                           save(StiPF,'StiP');
                       case -102
                           StiP.fixationDura = str2double(CMD_Word); % update fixating duration
                           save(StiPF,'StiP');
                       case -103
                           StiP.fixationAcqDura = str2double(CMD_Word); % update duration for acquiring fixation
                           save(StiPF,'StiP');
                       case -104
                           StiP.punishDelay = str2double(CMD_Word); % update punishing delay
                           save(StiPF,'StiP');
                       case -105
                           StiP.rewardDura = str2double(CMD_Word);  % update reward duration
                           save(StiPF,'StiP');
                       case -107
                           VersionThreshold = str2double(CMD_Word); % update version error threshold
                       case -108
                           VergenceThreshold = str2double(CMD_Word); % update vergence error threshold
                       case -109
                           VergenceOption = str2double(CMD_Word);  % 1-horizontal + vertical , 2-horizontal only
                       case -115
                           tempR = str2double(CMD_Word);
                           VP.fixationDotSize = round(tempR * VP.pixelsPerDegree); % update fixation dot size
                           if VP.fixationDotSize > 100
                               VP.fixationDotSzie = 100;
                           end
                           StiP.dotSize = tempR; % save dot size as degree                           
                           save(StiPF,'StiP');                           
                           % if GUI has enabled 'feedback' or 'dragging'
                           % options, GUI sends new fixation point updated by
                           % mouse click or dragging on the monitoring screen
                           % of the GUI
                       case -11
                           xPosFixation = str2double(CMD_Word); % update horizontal position of fixation point
                           if xPosFixation ~= xPosOld % if it is new position, trial will be restarted
                               xPosOld = xPosFixation;
                               StateID = 100;
                               FirstStep=1;
                           end
                       case -12
                           yPosFixation = -1* str2double(CMD_Word); % update vertical position of fixation point
                           if yPosFixation ~= yPosOld % if it is new position, trial will be restarted
                               yPosOld = yPosFixation;
                               StateID = 100;
                               FirstStep=1;
                           end
                       case -13
                           zPosFixation = str2double(CMD_Word); % update distance of fixation point (depth)
                           if zPosFixation ~= zPosOld % if it is new position, trial will be restarted
                               zPosOld = zPosFixation;
                               StateID = 100;
                               FirstStep=1;
                           end
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
                
                %reset TTL for reward
                if Datapixx('IsReady') % if there is DataPixx
                    Datapixx('SetDoutValues',0);
                    % reset TTL for reward signal low
                    % as reward line connected in first bit of DO in DataPixx (bit0)
                    Datapixx('RegWrRd');
                else
                    %<add code to reset reward TTL signal control>
                end
                
                % prepare blank screen
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, VP.backGroundColor);
                end
                % draw blank screen
                Screen('Flip', VP.window, [],1);
                
                % calculate Fixation position
                VP.fix_stereoX(1) = (((VP.IOD/2 + xPosFixation).*abs(VP.screenDistance./(VP.screenDistance+zPosFixation))) - VP.IOD/2)*VP.pixelsPerMm + VP.Rect(3)/2;
                VP.fix_stereoX(2) = (VP.IOD/2 - ((VP.IOD/2 - xPosFixation).*abs(VP.screenDistance./(VP.screenDistance+zPosFixation))))*VP.pixelsPerMm + VP.Rect(3)/2;
                VP.fix_stereoY = (yPosFixation.* abs(VP.screenDistance./(VP.screenDistance+zPosFixation)))*VP.pixelsPerMm + VP.Rect(4)/2;
                
                % count trial numbers
                PresentedTNum = PresentedTNum + 1;
                if TrialPass == 1
                    FinishedTNum = FinishedTNum + 1;
                end
                
                % if there is DatPixx, use its own timer or initialize MATLAB timer
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    StateTime = Datapixx('GetTime');
                else
                    StateTime = tic;
                end
                
                FirstStep = 0;
            else
                % if there is DatPixx, use its own timer or initialize MATLAB timer
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    EndT = Datapixx('GetTime') - StateTime;
                else
                    EndT = toc(StateTime);
                end
                
                % send trial information to GUI
                if connectServer
                    tempStr = [num2str(xPosFixation) ' ' str2double(-1*yPosFixation) ' ' str2double(zPosFixation) ' ' num2str(StateID) ' ' num2str(StateTime)];
                    SendUDPGui(Myudp,['6 111 ' tempStr]);  % send 'Trial_Start' signal
                    SendUDPGui(Myudp,['1 200 ' num2str(PresentedTNum)]);  % update system low in GUI
                    SendUDPGui(Myudp,['1 201 ' num2str(FinishedTNum)]); % update system low in GUI
                end
                
                % check timer reaches inter trial interal or not
                if EndT >= StiP.ITI
                    StateID = 99;
                    FirstStep = 1;
                end
            end
        case 99   %% draw fixation and check acquiring fixation point
            if FirstStep==1
                % setup fixation window for checking fixation violation
                if connectServer
                    tempStr = ['50 1 ' num2str(xPosFixation) ' ' num2str(-1*yPosFixation) ' ' num2str(zPosFixation) ' ' num2str(VersionThreshold) ' ' LColor ' ' RColor];
                    SendUDPGui(Myudp,tempStr);  % send 'Trial_Start' signal
                    SendUDPGui(Myudp,'51'); %% start eye window
                    SendUDPGui(Myudp,'53'); %% start vergence window
                    IsLEyeIn = 0; IsRyeIn = 0; IsVergenceIn=0;
                end
                
                % prepare fixation point on the screen
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, VP.backGroundColor);
                    Screen('DrawDots', VP.window, [VP.fix_stereoX(view+1), VP.fix_stereoY],VP.fixationDotSize, VP.fixColor, [],2);
                end
                % draw fixation point on the screen
                Screen('Flip', VP.window, [],1);
                
                if connectRipple
                    xippmex('digout',5,113);  % send event (fixation is presented) to Ripple
                end
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    StateTime = Datapixx('GetTime');
                else
                    StateTime = tic;
                end
                if connectServer
                    SendUDPGui(Myudp,['6 113 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fix_On' signal
                end
                FirstStep = 0;
            else
                if connectServer
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(xPosFixation) ' ' num2str(yPosFixation) ' ' num2str(zPosFixation) ' ' num2str(VergenceThreshold) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    EndT = Datapixx('GetTime') - StateTime;
                else
                    EndT = toc(StateTime);
                end
                
                if IsLEyeIn==1 && IsREyeIn==1 && IsVergenceIn==1 && EndT<= StiP.fixationAcqDura
                    StateID = 0;
                    FirstStep = 1;
                    if connectRipple
                        xippmex('digout',5,114); % send event (fixation acquired) to Ripple
                    end
                    if connectServer
                        SendUDPGui(Myudp,['6 114 ' num2str(StateID) ' ' num2str(StateTime)]);  % send event (fixation acquired) to GUI
                    end
                end
                if EndT > StiP.fixationAcqDura % fail to acquire fixation window in time
                    StateID = 10;
                    FirstStep = 1;
                    if connectRipple
                        xippmex('digout',5,115);
                    end
                    if connectServer
                        SendUDPGui(Myudp,['6 115 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation fail to acquired' signal
                    end
                    TrialPass = 0;
                end
            end
        case 0  %% check fixation holding time
            if FirstStep==1
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    StateTime = Datapixx('GetTime');
                else
                    StateTime = tic;
                end
                FirstStep = 0;
            else
                if connectServer
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(xPosFixation) ' ' num2str(yPosFixation) ' ' num2str(zPosFixation) ' ' num2str(VergenceThreshold) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    EndT = Datapixx('GetTime') - StateTime;
                else
                    EndT = toc(StateTime);
                end
                
                if IsLEyeIn~=1 || IsREyeIn~=1 || IsVergenceIn~=1  % break fixation window
                    StateID = 10;
                    WrongTNum = WrongTNum + 1;
                    FirstStep =1;
                    if connectRipple
                        xippmex('digout',5,116);  % send event (fixation broken) to Ripple
                    end
                    if connectServer
                        SendUDPGui(Myudp,['6 116 ' num2str(StateID) ' ' num2str(StateTime)]);  % send event (fixation broken) to GUI
                    end
                    TrialPass = 0;
                end
                
                if IsLEyeIn==1 && IsREyeIn==1 && IsVergenceIn==1 && EndT >= StiP.fixationDura % hold fixation window
                    StateID = 6;
                    CorrectTNum = CorrectTNum + 1;
                    FirstStep = 1;
                    if connectRipple
                        xippmex('digout',5,117);  % send event (holding fixation enough) to Ripple
                    end
                    if connectServer
                        SendUDPGui(Myudp,['6 117 ' num2str(StateID) ' ' num2str(StateTime)]);  % send event (holding fixation enough) to GUI
                    end
                end
                
            end
        case 6  %% reward for holding fixation
            if FirstStep==1
                
                if connectRipple
                    xippmex('digout',5,140); % send event (reward on) to Ripple
                end
                
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    StateTime = Datapixx('GetTime');
                    Datapixx('SetDoutValues', 1); % start rewarding (bit0)
                    Datapixx('RegWrRd');
                else 
                    StateTime = tic;
                    % <add code for start rewarding>
                end
                TrialPass = 1;
                
                if connectServer
                    SendUDPGui(Myudp,['6 140 ' num2str(StateID) ' ' num2str(StateTime)]);  % send event (reward on) signal to GUI
                end
                FirstStep = 0;
            else
                
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    EndT = Datapixx('GetTime') - StateTime;
                else
                    EndT = toc(StateTime);
                end
                
                if EndT >= StiP.rewardDura % check timer reaches reward duration
                    if Datapixx('IsReady')
                        Datapixx('SetDoutValues',0); % stop rewarding (bit0)
                        Datapixx('RegWrRd');
                    else
                        % < add code for stop rewarding>
                    end
                    if connectRipple
                        xippmex('digout',5,112); % send event (trial end) to Ripple
                    end
                    
                    if connectServer
                        SendUDPGui(Myudp,['6 112 ' num2str(StateID) ' ' num2str(StateTime)]);  % send event (trial end) to GUI
                    end
                    StateID = 100;
                    FirstStep = 1;
                end
            end
        case 10 % trial ends
            if FirstStep==1
                % prepare blank screen
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, VP.backGroundColor);
                end
                % draw blank screen
                Screen('Flip', VP.window, [],1);
                
                if connectRipple
                    xippmex('digout',5,112);  % send event (trial end) to Ripple
                end
                if connectServer
                    SendUDPGui(Myudp,['6 112 ' num2str(StateID) ' ' num2str(StateTime)]);  % send event (trial end) signal
                end
                
                % timer start for punishing delay
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    StateTime = Datapixx('GetTime');
                else
                    StateTime = tic;
                end
                FirstStep = 0;
            else
                if Datapixx('IsReady')
                    Datapixx('RegWrRd');
                    EndT = Datapixx('GetTime') - StateTime;
                else
                    EndT = toc(StateTime);
                end
                if EndT >= StiP.punishDelay % if timer reaches punishing delay
                    StateID = 100;
                    FirstStep = 1;
                end
            end
        case 110
            % initial state when server is in use and connected
            % it shows blank screen and wait until 'StateID' changes
            if FirstStep==1
                %reset TTL for reward
                if Datapixx('IsReady')
                    Datapixx('SetDoutValues',0); %% stop rewarding (bit0)
                    Datapixx('RegWrRd');
                else
                    % <add code to reset TTL for reward>
                end
                % prepare blank screen
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, VP.backGroundColor);
                end
                % draw blank screen
                Screen('Flip', VP.window, [],1);
                
                FirstStep = 0;
            else
                
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

if Datapixx('isReady')	
	Datapixx('SetDoutValues',0); %% stop rewarding (bit0)
    Datapixx('RegWrRd');
    Datapixx('Close');    
else
    % <add codes for reseting TTL of rewarding
end

if connectRipple
	if xippmex
		xippmex('close');
	end
end

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

