import os, json

class Playbooks:
    def __init__(self):
        directory = "settings/filters"
        extension = ".filt"
        self.filters = {}
        for jfile in [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file)) and file.endswith(extension)]:
            with open(jfile, 'r') as file:
                self.filters[jfile.split('\\')[-1].split('.')[0]] = json.loads(file.read())
                file.close()

    def make(self):
        full = ''
        for name in sorted(self.filters):
            filters = self.filters[name]
            full += f'\nPlaybook: {name}\n'

            for entry in filters:
                full += f'A:\t{entry["and"][0]} {entry["and"][1]} {entry["and"][2]} \n'
                for entry_or in entry['or']:
                    full += f'\tO:\t{entry_or[0]} {entry_or[1]} {entry_or[2]} \n'
        
        with open('data/playbooks.txt', 'w') as file:
            file.write(full.expandtabs(4))
            file.close()