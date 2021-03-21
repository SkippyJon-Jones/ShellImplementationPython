import os
import subprocess
import signal
from job import job
from job import STATUS
import joblist
from pipline import pipline
import time


#signal handlers
# catches and forwards control-C to appropraite job
def forward_int (signum, FRM):
  if joblist.has_fg_job():
    j = joblist.get_fg_job();
    for p in j.processes:
      os.kill(p.subprocess.pid, signal.SIGINT)

# catches and forwards control-z
def forward_stop (signum, FRM):
  if joblist.has_fg_job():
    j = joblist.get_fg_job();
    for p in j.processes:
      os.kill(p.subprocess.pid, signal.SIGTSTP)

# handles any change in child status(exited/terminated, continued, paused)
# updating the process status and corresponding job in the jobs list.
# Initially this function was meant to be a signal handler, but we could not
# block child signals in python (the googled approaches did not successfully
# block them) thus to avoid race conditions we just call this function at 
# the appropriate times.
def child_handler ():
  while True: #make sure to clean up all children
    try:
      child = os.waitpid (-1, os.WNOHANG | os.WCONTINUED | os.WUNTRACED)
      # child will be a tuple of (pid, exit_status)
      if child == (0,0):
        break;
      pid = child[0]
      exit_status = child[1]

      # get the job from the global joblist that contains
      # subprocess with pid pid
      j = joblist.get_job_with_process(pid)
      # get the subprocess from the job that matches pid pid

      p = j.get_subprocess (pid)
      
      # updates the status of the child process
      if(os.WIFEXITED (exit_status)):
        p.set_status (STATUS.TERMINATED)
      elif(os.WIFSTOPPED (exit_status)):
        p.set_status (STATUS.STPPED)
      elif(os.WIFCONTINUED (exit_status)):
        p.set_status (STATUS.RUNNING)

      # if the child was terminated by signal, print the relevant information
      elif(os.WIFSIGNALED(exit_status)):
        print("Job pid: " + str(pid) + " terminated by signal: " + str(os.WTERMSIG(exit_status)))
        p.set_status (STATUS.TERMINATED)

           
      # updates job list by looking at subprocesses
      joblist.synchronize (j)

    except OSError:
      break

# handles all builtin functions, except exit
def handle_builtin(p):
  command = p.commands[0][0]
  #Change Directory
  if command == "cd":
    try:
      os.chdir(p.commands[0][1])
    except:
      print("cd: no such file or directory:")
    return True
  #Print Current Location
  elif command == "help":
    print("Shell builtins: cd, help, jobs, bg, fg")
    return True
  elif command == "pwd":
    print(os.getcwd())
    return True
  #print active jobs
  elif command == "jobs":
    if joblist.length() == 0:
      print("There are no jobs activley running at this time")
    else:
     joblist.print_jobs() 
     return True
  elif command == "bg":
    bgjob = int(p.commands[0][1])

    #finds the appropriate job to send a SIGCONT to
    j = joblist.get_job_with_process (bgjob)

    #send a SIGCONT to each subprocess in the job
    for p in j.processes:
      os.kill (p.subprocess.pid, signal.SIGCONT)
    return True;
  elif command == "fg":
    fgjob = int(p.commands[0][1])
    
    #finds the appropriate job to send a SIGCONT to
    j = joblist.get_job_with_process(fgjob)
    j.fg = True
    
    #send a SIGCONT to each subprocess in the job
    for p in j.processes:
      os.kill (p.subprocess.pid, signal.SIGCONT)

    # wait for job to finish/no longer be in the foreground
    while (joblist.has_fg_job()):
      time.sleep(.01)
      child_handler()
    return True
  else:
    return False

def execute(p):
  j = None
  if len(p.commands) > 1:

    # iterate over all the commands that are piped
    for i in range(len(p.commands)):

      # first command in the pipeline
      if (i == 0):
        proc = None
        
        # checks if there is input redirection
        if p.input != "":
          fd = os.open (p.input, os.O_RDONLY)
          proc = subprocess.Popen(p.commands[i], preexec_fn=os.setpgrp, stdin=fd,
          stdout=subprocess.PIPE) 
        # else runs it normally
        else:
          proc = subprocess.Popen(p.commands[i], preexec_fn=os.setpgrp, stdout=subprocess.PIPE)
        j = joblist.add_job(p.fg)
        j.add_process(proc)
      # deals with last command in pipeline
      elif (i == len(p.commands)-1):
        in_proc = j.processes[i-1]
        proc = None
        # checks for output redirection and deals with it accordingly
        if p.output != "":
          fd_out = os.open(p.output, os.O_CREAT | os.O_WRONLY)
          proc=subprocess.Popen(p.commands[i], preexec_fn=os.setpgrp, stdin=in_proc.subprocess.stdout,
          stdout=fd_out)
        # else runs last command normally
        else:
          proc=subprocess.Popen(p.commands[i], preexec_fn=os.setpgrp, stdin=in_proc.subprocess.stdout) 
        j.add_process(proc)
      # if command is not last or first in the pipeline
      else:
        in_proc = j.processes[i-1]
        proc=subprocess.Popen(p.commands[i], preexec_fn=os.setpgrp, stdin=in_proc.subprocess.stdout, stdout=subprocess.PIPE) 
        j.add_process(proc)
  else:
    # creates singular process within a job
    proc = None
    # both input and output redirection case
    if p.input != "" and p.output != "":
      fd_in = os.open (p.input, os.O_RDONLY)
      fd_out = os.open(p.output, os.O_CREAT | os.O_WRONLY)
      proc = subprocess.Popen(p.commands[0], preexec_fn=os.setpgrp, stdin=fd_in, stdout=fd_out) 

    # just input redirection
    elif p.input != "":
      fd = os.open (p.input, os.O_RDONLY)
      proc = subprocess.Popen(p.commands[0], preexec_fn=os.setpgrp, stdin=fd) 

    # just output redirection
    elif p.output != "":
      fd_out = os.open(p.output, os.O_CREAT | os.O_WRONLY)
      proc = subprocess.Popen(p.commands[0], preexec_fn=os.setpgrp, stdout=fd_out) 

    # no input or output redirection
    else:
      proc = subprocess.Popen(p.commands[0], preexec_fn=os.setpgrp)    
    j = job(p.fg)
    j.add_process(proc)
    joblist.jobs.append(j)

  while (joblist.has_fg_job()):
    # repeatedly checking if any child process has finished
    time.sleep(.01)
    child_handler()

def main():
  #install signal handlers
  signal.signal(signal.SIGINT, forward_int)
  signal.signal(signal.SIGTSTP, forward_stop)

  #declare global joblist - must be global to be accessed by signal handlers
  global joblist
  joblist = joblist.joblist ()
  while True:
    try:
      print(" ")
      commandline = input((" ( ͡° ͜ʖ ͡°) $ "))
      if commandline.strip() == "exit":
        break
      p = pipline (commandline)
      builtin = handle_builtin (p)
      if builtin == False:
        execute (p)
        child_handler()
    except: 
      print("Error: command could not be executed")

if '__main__' == __name__:
  main()