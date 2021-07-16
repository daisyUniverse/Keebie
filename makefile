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
	-d python3 \
	-m "Michael Basaj <michaelbasaj@protonmail.com>" \
	--after-install "./packaging/postinst" \
	./keebie.py=/usr/bin/keebie \
	./config=/usr/share/keebie/config \
	./layers/=/usr/share/keebie/layers \
	./settings.json=/usr/share/keebie/

check-for-changes:
	@echo "MODIFIED FILES"
	@git status --porcelain | grep -E "^ ?M" || echo "None"

	@echo "NEW FILES"
	@git status --porcelain | grep -E "^ ?\?" || echo "None"

	@echo "DELETED FILES"
	@git status --porcelain | grep -E "^ ?D" || echo "None"
