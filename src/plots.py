

def cores_per_job(interval_list):
    list = [[interval_list[i+1],len(df[(df.total_execution_slots > interval_list[i]) & (df.total_execution_slots <= interval_list[i+1])])] for i in range(len(interval_list)-1)]
    return list

def mem_per_job(interval_list):
    list = [[interval_list[i+1],len(df[(df.memory > interval_list[i]) & (df.memory <= interval_list[i+1])])] for i in range(len(interval_list)-1)]
    return list
