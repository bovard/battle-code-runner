"""Module Docstring
This is a module for generating circles and squares!
"""
import getopt
import json
import os
import random
import sys

from PIL import Image, ImageDraw


class Constants:
    """
    A constants for all our magic strings
    """
    TOC_NAME = 'toc.json'
    MAX_HEIGHT = 'max_height'
    MAX_WIDTH = 'max_width'
    FILE_NAME = 'file_name'
    WIDTH = 'width'
    HEIGHT = 'height'
    PAGES = 'pages'
    FILE_FORMAT_NAME = "{}.png"


def check(files):
    """
    Loops through all the shapes and draws them, makes a toc with all pages
    """

    for file in files:




def fudge():
    """
    returns a small fudge factor
    """
    return random.randrange(-10, 10)


def look_at_image(file):
    """
    Draws a page to specifications
    """
    pass



def main():
    """
    main funciton, starts the program
    """
    # parse command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h", ["help"])
    except getopt.error, msg:
        print msg
        print "for help use --help"
        sys.exit(2)
    # process options
    for o, a in opts:
        if o in ("-h", "--help"):
            print __doc__
            sys.exit(0)
    # process arguments

    check(args)


if __name__ == "__main__":
    main()