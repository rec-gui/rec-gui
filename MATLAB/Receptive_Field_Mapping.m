function [VP, pa, d, g, b] = Receptive_Field_Mapping(connectServer, connectRipple, StereoMode)

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Parameters needed
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

VP.stereoMode = StereoMode;         

% stereoMode specifies the type of stereo display algorithm to use:
%
% 0 == Mono display - No stereo at all.
%
% 1 == Flip frame stereo (temporally interleaved) - You'll need shutter
% glasses that are supported by the operating system, e.g., the
% CrystalEyes-Shutterglasses.
%
% 2 == Top/bottom image stereo with lefteye=top also for use with special
% CrystalEyes-hardware.
%
% 3 == Same, but with lefteye=bottom.
%
% 4 == Free fusion (lefteye=left, righteye=right): This - together wit a
% screenid of zero - is what you'll want to use on MS-Windows dual-display
% setups for stereo output.
%
% 5 == Cross fusion (lefteye=right ...)
%
% 6-9 == Different modes of anaglyph stereo for color filter glasses:
%
% 6 == Red-Green
% 7 == Green-Red
% 8 == Red-Blue
% 9 == Blue-Red
%
% 10 == Dual-Window stereo: Open two onscreen windows, first one will
% display left-eye view, 2nd one right-eye view. Direct all drawing and
% flip commands to the first window, PTB will take care of the rest. This
% mode is mostly useful for dual-display stereo on MacOS/X. It only works
% on reasonably modern graphics hardware, will abort with an error on
% unsupported hardware.
%
% 11 == Like mode 1 (frame-sequential) but using Screen's built-in method,
% instead of the native method supported by your graphics card.
%

VP.multiSample = 8;
VP.fixColor = [255 255 255];
VP.backGroundColor = [0.4 0.4 0.4]; %Gray-scale

skipSync = 1;
Priority(2);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Setup our display
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if 1 == skipSync %skip Sync to deal with sync issues
    Screen('Preference','SkipSyncTests',1);
end
AssertOpenGL;
InitializeMatlabOpenGL(0);
global GL; %Global GL Data Structure, Cannot 'BeginOpenGL' Without It.
Screen('Preference', 'Verbosity', 0); % Increase level of verbosity for debug purposes:
Screen('Preference','VisualDebugLevel', 0); % control verbosity and debugging, level:4 for developing, level:0 disable errors
VP.screenID = max(Screen('Screens'));    %Screen for display.
[VP.window,VP.Rect] = PsychImaging('OpenWindow',VP.screenID,[VP.backGroundColor],[],[],[], VP.stereoMode, VP.multiSample);
[VP.windowCenter(1),VP.windowCenter(2)] = RectCenter(VP.Rect); %Window center
VP.windowWidthPix = VP.Rect(3)-VP.Rect(1);
VP.windowHeightPix = VP.Rect(4)-VP.Rect(2);

% Initialize Datapixx connection
try
    PsychImaging('PrepareConfiguration'); %Prepare pipeline for configuration.
    PsychImaging('AddTask','General','UseDataPixx'); % Tell PTB we want to display on a DataPixx device.
    if ~Datapixx('IsReady')
        Datapixx('Open');
    end
    Datapixx('DisablePropixxLampLed');
    Datapixx('SetPropixxDlpSequenceProgram',2);
    Datapixx('EnablePropixxLampLed');
    Datapixx('SetPropixx3DCrosstalk', 1);
    Datapixx('RegWr');
catch
    disp('Datapixx not enabled');
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% Ripple Connection Initialization
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
if connectRipple
    xippmex('close');
    if xippmex('tcp')
        disp('Ripple device found!');
    else
        sca;
        error('Ripple device not found!');
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% GUI Parameter Initialization
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
LColor = 'green'; RColor = 'blue';
packetSize = 1024;
bufferLength = packetSize*1;
CMD=[]; CMD_Word=[]; updated_CMDs = [];
IsLEyeIn=0; IsREyeIn=0; IsVergenceIn = 0;
IsESC = 0;
Version_Fix = 2; Vergence = 1; VergenceOption = 3;
OnGoing = 1; IsESC = 0;
b.barColor = [0 0 0];
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% REC-GUI Connection
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

load('Receptive_Field_Mapping_Conf.mat');  % read default configuration before receiving configuraion from GUI

if connectServer
    Myudp = udp('100.1.1.3', 5001, 'LocalPort', 5002);
    if ~isempty(Myudp)
        set(Myudp,'ReadAsyncMode','continuous');
        set(Myudp,'InputBufferSize',bufferLength*2);
        set(Myudp,'OutputBufferSize',bufferLength*2);
        set(Myudp,'DatagramTerminateMode','on');
        fopen(Myudp);   
        
        SendUDPGui(Myudp, '-1 8256');   %% send probe packet to establish initial UDP connection
        StateTime = GetSecs;
        readasync(Myudp);  % start async. reading to control flow and check eye pos
        
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
                            case '-4'
                                VP.screenDistance = CMD_Word;                                
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

if connectServer
    Myudp_eye = udp('100.1.1.3', 5003, 'LocalPort', 5004);
    if ~isempty(Myudp_eye)
        set(Myudp_eye,'ReadAsyncMode','continuous');
        set(Myudp_eye,'InputBufferSize',bufferLength*2);
        set(Myudp_eye,'OutputBufferSize',bufferLength);
        set(Myudp_eye,'DatagramTerminateMode','on');
        fopen(Myudp_eye);        
        readasync(Myudp_eye);  % start async. reading to control flow and check eye pos
    end
