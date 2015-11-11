#!/usr/bin/env python
import argparse
import genesis

parser = argparse.ArgumentParser(description='Upload a batch NGS reads to the Genesis platform.')

parser.add_argument('project', help='Project id')
parser.add_argument('-a', '--address', default='http://cloud.genialis.com', help='GenCloud url')
parser.add_argument('-e', '--email', default='anonymous@genialis.com', help='Sign-in e-mail')
parser.add_argument('-p', '--password', default='anonymous', help='Sign-in password')
parser.add_argument('-r', metavar='READS', nargs='*', help='List of NGS fastq files')
parser.add_argument('-r1', metavar='READS-1', nargs='*', help='List of NGS fastq files (mate 1)')
parser.add_argument('-r2', metavar='READS-2', nargs='*', help='List of NGS fastq files (mate 2)')

args = parser.parse_args()

if not (args.r or (args.r1 and args.r2)) or \
    (args.r and (args.r1 or args.r2)):
    parser.print_help()
    print
    print "ERROR: define either -r or -r1 and -r2"
    print
    exit(1)

if not args.r and len(args.r1) != len(args.r2):
    parser.print_help()
    print
    print "ERROR: -r1 and -r2 file list length must match"
    print
    exit(1)

g = genesis.Genesis(args.email, args.password, args.address)

if args.r:
    for r in args.r:
        r = g.upload(args.project, 'import:upload:reads-fastq', src=r)
else:
    for r1, r2 in zip(args.r1, args.r2):
        r = g.upload(args.project, 'import:upload:reads-fastq-paired-end', src1=r1, src2=r2)
