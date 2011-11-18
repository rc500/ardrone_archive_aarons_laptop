# Documentation source directory
SOURCEDIR=doc

# Documentation build directory
BUILDDIR=doc

all: html epub pdf

html:
	sphinx-build -b html $(SOURCEDIR) $(BUILDDIR)/html

epub:
	sphinx-build -b epub $(SOURCEDIR) $(BUILDDIR)/epub

pdf: latex
	$(MAKE) -C $(BUILDDIR)/latex/

latex:
	sphinx-build -b latex $(SOURCEDIR) $(BUILDDIR)/latex

clean:
	rm -rf $(BUILDDIR)/html
	rm -rf $(BUILDDIR)/epub
	rm -rf $(BUILDDIR)/latex

sync: html
	rsync -av --delete $(BUILDDIR)/html/ l4.me.uk:~/public_html/ardrone

.PHONY: all clean html epub pdf latex sync

# vim:ts=8:noet:sts=8
