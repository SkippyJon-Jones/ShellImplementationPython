from enum import Enum

class job:
  def __init__(self, fg):
    self.processes = []
    self.fg = fg

  # checks if a job contains a given process
  def contains_process (self, process):
    for p in self.processes:
      if p.subprocess.pid == process.subprocess.pid:
        return True
    return False

  # gets a process from a given pid 
  def get_subprocess (self, pid):
    for process in self.processes:
      if process.subprocess.pid ==  pid:
        return process
    return None

  # gets the state of a job
  def get_state (self):
    return self.fg

  # sets the state of a job
  def set_state (self, state):
    self.fg = state

  # adds a process to a given job
  def add_process (self, subprocess):
    self.processes.append(process (subprocess))

  # prints all the subprocess's pids within a job
  def print_job (self):
    for p in self.processes:
      print (p.subprocess.pid)

# process class that allows a subprocess to also have a STATUS
# which can be RUNNING, STOPPED, or TERMINATED
class process:
  def __init__(self, subprocess):
    self.subprocess = subprocess
    self.status = STATUS.RUNNING

  def get_status (self):
    return self.status

  def set_status (self, state):
    self.status = state

# enum defining the differet possible states of a subprocess
class STATUS (Enum):
  RUNNING = 1
  STOPPED = 2
  TERMINATED = 3