end

if connectServer
    StateID = 110;
    FirstStep = 1;
else
    StateID = 100;
    FirstStep = 1;
end


% Now calculate proper conversion factors, etc.
if VP.stereoMode == 4
    VP.screenWidthPix = 2*VP.windowWidthPix;
else
    VP.screenWidthPix = VP.windowWidthPix;
end
VP.screenHeightPix = VP.windowHeightPix;
glBlendFunc(GL.SRC_ALPHA,GL.ONE_MINUS_SRC_ALPHA); %Alpha blending for antialising
VP.ifi = Screen('GetFlipInterval', VP.window);
VP.frameRate = Screen('FrameRate',VP.window);
if VP.stereoMode
    VP.stereoViews = 1;
else
    VP.stereoViews = 0;
end
% Calculate the width of one eye's view (in deg)
VP.screenWidthDeg = 2*atand(0.5*VP.screenWidthMm/VP.screenDistance);
VP.pixelsPerDegree = VP.screenWidthPix/VP.screenWidthDeg; % calculate pixels per degree
VP.pixelsPerMm = VP.screenWidthPix/VP.screenWidthMm; %% pixels/Mm
VP.MmPerDegree = VP.screenWidthMm/VP.screenWidthDeg;
VP.degreesPerMm = 1/VP.MmPerDegree;
VP.aspect = VP.screenWidthPix/VP.screenHeightPix;
% Initial flip to sync us to VBL and get start timestamp:
VP.vbl = Screen('Flip', VP.window);

