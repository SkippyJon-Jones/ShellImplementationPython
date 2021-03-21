import glob
import subprocess
class pipline:
  def __init__(self, command):
      
    #checks for input and output redirection and deals with it accordingly
    (result, command) = self.find_in_out(command, ">")
    self.output = result
    (result, command) = self.find_in_out(command, "<")
    self.input = result

    self.commands = []
    if "&" in command:
      self.fg = False
      command = command.split (" &")[0]
    else:
      self.fg = True
    
    
    for c in command.strip().split("|"):
      quoted_text = ""
      index = -1
      double = False
      single = False
      if '\"' in c:
        double = True

      if '\'' in c:
        single = True
        index = c.find("\'")
        quoted_text = c[index + 1:c.rfind("\'")]
        c = c.replace(c[index:c.rfind("\'") + 1], "")

      if not double:
          # use "+" as a placeholder for the space with the command
          # only accounts for escaping from spaces, not other chars
         command_list = c.replace("\ ", "+")
      else:
        command_list = c

      command_list = self.subcommand(command_list)

      if double:
        index = command_list.find("\"")
        quoted_text = command_list[index + 1:command_list.rfind("\"")]
        command_list = command_list.replace(command_list[index:command_list.rfind("\"") + 1], "")

      # split the command into its respective parts
      command_list = command_list.strip().split(" ") # cat *.txt --> [cat, *.txt]
      final_list = [] # [cat]
      for elemWithoutSpaces in command_list:
        # insert the spaces into the file name
        elem = elemWithoutSpaces.replace("+", " ")
        # deal with globbing   
        if "*" in elem or "?" in elem:
          for found in glob.glob(elem): 
            final_list.append(found)
        else:
          final_list.append(elem)
      if double or single:
        if "$" not in quoted_text:
          final_list.append(quoted_text)
      self.commands.append(final_list)

  # deals with subcommands within input
  def subcommand(self, elem):
    # checks for the subcommand token
    if "$(" in elem:
      # gets the subcommand out of the input
      start_index = elem.find("$(")
      end_index = elem.find(")")
      subcmd = elem[start_index+2:end_index]

      # creates a process from the subcommand
      proc = subprocess.Popen(subcmd.split(" "), stdout = subprocess.PIPE)
      # gets output from the subprocess
      (stdout, stderr) = proc.communicate()
      proc.wait()

      # changes from bits to string
      encoding = 'utf-8'
      stdout = stdout.decode(encoding)

      # replaces the subcommand with the output from the 
      # subcommand
      replaced = elem[start_index:end_index+1]
      elem = elem.replace(replaced, stdout)
      return elem
    else:
      return elem      

   #
  def find_in_out (self, command, char):
    result = ""
    # if there is no input or output redirect, return command unmodified
    if char not in command:
      return ("", command)
    index = command.find(char) #cat file.txt >  hello.txt 
    start_ind = index + 1
    # checks for spaces between arguments
    while (command[start_ind] == " "):
      start_ind += 1
    end_ind = start_ind

    # find end index of output/input redirection goal
    while (end_ind < len(command) and command[end_ind] != " "):
      end_ind +=1

    # output/input to "result" file
    result = command[start_ind:end_ind]
    # isolate the command from the output/input file
    command = command[0:index] + command[end_ind:]
    return (result, command)