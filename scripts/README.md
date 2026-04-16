```
aim_platform_admin/scripts/restructure.rope.py
```

### What it does, in order:

	1. Creates py/imports/, py/schedule/, py/diagnostics/ folders
	2.	Drops an empty __init__.py in each (makes them Python packages)
	3.	Loops through every move, using Rope to relocate the file and rewrite every import statement across app.py, webhook_service.py, and all other files that reference them

**RUN THIS SCRIPT ONLY ONCE**
If you run this script twice, the files won’t be at their original root location, on the second run and it’ll error on anything already moved
    
### Install:

```
py -m pip install rope
```
