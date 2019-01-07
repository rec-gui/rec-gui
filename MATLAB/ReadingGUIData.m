clear all;
fName = 'test';
fPath = '/test_folder/';
fileID = fopen([fPath fName]);

frewind(fileID)
header = fread(fileID, 500, '*char')'; % read ascii header
config= []; data=[]; MessageList=[];
EndF = 0; NumT = 1; TStart = false;
InvalideTNum = 0;
while ~EndF    % reading main data
    [tempI, tempC] = fread(fileID, 1, 'int');
    if tempC>0
        config(NumT,1) = tempI;
        config(NumT,2:7) = fread(fileID, 6, 'float');
        config(NumT,8:9) = fread(fileID, 2, 'int');
        config(NumT,10:12) = fread(fileID, 3, 'float');
        config(NumT,13:20) = fread(fileID, 8, 'float');
        config(NumT,21:23) = fread(fileID, 3, 'int');
        datalength = config(NumT,1);
        for i=1:datalength
            data(NumT).TimeStamp_gui(i) = fread(fileID, 1, 'double');
            data(NumT).eyePositions(i,1:6) =  fread(fileID, 6, 'int'); %[right eyeX, right eyeY, right eyeZ, left eyeX, left eyeY, left eyeZ]
            tempStr = char(cellstr(fread(fileID, 64, '*char')'));
            
            if ~isempty(tempStr)
                if length(tempStr)<64
                    for ii=1:(64-length(tempStr))
                        tempStr = [tempStr 'q'];
                    end
                elseif length(tempStr)>64
                    tempStr(65:length(tempStr)) = '';
                end
                
                p=find(char(cellstr(tempStr))=='q');
                if ~isempty(p)
                    tempStr(p) ='';
                end
                
                tempData = strsplit(char(cellstr(tempStr)),' ');
                temp = str2double(cell2mat(tempData(1)));
                if temp==6   %%% magic number from MATLAB
                    CtnWord = str2double(cell2mat(tempData(2)));
                    switch CtnWord %% event code from MATLAB
                        case XX1
                    end
                end
            end
        end
        disp(['Trial Num: ' num2str(NumT-1) ',   length:' num2str(datalength)]);
    else
        EndF=1;
    end
end

