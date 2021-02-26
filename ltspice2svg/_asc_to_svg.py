import argparse
from ltspice2svg import *


parser = argparse.ArgumentParser()
parser.add_argument('asc_file')
parser.add_argument('svg_file')
args = parser.parse_args()


draw(args.asc_file, args.svg_file)
