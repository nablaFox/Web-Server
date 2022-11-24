import re, os, subprocess, sys

sys.stdout.reconfigure(encoding='utf-8')

# the print() method is equivalent to "echo" in PHP and is the method for display output of python scripts in html page
# add sys.stdout.reconfigure(encoding='utf-8') to python's scripts that you want to implement

class Interpreter:
    
    def __init__(self, file):
        self.file = file
        self.page, self.new_content = None, None

        try:
            with open(file, 'rb') as reader:
                self.page = reader.read().splitlines()
        except:
            print("File Not Found")
        
        if self.page:
            self.run()

    def get_path(self, line):
        path = re.search('"(.*)"', line)
        return path.group(1) 

    def get_output(self, path):

        file_dir = os.path.dirname(self.file)
        cmd = "python " + '"' + file_dir + "/" + path + '"'
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout = p.communicate()[0]
        p.stdout.close()

        return stdout

    def run(self):

        for row in range(len(self.page)):
            line = self.page[row].decode('utf-8')
            if "</py-script>" in line:

                script = self.get_path(line) # prendi il percorso dello script
                output = self.get_output(script) # esegui lo script e prendi il suo output

                if output:
                    self.page[row] = output # sostituisci l'output dello script all'interno del tag (della riga)

        self.new_content = ""

        for row in range(len(self.page)):
            self.new_content += self.page[row].decode('utf-8') + "\n"

    def content(self):
        return self.new_content.encode('utf-8')
