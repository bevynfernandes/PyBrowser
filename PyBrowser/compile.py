import os
import secrets
from shutil import rmtree

import config

defaults = {"name": "Microsoft Word"}
vars = {}
clean = True

def main():
	"""Auto compiles PyBrowser into a .exe
	A few notes:
	- The package will be encrypted using a random string generated by secrets.token_urlsafe().
	- The config will be regenerated using ./PyBrowser/config.py, so edit the configuration using the script and not the .json as that will be lost.
	"""
	if os.path.isfile("main.py"):
		os.chdir("..")
	
	cwd: str = f"{os.getcwd()}/PyBrowser"
	vars["name"]: str = input(f"What name to save as (Enter for default: {defaults['name']}): ")
	if vars["name"] == "":
		vars["name"]: str = defaults["name"]
	
	vars["app_type"]: str = input(f"Show command window in the compiled app? - Y/N: ")
	if vars["app_type"].lower() == "y":
		vars["app_type"] = "console"
	else:
		vars["app_type"] = "windowed"

	config.smain(f"{cwd}/config.json")
	print(f"{vars=}")
	command = f'py -m PyInstaller --noconfirm --onefile --{vars["app_type"]} --icon "{cwd}/images/icon.ico" --name "{vars["name"]}" --clean --key "{secrets.token_urlsafe()}" --add-data "{cwd}/images;images/" --add-data "{cwd}/overload;overload/" --add-data "{cwd}/config.json;." "{cwd}/main.py"'

	os.system(command)
	if clean:
		print("Cleaning up...")
		rmtree("build")
		os.remove(f"{vars['name']}.spec")
	print(f"The exe has been saved as: ./dist/{vars['name']}.exe")

if __name__ == "__main__":
	main()