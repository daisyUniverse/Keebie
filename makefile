SHELL=/bin/bash

bin_path="/usr/bin/keebie"
install_path="/usr/share/keebie/"

pkg_type="tar"

# .SILENT:

pre-pkg: check-for-changes


pkg: pre-pkg 
	fpm --verbose -f \
	-t $(pkg_type) \
	-s dir \
	-a all \
	-p ../ \
	-n keebie \
	-d python3 -d python3-evdev \
	-m "Michael Basaj <michaelbasaj@protonmail.com>" \
	./keebie.py=$(bin_path) \
	./config=$(install_path) \
	./layers/=$(install_path)/layers \
	./settings.json=$(install_path)

	# --before-install "./packaging/preinst" \
	# --after-install "./packaging/postinst" \
	# --before-install "./packaging/prerm" \
	# --after-remove "./packaging/postem" \
	
check-for-changes:
	@echo "MODIFIED FILES"
	@git status --porcelain | grep -E "^ ?M" || echo "None"

	@echo "NEW FILES"
	@git status --porcelain | grep -E "^ ?\?" || echo "None"

	@echo "DELETED FILES"
	@git status --porcelain | grep -E "^ ?D" || echo "None"
