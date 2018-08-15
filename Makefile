all:
	@echo "This Makefile is only used to edit files"
	@echo "Run ./flickr_images_grab.py or read README.md for help"
	@echo
	@echo "Try: make vi"
	@echo "(Use :q<enter> to quit vi, in case you didn't know."

vi:
	vim Makefile flickr_images_grab.py config.json keywords.txt bansi.py
