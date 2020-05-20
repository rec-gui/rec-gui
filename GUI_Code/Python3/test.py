
from data_collection import DataFileObj


complete_data = DataFileObj.read_data('data/hoon_01_24_17_16_06_20')
if not complete_data:
    print " No data to read"


total_records = 0
total_eye_data_record = 0
total = 0
total_task_start = 0
total_task_end = 0
total_task_rec = 0
for dc in complete_data:
    # print "Config \n", dc['config'], '\n'
    # For each run what is the total records saved
    total += len(dc['data'])
    print "\ntotal record", total, "in task ", complete_data.index(dc)
    print "-----------------"

    for d in dc['data']:
        # How many task records
        # if complete_data.index(dc) == 23:
        #     print d
        if d[5][0] != '\x00':
            # print d
            command_type =  d[5].split()
            if command_type[0] == '6':


                if command_type[1] == '111':
                    total_task_start += 1
                    print d
                elif command_type[1] == '112':
                    total_task_end += 1
                    print d
            total_task_rec += 1
        else:
            total_eye_data_record += 1

        total_records +=1

print "\n\ntotal records read and iterated", total, total_records
print "total tasks", len(complete_data)
print "Total task records ", total_task_rec
print "total eye records ", total_eye_data_record
print "total start and end rec ", total_task_start, total_task_end






