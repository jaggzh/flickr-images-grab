all:
	@echo "This Makefile is only used to edit files"
	@echo "Run ./flickr_images_grab.py or read README.md for help"
	@echo
	@echo "make vi:      Edit files"
	@echo "make s:       Perform searches and store results in /search"
	@echo "make dl:      Download search results (pick dlfl/dlplain in Makefile)"
	@echo "make dlall:   Download images from search"
	@echo "make dlfl:    Download images from search requiring exif focallength"

vi:
	vim Makefile flickr_images_grab.py config.json keywords.txt keywords.txt-full bansi.py

s:  # Search (but we have a search/ dir so make will ignore such a rule)
	./flickr_images_grab.py --search

download: dl

dl: dlfl

dlfl:
	./flickr_images_grab.py --focallength --download

dlall:
	./flickr_images_grab.py --download
