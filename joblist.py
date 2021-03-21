from job import job
from job import STATUS

# joblist class handles the list of jobs the shell is running
class joblist:
  def __init__(self):
    self.jobs = [] 
  
  #add a job to the joblist
  def add_job (self, fg):
    self.jobs.append (job (fg))
    return self.jobs[len(self.jobs) - 1]

  # returns the fg job if any
  def get_fg_job (self):
    for j in self.jobs:
      if j.fg:
        return j
    return None
 
  # Returns true if the joblist has an fg job, false otherwise
  def has_fg_job (self):
    if (self.get_fg_job () == None):
      return False
    return True

  # Gets the job that contains the subprocess with pid pid 
  def get_job_with_process (self, pid):
    for j in self.jobs:
      for p in j.processes:
          if p.subprocess.pid == pid:
            return j
    return None

# takes a job and updates whether it is foreground, background, or terminated(removes from joblist), based on the status of its subprocesses
  def synchronize (self, job):
    #check if anything running
    somethingRunning = False
    for process in job.processes:
      if process.status == STATUS.RUNNING:
        somethingRunning = True
        break
    
    # if no processes are running, it is a no longer a foreground
    #  process
    if somethingRunning == False:
      job.fg = False
  
    for process in job.processes:
      if process.status != STATUS.TERMINATED:
        return
    # No process left running in job, remove from jobslist 
    self.jobs.remove (job)

  def print_jobs (self):
    for j in self.jobs:
      j.print_job ()

  def length (self):
    return len (self.jobs)