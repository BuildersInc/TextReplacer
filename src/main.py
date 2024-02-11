import os
import logging
import argparse
import glob
import json
import re
import time
import tkinter as tk
from tkinter import filedialog

VERSION = "1.2"

SCRIPT_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_PATH)

class Window(tk.Tk):
    def __init__(self, title: str = "Text replacer",
                 size: str = "400x400",
                 home_dir: str = __file__) -> None:

        super().__init__()
        self.title(f"{title}: Version {VERSION}")
        self.geometry(size)

        self.quit_button = tk.Button(self, text="Open Project Folder",
                                     command=self.open_project_handler)

        self.quit_button.config(bg="red")
        self.quit_button.pack()

        self.load_config = tk.Button(self, text="Open Config File",
                                     command=self.open_config_handler)
        self.load_config.config(bg="red")
        self.load_config.pack()

        self.replace_all = tk.Button(self, text="Replace All",
                                     command=self.replace_all_handler)
        self.replace_all.pack()

        self.dry_run = tk.Button(self, text="Dry Run",
                                 command=self.dry_run_handler)
        self.dry_run.pack()

        self.home_dir = home_dir
        self.replace_config = None
        self.loaded_files = None

    def open_project_handler(self):
        filepath = filedialog.askdirectory(title="Open Dirs",
                                           initialdir=self.home_dir)
        print(filepath)
        self.loaded_files = self.find_files_in_dir(filepath)
        if self.loaded_files:
            self.quit_button.config(bg="green")
            self.save_project_history(filepath)

    def find_files_in_dir(self, path: str, file_suffix: str = "sht") -> list[str]:
        """
        Searches for a file type and returnes a list of paths to all files
        in this directory using this file suffix

        Args:
            path (str): path to start looking
            file_suffix (str, optional): filetype to search. Defaults to "sht".

        Returns:
            list[str]: List of paths
        """
        files = glob.glob(f"{path}/**/*.{file_suffix}", recursive=True)
        print(files)
        return files

    def open_config_handler(self):
        filetypes = (
                ('Config file', "*.json"),
                ('All files', '*.*')
            )

        filepath = filedialog.askopenfilename(title='OpenConfig File',
                                              initialdir=self.home_dir,
                                              filetypes=filetypes)
        with open(filepath, "r", encoding="utf-8") as config_file:
            json_config = json.loads(config_file.read())
            config = {}
            for _, values in json_config.items():
                # Item is not active
                if not values.get("Active", "True") == "True":
                    continue
                config |= {values.get("OldValue"): values.get("NewValue")}
        self.replace_config = config
        if self.replace_config:
            self.load_config.config(bg="green")
        print(self.replace_config)

    def replace_all_handler(self):
        if not self._check_files_are_loaded():
            return

        for current_file_path in self.loaded_files:
            # create a backup of the current file
            text = None
            replaced_text = None
            with open(current_file_path, "r") as current:
                with open(f"{current_file_path}.{time.time()}.old", "w") as old:
                    text = current.read()
                    replaced_text = text
                    old.write(text)
            # Replace the items
            for from_value, to_value in self.replace_config.items():
                pattern = r'\b' + re.escape(from_value) + r'\b'
                replaced_text = re.sub(pattern, to_value, replaced_text)
            # Save the replaced text
            with open(current_file_path, "w", encoding="utf-8") as current:
                current.write(replaced_text)

    def dry_run_handler(self):
        if not self._check_files_are_loaded():
            return
        for current_file_path in self.loaded_files:
            # create a backup of the current file
            text = None
            counter = {}
            with open(current_file_path, "r") as current:
                text = current.read()
            # Replace the items
            for from_value, _ in self.replace_config.items():
                pattern = r'\b' + re.escape(from_value) + r'\b'
                amount = len(re.findall(pattern, text))
                counter |= {from_value: amount}
            print(f"In file {current_file_path} would have replaced {counter}")

    def save_project_history(self, last_dir):
        with open(f"{SCRIPT_DIR}/history", "w", encoding="utf-8") as history:
            history.write(last_dir)

    def _check_files_are_loaded(self) -> bool:
        if not self.replace_config:
            logging.critical("Please load config file first")
            return False
        if not self.loaded_files:
            logging.critical("Please load Project files first")
            return False
        return True

def get_parser():
    """
    Generate an argument parser
    :return: New argument parser
    """
    new_parser = \
        argparse.ArgumentParser(description='<ScriptDescription>',
                                formatter_class=argparse.RawTextHelpFormatter)

    new_parser.add_argument('-v', '--verbosity', required=False, action='count', default=False,
                            help='increase output verbosity (e.g.: -vv is more than -v).')

    return new_parser

def main(args):
    home_dir = __file__
    if os.path.exists(f"{SCRIPT_DIR}/history"):
        with open(f"{SCRIPT_DIR}/history", "r", encoding="utf-8") as history:
            home_dir = history.readline()
    window = Window(home_dir=home_dir)
    # Run the Tkinter event loop
    window.mainloop()



if __name__ == "__main__":
    parser = get_parser()
    parsed_args = parser.parse_args()
    LOG_FORMAT = '[%(asctime)s.%(msecs)03d|%(levelname)s|%(name)s] %(message)s'
    # level is set to 10 (DEBUG) if -v is given, 9 if -vv, 8 if -vvv and so on. Otherwise to 20 (INFO)
    level = logging.DEBUG - parsed_args.verbosity + 1 if parsed_args.verbosity > 0 else logging.INFO
    logging.basicConfig(format=LOG_FORMAT, datefmt='%H:%M:%S', level=level)
    main(args=parsed_args)
