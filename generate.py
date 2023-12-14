#!/bin/python
import os

from os.path import join, exists, isdir
from json import load
from subprocess import check_call
from shutil import copyfile
from argparse import ArgumentParser


# Setup
abs_path = "/".join(__file__.split("/")[0:-1])
base_projects = []
for file in os.listdir(abs_path):
    if isdir(join(abs_path, file)) and not file.startswith("."):
        base_projects.append(file)

# Create args
args_parser = ArgumentParser("generate-project")
args_parser.add_argument("project", help="project to generate", choices=base_projects)
args_parser.add_argument("-m", "--mkdir-path", metavar="path-dir", help="Create project directory", default=".", )
args_parser.add_argument("-o", "--options", metavar="options", help="Options project", default="")

args = args_parser.parse_args()
project = args.project
mkdir_path = args.mkdir_path
project_options = {}
if args.options:
    _options = args.options.split(";")
    for _op in _options:
        _arg, _value = _op.split(":")
        project_options[_arg] = _value

with open(join(abs_path, project, "settings.json"), 'r') as fp:
    settings = load(fp)


def refactor_content(content):
    for arg, value in project_options.items():
        print(arg, value)
        key = settings["options"].get(arg, None)

        if key:
            content = content.replace(key, value)

    return content


def create_file(file, path):
    example_file = file.get("example", None)
    file_path = join(path, file["name"])
    if example_file is not None:
        copyfile(join(abs_path, project, file["example"]), file_path)
        if settings.get("options", None):
            with open(file_path, "r") as fp:
                content = fp.read()

            content = refactor_content(content)
            with open(file_path, "w") as fp:
                fp.write(content)
        return

    with open(file_path, "w") as fp:
        content = file.get("content", None)

        if content is not None:
            if settings.get("options", None):
                content = refactor_content(content)
            fp.write(content)

        
def create_folder(folder, path):
    folder_path = join(path, folder["name"])
    os.mkdir(folder_path)

    for file in folder.get("files", []):
        create_file(file, folder_path)
    for folder in folder.get("folders", []):
        create_folder(folder, folder_path)


def refactor_name(filename):
    if settings.get("options", None):
        for arg, value in settings["options"].items():
            if value in filename:
                filename = filename.replace(value, project_options[arg])

    return filename

# Generate project
if not exists(mkdir_path):
    os.mkdir(mkdir_path)

os.chdir(mkdir_path)

for k, v in settings.items():
    match k:
        case "create-venv":
            if v:
                check_call("python -m venv venv", shell=True)
        case "requires":
            for package in v:
                check_call(["venv/bin/pip", "install", package])
        case "files":
            for file in v:
                file["name"] = refactor_name(file["name"])
                create_file(file, ".")
        case "folders":
            for folder in v:
                folder["name"] = refactor_name(folder["name"])
                create_folder(folder, ".")
                