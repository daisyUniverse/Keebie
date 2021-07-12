SHELL=/bin/bash

make_output_path="./.made/"

bin_path="/usr/bin/keebie"
install_path="/usr/share/keebie/"

pkg_name="keebie"
pkg_version="1.1.1"

# .SILENT:

clean:
	@echo -e "\ncleaning...\n"

	rm -rfv $(make_output_path)

	@echo -e "\nclean"


deb-pkg: deb-pkg-data deb-pkg-control deb-pkg-build
	@echo -e "\nbuilt a .deb package with dpkg-buildpackage"


deb-pkg-data:
	@echo -e "\narranging data...\n"

	mkdir -pv $(make_output_path)"/deb-pkg/source/"$(pkg_name)"-"$(pkg_version)"/"

	cp -vr ./* $(make_output_path)"/deb-pkg/source/"$(pkg_name)"-"$(pkg_version)"/"


deb-pkg-control:
	@echo -e "\narranging control...\n"

	cp -vr "./package info/deb/"* $(make_output_path)"/deb-pkg/source/"$(pkg_name)"-"$(pkg_version)"/"


deb-pkg-build: deb-pkg-control deb-pkg-data
	@echo -e "\narchiving package...\n"

	cd $(make_output_path)"/deb-pkg/source/"$(pkg_name)"-"$(pkg_version)"/" && \
	dpkg-buildpackage -us -uc -F