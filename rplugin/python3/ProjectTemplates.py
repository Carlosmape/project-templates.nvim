import pynvim
import re
import os
import shutil
from binaryornot.check import is_binary


@pynvim.plugin
class ProjectTemplate(object):
    def __init__(self, vim):
        self.vim = vim
        self.projectDir = f"{os.path.expanduser('~')}/.templates"
        self.projects = {}
        self.tokenized_files = []
        self.tokenized_file_names = []
        self.tokens = []
        self.token_values = []

        if not os.path.isdir(self.projectDir):
            os.mkdir(self.projectDir)

    @pynvim.command("LoadTemplate", sync=True)
    def loadTemplate(self):
        dir = os.listdir(self.projectDir)
        self.vim.command(f'let choice = Finder({str(dir)}, "Enter the name of the template")')
        to_load = self.vim.eval('choice[0]')

        projectName = self.vim.eval('input("Enter the name of the project> ")')
        pwd = self.vim.eval('getcwd()')
        projectName = os.path.join(pwd, projectName)

        if os.path.isdir(projectName):
            overwrite = self.vim.eval(f'input("Project {os.path.basename(projectName)} already exists. Overwrite? (y/n) ")')
            if overwrite.startswith('y'):
                shutil.rmtree(projectName)
            else:
                return

        shutil.copytree(os.path.join(self.projectDir, to_load), projectName)
        self.vim.chdir(projectName)

        self.getTokensFromProject(projectName)
        self.replaceTokens()

        self.vim.command("redraw | echo")
        self.vim.out_write(f"\nTemplate {to_load} Loaded Successfully.\n")

    def getTokensFromProject(self, projectName):
        r = re.compile(r'#{[^}]+}')
        for currentfolder, subfolders, files in os.walk(projectName):
            for file in files:
                file_path = os.path.join(currentfolder, file)
                if not is_binary(file_path):

                    # Look for tokenized file names (tokens are in the file name)
                    file_matches = r.findall(file)
                    for file_match in file_matches:
                        print('{file_match} token in file {file_path}')
                        if file_path not in self.tokenized_file_names:
                            self.tokenized_file_names.append(file_path)
                        if file_match not in self.tokens:
                            self.tokens.append(file_match)

                    # Look for tokenized files (tokens are inside file contents)
                    with open(file_path, 'r') as tosearch:
                        contents = tosearch.read()
                        matches = r.findall(contents)
                        print(f'{matches} in file {file_path}')

                        for match in matches:
                            if match not in self.tokens:
                                self.tokens.append(match)

                    if file_path not in self.tokenized_files:
                        self.tokenized_files.append(file_path)

        print(self.tokens)

    def replaceTokens(self):
        """User insert new loaded tokens values and does replacement where it is needed""" 
        # Ask user to replace token with desired value
        for token in self.tokens:
            token_value = self.vim.eval(f'input("Enter the value for the token {token}> ")')
            self.token_values.append((token, token_value))
        
        # Replace tokens in file's content with given value
        for file in self.tokenized_files:
            with open(file, 'r') as toread:
                content = toread.read()
            for token, value in self.token_values:
                r = re.compile(token)
                content = r.sub(value, content)
            with open(file, 'w') as towrite:
                towrite.write(content)

        # Replace tokens in file's names with given value
        for file in self.tokenized_file_names:
            for token, value in self.token_values:
                # Ensure this token is inside this tokenized file name
                if token in file: 
                    r = re.compile(token)
                    file_name = r.sub(value, file)
                    os.rename(file, file_name)

    @pynvim.command("SaveAsTemplate", sync=True)
    def saveAsTemplate(self):
        pwd = self.vim.eval('getcwd()')
        template_name = self.vim.eval('input("Enter the name of the new template> ")')

        # shutil.copytree(pwd, self.projectDir + os.sep() + template_name)
        shutil.copytree(pwd, f'{self.projectDir}/{template_name}')


        self.vim.command("redraw | echo")
        self.vim.command(f"echo 'Template {template_name} Created.'")

    @pynvim.command("DeleteTemplate", sync=True)
    def deleteTemplate(self):
        dir = os.listdir(self.projectDir)
        self.vim.command(f'let choice = Finder({str(dir)}, "Enter the name of the template to delete")')
        to_delete = self.vim.eval('choice[0]')
        to_delete = os.path.join(self.projectDir, to_delete)

        if os.path.isdir(to_delete):
            shutil.rmtree(to_delete)

        self.vim.command("redraw | echo")
        self.vim.command(f"echo 'Template {os.path.basename(to_delete)} Deleted Successfully.'")

