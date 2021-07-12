export SHELL=/bin/bash

export bin_path="/usr/bin/keebie"
export install_path="/usr/share/keebie/"


# .SILENT:

pre-pkg: check-for-changes


deb: pre-pkg deb-build
	@echo -e "\nbuilt a .deb package with dpkg-buildpackage"


deb-build:
	@echo -e "\narchiving package...\n"
	dpkg-buildpackage -us -uc -F
	rm -rfv "./debian/files"


check-for-changes:
	@echo "MODIFIED FILES"
	@git status --porcelain | grep -E "^ ?M" || echo "None"

	@echo "NEW FILES"
	@git status --porcelain | grep -E "^ ?\?" || echo "None"

	@echo "DELETED FILES"
	@git status --porcelain | grep -E "^ ?D" || echo "None"
