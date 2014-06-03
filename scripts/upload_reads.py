#!/usr/bin/env python
import argparse
import genapi

parser = argparse.ArgumentParser(description='Upload NGS reads to the Genesis platform.')

parser.add_argument('-a', '--address', default='http://cloud.genialis.com', help='GenCloud url')
parser.add_argument('-e', '--email', default='anonymous@genialis.com', help='Sign-in e-mail')
parser.add_argument('-p', '--password', default='anonymous', help='Sign-in password')
parser.add_argument('-r', metavar='READS', help='NGS fastq file')
parser.add_argument('-r1', metavar='READS-1', help='NGS fastq file (mate 1)')
parser.add_argument('-r2', metavar='READS-2', help='NGS fastq file (mate 2)')

args = parser.parse_args()

if not (args.r or (args.r1 and args.r2)) or \
    (args.r and (args.r1 or args.r2)):
    parser.print_help()
    print
    print "ERROR: define either -r or -r1 and -r2."
    print
    exit(1)

if args.r:

    pass