% ListenChar(2); % Stop making keypresses show up in matlab
HideCursor;
KbName('UnifyKeyNames'); % Unify keyboard
pa.stimulus_names = [{'dots'},{'grating'},{'bar'}];
reward = 0; % Reward flag
pa.xPos = 0; % Default starting position
pa.yPos = 0;
updated_CMDs = [];
VP.CopyBuffer = Screen('OpenOffScreenWindow',-1, []); %, [], [], [], VP.multiSample);
Screen('BlendFunction', VP.CopyBuffer, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
VP.barWindow = Screen('OpenOffscreenWindow', -1',VP.backGroundColor);
Screen('BlendFunction',VP.barWindow, 'GL_SRC_ALPHA','GL_ONE_MINUS_SRC_ALPHA');
pa.randomAngles =  linspace(0,315,8);

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%% GO!
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

cleanupobj = onCleanup(@() CleanUP(Myudp, Myudp_eye));

while ~IsESC && OnGoing
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% REC-GUI Update of stim
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
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
                        rawStr = UDP_Pack(tempIndex(i-1)+1:tempIndex(i)-1);
                    else
                        rawStr = UDP_Pack(1:tempIndex(i)-1);
                    end
                    [CMD, tempWord] = strtok(rawStr, ' ');
                    updated_CMDs(i) = str2double(CMD);
                    CMD_Word = strrep(tempWord,' ','');
                    switch rawStr
                        case '-2 100'
                            StateID = 100;
                            FirstStep = 1;
                        case '-2 101'
                            OnGoing = 0;
                        case '-2 103'
                            OnGoing = 0;
                        case '-2 102'
                            StateID = 110;
                            FirstStep = 1;
                        case '-2 108'
                            StateID = 6;
                            FirstStep = 1;
                    end
                    
                    switch CMD
                        case '-9'
                            MUp = 0;
                            MDown = 1;
                        case '-10'
                            MUp = 1;
                            MDown = 0;
                        case '-11'
                            pa.xPos = str2double(CMD_Word)*VP.pixelsPerMm + VP.Rect(3)/2; % input from dragging, comes in mm where [0,0] is screen center
                        case '-12'
                            pa.yPos = -(str2double(CMD_Word))*VP.pixelsPerMm + VP.Rect(4)/2; % input from dragging, comes in mm where [0,0] is screen center
                        case '-18'
                            pa.stim_type = char(pa.stimulus_names(str2double(CMD_Word)));
                        case '-19'
                            d.dot_density = str2double(CMD_Word); % dots/deg^2
                        case '-20'
                            d.dot_size = str2double(CMD_Word); % deg
                        case '-22'
                            pa.radius = str2double(CMD_Word)./2; % deg in diameter, change to radius
                        case '-23'
                            pa.depth = str2double(CMD_Word); % input in mm
                        case '-24'
                            g.contrast = str2double(CMD_Word); % percentage
                        case '-25'
                            pa.angle = str2double(CMD_Word) - 180;
                        case '-26'
                            g.cycspeed = str2double(CMD_Word); % cycles/second
                        case '-27'
                            g.freq = str2double(CMD_Word)/VP.pixelsPerDegree; % translate from cycles/deg to cycles/pix for calcs
                        case '-28'
                            d.speed = str2double(CMD_Word); % deg/sec
                        case '-29'
                            pa.pulse_duration = str2double(CMD_Word);
                        case '-30'
                            pa.pulse_iti = str2double(CMD_Word);
                            if pa.pulse_iti > 0
                                pa.pulse = 1;
                            else
                                pa.pulse = 0;
                            end
                        case '-31'
                            pa.xPosFixation = (tand(str2double(CMD_Word))*VP.screenDistance); % input is in deg, we need pixels - change to mm here, later convert to screen coordinates
                        case '-32'
                            pa.yPosFixation = -(tand(str2double(CMD_Word))*VP.screenDistance); % input is in deg, we need pixels - chnage to mm here, later convert to screen coordinates
                        case '-33'
                            pa.zPosFixation = str2double(CMD_Word); % mm
                        case '-34'
                            b.bar_height = (tand(str2double(CMD_Word))*VP.screenDistance*VP.pixelsPerMm); % deg, width specified by the diameter parameter
                        case '-35'
                            b.bar_width = tand(str2double(CMD_Word))*VP.screenDistance*VP.pixelsPerMm;
                        case '-36'
                            b.barColor(1) = str2double(CMD_Word).*255;
                        case '-37'
                            b.barColor(2) = str2double(CMD_Word).*255;
                        case '-38'
                            b.barColor(3) = str2double(CMD_Word).*255;
                        case '-106'
                            pa.reward_duration = str2double(CMD_Word);
                        case '-107'
                            pa.ITI = str2double(CMD_Word);
                        case '-108'
                            VP.fixationDotSize = str2double(CMD_Word);
                        case '-109'
                            Version_Fix = str2double(CMD_Word);
                        case '-110'
                            pa.trial_duration = str2double(CMD_Word);
                        case '-111'
                            pa.fixationAcqDura = str2double(CMD_Word);
                        case '-112'
                            pa.fixationDura = str2double(CMD_Word);
                        case '-113'
                            pa.randDir = str2double(CMD_Word);
                            
                    end
                end
            end
        end
    else
        IsLEyeIn = 1; IsREyeIn = 1; Version_Fix = 3; IsVergenceIn = 1;
    end
    
    % Check for GUI commands in the range of values corresponding to
    % stimulus updates
    if any(updated_CMDs>=-110 & updated_CMDs<= -18)
        updated_CMDs = [];
        if StateID ~=110
            StateID = 100; % Stimulus parameter updates
            FirstStep = 1;
        end
    end
    
    [keydown, ~, keyCode] = KbCheck;
    if keydown
        keyCode = find(keyCode,1);
        if keyCode==10 || keyCode == KbName('escape')
            IsESC = 1;
        end
    end
    
    % Control stimulus using mouse if not connected to server
    if ~connectServer
        ShowCursor(0);
        % Get the mouse position if the button is pressed
        [mpa.xPos, mpa.yPos, button] = GetMouse(VP.window);
        if button(1)
            pa.xPos =  mpa.xPos; %(mpa.xPos - VP.Rect(3)/2)/VP.pixelsPerMm;
            pa.yPos = mpa.yPos; %(mpa.yPos - VP.Rect(4)/2)/VP.pixelsPerMm;
        end
    end
    
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% Begin States
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    switch StateID
        case 110 % Start-up State
            if FirstStep==1
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, [VP.backGroundColor(1:3)*255]);
                end
                VP.vbl = Screen('Flip', VP.window,[],1);
                FirstStep = 0;
            end
            
        case 100 % Stimulus Parameter Updates
            if FirstStep==1
                % Clear the screen
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, [VP.backGroundColor(1:3)*255]);
                end
                VP.vbl = Screen('Flip', VP.window, [],1);
                
                pa.radius_mm = tand(pa.radius)*VP.screenDistance;
                pa.radius_pix = pa.radius_mm*VP.pixelsPerMm;
                pa.depth_ratio = ((VP.screenDistance + pa.depth)./VP.screenDistance);
                
                % Fixation position
                VP.fix_stereoX(1) = (((VP.IOD/2 + pa.xPosFixation).*abs(VP.screenDistance./(VP.screenDistance+pa.zPosFixation))) - VP.IOD/2)*VP.pixelsPerMm + VP.Rect(3)/2;
                VP.fix_stereoX(2) = (VP.IOD/2 - ((VP.IOD/2 - pa.xPosFixation).*abs(VP.screenDistance./(VP.screenDistance+pa.zPosFixation))))*VP.pixelsPerMm + VP.Rect(3)/2;
                VP.fix_stereoY = (pa.yPosFixation.* abs(VP.screenDistance./(VP.screenDistance+pa.zPosFixation)))*VP.pixelsPerMm + VP.Rect(4)/2;
                
                if pa.pulse_iti > 0
                    pa.pulse = 1;
                else
                    pa.pulse = 0;
                end
                pa.depth_ratio = ((VP.screenDistance + pa.depth)./VP.screenDistance);
                switch pa.stim_type
                    case {'dots'}
                        pa.drawmask = 1;
                        d.dotCoordinates = [];
                        d.dotColor = [];
                        d.dot_angle = [];
                        d.dot_size_pix = [];
                        d.left_points = [];
                        d.right_points = [];
                        d.dot_size_pix = d.dot_size*VP.pixelsPerDegree;
                        d.num_dots = floor((2*pa.radius)^2*d.dot_density);
                        d.frame_speed_lat_mm = abs(tand(d.speed)*VP.screenDistance)/(VP.frameRate/2); % Based on degrees so must be based on depth since we move the dots in world coordinates
                        % Square Spacing Initialization
                        d.dotCoordinates(:,1:2) = -pa.radius_mm*pa.depth_ratio + 2*pa.radius_mm*pa.depth_ratio.*rand(d.num_dots,2); %-pa.persp_radius + 2*pa.persp_radius.*rand(d.num_dots,2);
                        d.dotCoordinates(:,3) = zeros(d.num_dots,1); %-sqrt(pa.staticDist^2 - (d.dotCoordinates(:,1)+pa.xPos).^2 - (d.dotCoordinates(:,2)+pa.yPos).^2);
                        % Make dots white and black
                        d.dotColor = [ones(ceil(d.num_dots/2),3); zeros(floor(d.num_dots/2),3)];
                        d.dotColor(:,4) = ones(d.num_dots,1).*g.contrast/100;
                        d.dot_size_pix = repmat(d.dot_size_pix,d.num_dots,1);
                        % Rotation angle for the stimulus
                        pa.planar_rotMat = rotationVectorToMatrix(d2r(-pa.angle+180).*[0,0,1]);
                        
                    case {'grating'}
                        % Adapted from PTB's DriftDemo2
                        pa.drawmask = 1; % We need a mask for this
                        
                        % Define Half-Size of the grating image.
                        texsize = ceil(pa.radius_pix);
                        
                        % Calculate parameters of the grating:
                        % First we compute pixels per cycle, rounded up to full pixels, as we
                        % need this to create a grating of proper size below:
                        p=ceil(1/g.freq); % g.freq is in cycles/pix
                        
                        % Also need frequency in radians:
                        fr=g.freq*2*pi;
                        
                        % This is the visible size of the grating. It is twice the half-width
                        % of the texture plus one pixel to make sure it has an odd number of
                        % pixels and is therefore symmetric around the center of the texture:
                        VP.visiblesize=2*texsize+1;
                        
                        % Create one single static grating image:
                        % Find the color values which correspond to white and black: Usually
                        % black is always 0 and white 255, but this rule is not true if one of
                        % the high precision framebuffer modes is enablbarColored via the
                        % PsychImaging() commmand, so we query the true values via the
                        % functions WhiteIndex and BlackIndex:
                        white=WhiteIndex(VP.screenID);
                        black=BlackIndex(VP.screenID);
                        
                        % Round gray to integral number, to avoid roundoff artifacts with some
                        % graphics cards:
                        gray=((white+black)/2);
                        % This makes sure that on floating point framebuffers we still get a
                        % well defined gray. It isn't strictly neccessary in this demo:
                        if gray == white
                            gray=white / 2;
                        end
                        
                        % Contrast 'inc'rement range for given white and gray values:
                        inc=(white-gray)*g.contrast/100;
                        
                        % We only need a texture with a single row of pixels(i.e. 1 pixel in height) to
                        % define the whole grating! If the 'srcRect' in the 'Drawtexture' call
                        % below is "higher" than that (i.e. visibleSize >> 1), the GPU will
                        % automatically replicate pixel rows. This 1 pixel height saves memory
                        % and memory bandwith, ie. it is potentially faster on some GPUs.
                        % However it does need 2 * texsize + p columns, i.e. the visible size
                        % of the grating extended by the length of 1 period (repetition) of the
                        % sine-wave in pixels 'p':
                        x = meshgrid(-texsize:texsize + p, 1);
                        
                        % Compute actual cosine grating:
                        grating=gray + inc*cos(fr*x);
                        % Store 1-D single row grating in texture:
                        g.gratingTex = Screen('MakeTexture', VP.window, grating);
                        % Rotation angle for the stimulus
                        pa.planar_rotMat = rotationVectorToMatrix(d2r(-pa.angle+180).*[0,0,1]);
                    case {'bar'}
                        pa.drawmask = 0;
                        b.barRect = CenterRectOnPoint([0 0 b.bar_width b.bar_height], VP.Rect(3)/2, VP.Rect(4)/2);
                        Screen('FillRect',VP.barWindow, [VP.backGroundColor]);
                        Screen('FillRect', VP.barWindow, [b.barColor, g.contrast/100*255], b.barRect);
                        b.barTex = Screen('MakeTexture',VP.window, VP.barWindow);
                        % Rotation angle for the stimulus
                        pa.planar_rotMat = rotationVectorToMatrix(d2r(pa.angle).*[0,0,1]);
                end
                
                
                
                % Setup an aperture that is based on the radius defined in screen
                % coordinates (mm)
                if pa.drawmask
                    if isfield(VP,'masktex')
                        clear VP.masktex
                    end
                    % Enable alpha blending for proper combination of the gaussian aperture
                    % with the drifting sine grating:
                    Screen('BlendFunction', VP.window, GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
                    % We create a  two-layer texture: One unused luminance channel which we
                    % just fill with the same color as the background color of the screen
                    % 'gray'. The transparency (aka alpha) channel is filled based on
                    % the size of the aperture
                    mask=ones(2*VP.windowWidthPix+1, 2*VP.windowHeightPix+1, 2)*VP.backGroundColor(1)*255;
                    [x,y]=meshgrid(-1*VP.windowWidthPix:1*VP.windowWidthPix,-1*VP.windowHeightPix:1*VP.windowHeightPix);
                    centerX = 0;
                    centerY = 0;
                    opaque = ones(size(x'));
                    for ii = 1:length(centerX)
                        opaque = min(opaque,(sqrt((x'+centerX(ii)).^2+(y'+centerY(ii)).^2) > pa.radius_pix));
                    end
                    opaque = opaque*1;
                    mask(:, :, 2)= opaque*255;
                    VP.masktex=Screen('MakeTexture', VP.window, permute(mask,[2,1,3]));
                end
                
                StateTime = GetSecs;
                
                FirstStep = 0;
            else
                EndT = GetSecs - StateTime;
                if pa.pulse == 1
                    pa.pulse_on = 1;
                    pa.pulse_initiate = 1;
                else
                    pa.pulse_on = 1;
                end
                if EndT>=pa.ITI
                    StateID = 99; % Fixation
                    FirstStep = 1;
                end
            end
            
        case 99   %% Fixation Point starts
            if FirstStep==1
                if connectServer
                    tempStr = ['50 1 ' num2str(pa.xPosFixation) ' ' num2str(-pa.yPosFixation) ' ' num2str(pa.zPosFixation) ' ' num2str(Version_Fix) ' ' LColor ' ' RColor];
                    SendUDPGui(Myudp,tempStr);  % send 'Trial_Start' signal
                    SendUDPGui(Myudp,'51'); %% start eye window
                    SendUDPGui(Myudp,'53'); %% start vergence window
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(pa.xPosFixation) ' ' num2str(pa.yPosFixation) ' ' num2str(pa.zPosFixation) ' ' num2str(Vergence) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                
                StateTime = GetSecs;
                
                for view = 0:VP.stereoViews
                    % Select 'view' to render (left- or right-eye):
                    Screen('SelectStereoDrawbuffer', VP.window, view);
                    Screen('FillRect',VP.window, [VP.backGroundColor(1:3)*255]);
                    Screen('DrawDots', VP.window, [VP.fix_stereoX(view+1), VP.fix_stereoY],VP.fixationDotSize, VP.fixColor, [],2);
                end
                VP.vbl = Screen('Flip', VP.window, [],1);
                if connectServer
                    SendUDPGui(Myudp,['6 111 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Trial Start' signal
                    SendUDPGui(Myudp,['6 113 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fix_On' signal
                end
                FirstStep = 0;
            else
                EndT = GetSecs - StateTime;
                if connectServer
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(pa.xPosFixation) ' ' num2str(pa.yPosFixation) ' ' num2str(pa.zPosFixation) ' ' num2str(Vergence) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                if IsLEyeIn==1 && IsREyeIn==1 && IsVergenceIn==1 && EndT<= pa.fixationAcqDura %fixation acquired, check if they have held it long enough to draw the stim
                    StateID = 98; % Pre stim
                    FirstStep = 1;
                    if connectServer
                        SendUDPGui(Myudp,['6 114 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation acquired' signal
                    end
                    if connectRipple
                        xippmex('digout',5,114); % Fixation acquired
                    end
                end
                if EndT > pa.fixationAcqDura % failed to acquire fixation window send to intertrial pause
                    StateID = 100; % ITI
                    FirstStep = 1;
                    if connectServer
                        SendUDPGui(Myudp,['6 115 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation failed to acquire' signal
                    end
                    if connectRipple
                        xippmex('digout',5,115); % Fixation Failed to acquire
                    end
                end
            end
            
        case 98 % Pre stimulus fixation holding time
            if FirstStep==1
                if connectServer
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(pa.xPosFixation) ' ' num2str(pa.yPosFixation) ' ' num2str(pa.zPosFixation) ' ' num2str(Vergence) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                StateTime = GetSecs;
                
                FirstStep = 0;
            else
                EndT = GetSecs - StateTime;
                if connectServer
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(pa.xPosFixation) ' ' num2str(pa.yPosFixation) ' ' num2str(pa.zPosFixation) ' ' num2str(Vergence) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                %Check fixation
                if IsLEyeIn~=1 || IsREyeIn ~=1 || IsVergenceIn~=1   % break fixation window, clear and send to new trial
                    StateID = 100; % ITI
                    FirstStep = 1;
                    if connectServer
                        SendUDPGui(Myudp,['6 116 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation broken' signal
                    end
                    if connectRipple
                        xippmex('digout',5,116); % Break during fixation
                    end
                end
                if IsLEyeIn==1 && IsREyeIn == 1 && IsVergenceIn==1 && EndT >= pa.fixationDura % Fixated long enough, show the stimulus
                    StateID = 97; % Stim
                    FirstStep = 1;
                    if connectServer
                        SendUDPGui(Myudp,['6 117 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation good' signal
                    end
                    if connectRipple
                        xippmex('digout',5,117);% send 'Fixation good' signal
                    end
                    
                end
            end
            
        case 97 % stimulus drawing
            if FirstStep==1
                if connectServer
                    SendUDPGui(Myudp,['6 118 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Stim #1 On' signal
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(pa.xPosFixation) ' ' num2str(pa.yPosFixation) ' ' num2str(pa.zPosFixation) ' ' num2str(Vergence) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                StateTime = GetSecs;
                FirstStep = 0;
                fn= 1;
            else
                EndT = GetSecs - StateTime;
                if connectServer
                    SendUDPGui(Myudp,'4');  %% request checking eye window
                    SendUDPGui(Myudp,['5 ' num2str(pa.xPosFixation) ' ' num2str(pa.yPosFixation) ' ' num2str(pa.zPosFixation) ' ' num2str(Vergence) ' ' num2str(VergenceOption)]);  %% request checking vergence
                end
                %Check fixation
                if IsLEyeIn~=1 || IsREyeIn~=1 || IsVergenceIn~=1   % break fixation window, clear and send to new trial
                    StateID = 100;
                    FirstStep = 1;
                    if connectServer
                        SendUDPGui(Myudp,['6 119 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'Fixation broke' signal
                    end
                    if connectRipple
                        xippmex('digout',5,119);
                    end
                    continue % Don't spend time drawing this frame, cancel the trial
                end
                
                if IsLEyeIn==1 && IsREyeIn==1 && IsVergenceIn==1 && EndT>= pa.trial_duration   % hold fixation window, continue checking
                    FirstStep = 1;
                    reward = 1;
                end
            end
            
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            %% Stimulus
            %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
            % Clear the screen to our offscreen buffer
            Screen('FillRect',VP.CopyBuffer, [VP.backGroundColor(1:3)*255]);
            if pa.pulse_on == 1
                % Depth Calculations
                % So that the stimulus still aligns with the mouse, we find the world
                % x,y,z that projects to the mouse x,y. Positive depths are
                % further, negative depths are nearer. We will use these when drawing later
                pa.worldMouse = [(pa.xPos- VP.Rect(3)/2)/VP.pixelsPerMm, (pa.yPos- VP.Rect(4)/2)/VP.pixelsPerMm].*pa.depth_ratio;
                
                switch pa.stim_type
                    case 'dots'
                        % Move dots laterally
                        d.dotCoordinates(:,1) = d.dotCoordinates(:,1) + d.frame_speed_lat_mm;
                        
                        d.dotCoordinates(:,3) = VP.screenDistance + pa.depth;
                        
                        % Check if we exited
                        pa.outside = find(d.dotCoordinates(:,1)>(pa.radius_mm*pa.depth_ratio)); %find(d.dotCoordinates(:,1)>pa.persp_radius);
                        
                        % Give new position to dots that have exited
                        if ~isempty(pa.outside)
                            % Square Spacing Initialization
                            d.dotCoordinates(pa.outside,1) = -pa.radius_mm*pa.depth_ratio;
                            d.dotCoordinates(pa.outside,2) = -pa.radius_mm*pa.depth_ratio + 2*pa.radius_mm*pa.depth_ratio.*rand(length(pa.outside),1);
                        end
                        
                        points = [d.dotCoordinates(:,1:3)];
                        
                        % rotate to our angle
                        points(:,1:3) = points(:,1:3)*pa.planar_rotMat;
                        
                        % Offset to cursor location
                        points(:,1:2) = points(:,1:2) + repmat([pa.worldMouse(1), pa.worldMouse(2)],size(points,1),1);
                        
                        % Dot sizes will all be the same, don't change with depth
                        d.persp_dot_size = [];
                        d.persp_dot_size = d.dot_size_pix;
                        
                        
                        % Calculate screen projections
                        VP.leftStereoX = ((VP.IOD/2 + points(:,1) ).*abs(VP.screenDistance./points(:,3))) - VP.IOD/2;
                        VP.rightStereoX = VP.IOD/2 - ((VP.IOD/2 - points(:,1)).*abs(VP.screenDistance./points(:,3)));
                        VP.stereoY = points(:,2).* abs(VP.screenDistance./points(:,3));
                        d.left_points(:,1:2) = [VP.leftStereoX.*VP.pixelsPerMm+VP.Rect(3)/2, VP.stereoY.*VP.pixelsPerMm+VP.Rect(4)/2];
                        d.right_points(:,1:2) = [VP.rightStereoX.*VP.pixelsPerMm+VP.Rect(3)/2, VP.stereoY.*VP.pixelsPerMm+VP.Rect(4)/2];
                        
                        % For aperture
                        VP.mouse_leftStereoX = ((VP.IOD/2 + pa.worldMouse(1)).*abs(VP.screenDistance./(VP.screenDistance+pa.depth))) - VP.IOD/2;
                        VP.mouse_rightStereoX = VP.IOD/2 - ((VP.IOD/2 - pa.worldMouse(1)).*abs(VP.screenDistance./(VP.screenDistance+pa.depth)));
                        VP.mouse_stereoY = pa.worldMouse(2).* abs(VP.screenDistance./(VP.screenDistance+pa.depth));
                        left_position = [VP.mouse_leftStereoX.*VP.pixelsPerMm+VP.Rect(3)/2, VP.mouse_stereoY.*VP.pixelsPerMm+VP.Rect(4)/2];
                        right_position = [VP.mouse_rightStereoX.*VP.pixelsPerMm+VP.Rect(3)/2, VP.mouse_stereoY.*VP.pixelsPerMm+VP.Rect(4)/2];
                        
                        Screen('SelectStereoDrawbuffer', VP.window, 0);
                        % Draw all our dots to the offscreen buffer
                        Screen('DrawDots',VP.window, d.left_points(:,1:2)', d.persp_dot_size', d.dotColor(:,1:4)'.*255,[],2);
                        if pa.drawmask == 1
                            center = [left_position(1), left_position(2)]; %[(pa.xPos*VP.pixelsPerMm)+VP.windowWidthPix/2, (pa.yPos*VP.pixelsPerMm)+VP.windowHeightPix/2]; %[pa.xPos, pa.yPos];
                            destRect = CenterRectOnPoint(VP.Rect.*2,center(1),center(2));
                            Screen('DrawTexture',VP.window,VP.masktex,[],destRect);
                        end
                        Screen('SelectStereoDrawbuffer', VP.window, 1);
                        % Draw all our dots to the offscreen buffer
                        Screen('DrawDots',VP.window, d.right_points(:,1:2)', d.persp_dot_size', d.dotColor(:,1:4)'.*255,[],2);
                        if pa.drawmask == 1
                            center = [right_position(1), right_position(2)];
                            destRect = CenterRectOnPoint(VP.Rect.*2,center(1),center(2));
                            Screen('DrawTexture',VP.window,VP.masktex,[],destRect);
                        end
                        
                    case 'grating'
                        % Recompute p, this time without the ceil() operation from above.
                        % Otherwise we will get wrong drift speed due to rounding errors!
                        p=1/g.freq;  % pixels/cycle
                        
                        % Translate requested speed of the grating (in cycles per second) into
                        % a shift value in "pixels per frame", for given waitduration: This is
                        % the amount of pixels to shift our srcRect "aperture" in horizontal
                        % directionat each redraw:
                        g.shiftperframe= g.cycspeed * p / (VP.frameRate/2);
                        
                        % Shift the grating by "shiftperframe" pixels per frame:
                        % the mod'ulo operation makes sure that our "aperture" will snap
                        % back to the beginning of the grating, once the border is reached.
                        % Fractional values of 'xoffset' are fine here. The GPU will
                        % perform proper interpolation of color values in the grating
                        % texture image to draw a grating that corresponds as closely as
                        % technical possible to that fractional 'xoffset'. GPU's use
                        % bilinear interpolation whose accuracy depends on the GPU at hand.
                        % Consumer ATI hardware usually resolves 1/64 of a pixel, whereas
                        % consumer NVidia hardware usually resolves 1/256 of a pixel. You
                        % can run the script "DriftTexturePrecisionTest" to test your
                        % hardware...
                        xoffset = mod(fn*g.shiftperframe,p);
                        
                        % Define shifted srcRect that cuts out the properly shifted rectangular
                        % area from the texture: We cut out the range 0 to visiblesize in
                        % the vertical direction although the texture is only 1 pixel in
                        % height! This works because the hardware will automatically
                        % replicate pixels in one dimension if we exceed the real borders
                        % of the stored texture. This allows us to save storage space here,
                        % as our 2-D grating is essentially only defined in 1-D:
                        g.srcRect=[xoffset 0 xoffset + VP.visiblesize VP.visiblesize];
                        
                        % Calculate screen projections based on depth
                        VP.leftStereoX = ((VP.IOD/2 + pa.worldMouse(1)).*abs(VP.screenDistance./(VP.screenDistance+pa.depth))) - VP.IOD/2;
                        VP.rightStereoX = VP.IOD/2 - ((VP.IOD/2 - pa.worldMouse(1)).*abs(VP.screenDistance./(VP.screenDistance+pa.depth)));
                        VP.stereoY = pa.worldMouse(2).* abs(VP.screenDistance./(VP.screenDistance+pa.depth));
                        left_position = [VP.leftStereoX.*VP.pixelsPerMm+VP.Rect(3)/2, VP.stereoY.*VP.pixelsPerMm+VP.Rect(4)/2];
                        right_position = [VP.rightStereoX.*VP.pixelsPerMm+VP.Rect(3)/2, VP.stereoY.*VP.pixelsPerMm+VP.Rect(4)/2];
                        
                        g.position_left = CenterRectOnPoint([0 0 VP.visiblesize VP.visiblesize], left_position(1),left_position(2));
                        g.position_right = CenterRectOnPoint([0 0 VP.visiblesize VP.visiblesize], right_position(1),right_position(2));
                        
                        Screen('SelectStereoDrawbuffer', VP.window, 0);
                        % Draw grating texture rotated by "angle":
                        Screen('DrawTexture', VP.window, g.gratingTex, g.srcRect, g.position_left, -pa.angle);
                        % Draw our mask in the proper location
                        if pa.drawmask == 1
                            center = [left_position(1), left_position(2)]; %[(pa.xPos*VP.pixelsPerMm)+VP.windowWidthPix/2, (pa.yPos*VP.pixelsPerMm)+VP.windowHeightPix/2]; %[pa.xPos, pa.yPos];
                            destRect = CenterRectOnPoint(VP.Rect.*2,center(1),center(2));
                            Screen('DrawTexture',VP.window,VP.masktex,[],destRect);
                        end
                        Screen('SelectStereoDrawbuffer', VP.window, 1);
                        % Draw grating texture rotated by "angle":
                        Screen('DrawTexture', VP.window, g.gratingTex, g.srcRect, g.position_right, -pa.angle);
                        % Draw our mask in the proper location
                        if pa.drawmask == 1
                            center = [right_position(1), right_position(2)];
                            destRect = CenterRectOnPoint(VP.Rect.*2,center(1),center(2));
                            Screen('DrawTexture',VP.window,VP.masktex,[],destRect);
                        end
                        
                    case 'bar'
                        % Calculate screen projections based on depth
                        VP.leftStereoX = ((VP.IOD/2 + pa.worldMouse(1)).*abs(VP.screenDistance./(VP.screenDistance+pa.depth))) - VP.IOD/2;
                        VP.rightStereoX = VP.IOD/2 - ((VP.IOD/2 - pa.worldMouse(1)).*abs(VP.screenDistance./(VP.screenDistance+pa.depth)));
                        VP.stereoY = pa.worldMouse(2).* abs(VP.screenDistance./(VP.screenDistance+pa.depth));
                        left_position = [VP.leftStereoX.*VP.pixelsPerMm+VP.Rect(3)/2, VP.stereoY.*VP.pixelsPerMm+VP.Rect(4)/2];
                        right_position = [VP.rightStereoX.*VP.pixelsPerMm+VP.Rect(3)/2, VP.stereoY.*VP.pixelsPerMm+VP.Rect(4)/2];
                        
                        b.position_left = CenterRectOnPoint(b.barRect, left_position(1),left_position(2));
                        b.position_right = CenterRectOnPoint(b.barRect, right_position(1),right_position(2));
                        
                        Screen('SelectStereoDrawbuffer', VP.window, 0);
                        % Draw grating texture rotated by "angle":
                        Screen('DrawTexture', VP.window, VP.barWindow, b.barRect, b.position_left, -pa.angle,[],[g.contrast/100]);
                        Screen('SelectStereoDrawbuffer', VP.window, 1);
                        % Draw grating texture rotated by "angle":
                        Screen('DrawTexture', VP.window, VP.barWindow, b.barRect, b.position_right, -pa.angle, [], [g.contrast/100]);
                end
            end
            
            % Check if we are using a pulsing stimulus
            if pa.pulse == 1
                if pa.pulse_on == 1
                    if pa.pulse_initiate == 1
                        pa.pulse_on_start = GetSecs;
                        pa.pulse_initiate = 0;
                        
                    else
                        pa.pulse_on_dura = GetSecs - pa.pulse_on_start;
                        if pa.pulse_on_dura>=pa.pulse_duration
                            pa.pulse_on = 0;
                            pa.pulse_off_initiate = 1;
                        end
                    end
                else
                    if pa.pulse_off_initiate == 1
                        pa.pulse_off_start = GetSecs;
                        pa.pulse_off_initiate = 0;
                    else
                        pa.pulse_off_dura = GetSecs - pa.pulse_off_start;
                        if pa.pulse_off_dura>=pa.pulse_iti
                            pa.pulse_on = 1;
                            pa.pulse_initiate = 1;
                            if pa.randDir % Using a random direction?
                                % Rotation angle for the stimulus
                                pa.angle = randsample(pa.randomAngles,1);
                                pa.planar_rotMat = rotationVectorToMatrix(d2r(-pa.angle+180).*[0,0,1]);
                            end
                        end
                    end
                end
            end
            
            Screen('SelectStereoDrawbuffer', VP.window, 0);
            
            % Photodiode masks for each eye so stimulus doesn't interrupt
            % signal
            Screen('DrawDots',VP.window, [VP.Rect(1)+25 VP.Rect(4)-25], 50, [VP.backGroundColor(1:3)*255],[0 0],2);
            Screen('DrawDots',VP.window, [VP.Rect(3)-25 VP.Rect(4)-25], 50, [VP.backGroundColor(1:3)*255],[0 0],2);
            if pa.pulse_on
                % Draw Left photodiode circle
                Screen('DrawDots',VP.window, [VP.Rect(1)+25 VP.Rect(4)-25], 50, [255 255 255],[0 0],2);
            end
            Screen('DrawDots', VP.window, [VP.fix_stereoX(1), VP.fix_stereoY],VP.fixationDotSize, VP.fixColor, [],2);
            
            Screen('SelectStereoDrawbuffer', VP.window, 1);
            
            % Photodiode masks for each eye so stimulus doesn't interrupt
            % signal
            Screen('DrawDots',VP.window, [VP.Rect(1)+25 VP.Rect(4)-25], 50, [VP.backGroundColor(1:3)*255],[0 0],2);
            Screen('DrawDots',VP.window, [VP.Rect(3)-25 VP.Rect(4)-25], 50, [VP.backGroundColor(1:3)*255],[0 0],2);
            if pa.pulse_on
                % Draw Right photodiode circle
                 Screen('DrawDots',VP.window, [VP.Rect(3)-25 VP.Rect(4)-25], 50, [255 255 255],[0 0],2);
            end
            Screen('DrawDots', VP.window, [VP.fix_stereoX(2), VP.fix_stereoY],VP.fixationDotSize, VP.fixColor, [],2);
            
            VP.vbl = Screen('Flip', VP.window, [],0);
            fn = fn+1;
            if connectRipple
                xippmex('digout',5,10000 + pa.xPos);
                xippmex('digout',5,20000 + pa.yPos);
            end
    end
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    %% Rewarding
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    if reward == 1 && StateID~=110
        if FirstStep == 1
            reward_start = GetSecs;
            StateTime = reward_start;
            FirstStep = 0;
            if connectServer
                SendUDPGui(Myudp,['6 140 ' num2str(StateID) ' ' num2str(StateTime)]);  % send 'rewarding juice' signal
            end
%             if Datapixx('IsReady')
%                 Datapixx('RegWrRd');
%                 StateTime = Datapixx('GetTime');
%                 Datapixx('SetDoutValues', 1); %% start rewarding (bit0)
%                 Datapixx('RegWrRd');
%             else
                if connectServer
                    SendUDPGui(Myudp, '60'); %reward on
                end
%             end
            if connectRipple
                xippmex('digout',5,140); % reward on
            end
        else
            reward_time = GetSecs - reward_start;
            if reward_time >= pa.reward_duration
                reward = 0;
%                 if Datapixx('IsReady')
%                     Datapixx('SetDoutValues',0); %% stop rewarding (bit0)
%                     Datapixx('RegWrRd');
%                 else
                    if connectServer
                        SendUDPGui(Myudp, '61'); %reward off
                    end
%                 end
                if connectRipple
                    xippmex('digout',5,141); % reward off
                end
            end
        end
    end
end

%%%%%%%%%%%%%%%%%%%%%%
%% Clean Up
%%%%%%%%%%%%%%%%%%%%%%
if connectServer
    if ~isempty(Myudp)
        fclose(Myudp);
    end
    if ~isempty(Myudp_eye)
        fclose(Myudp_eye);
    end
end

if connectRipple
    if xippmex
        xippmex('close')
    end
end

RestrictKeysForKbCheck([]); % Reenable all keys for KbCheck:
ListenChar; % Start listening to GUI keystrokes again
ShowCursor;
clear moglmorpher;
Screen('CloseAll');%sca;
clear moglmorpher;
Priority(0);

end

function SendUDPGui(Dest, tempStr)
packetSize = 1024;
SendStr(1:packetSize) = 'q';
SendStr(1:length(tempStr)+1) = [tempStr '/'];
fwrite(Dest, SendStr);    %% send UDP packet
end

function CleanUP(UDP1, UDP2)
if ~isempty(UDP1)
    fclose(UDP1);
end
if ~isempty(UDP2)
    fclose(UDP2);
end

if xippmex
    xippmex('close')
end

end
