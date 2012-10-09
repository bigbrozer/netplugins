default:

distclean: clean clean-deb

clean: py-bytecode backup-files
	@dh_clean

clean-deb:
	@echo "Cleaning package creation directory..."
	@rm -rf ./pkg-build

py-bytecode:
	@echo 'Cleaning Python byte code files...'
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +

backup-files:
	@echo 'Cleaning backup files...'
	@find . -name '*~' -exec rm -f {} +
	@find . -name '#*#' -exec rm -f {} +

