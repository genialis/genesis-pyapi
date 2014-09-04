#!/usr/bin/env python
import sys
import argparse

import genapi


parser = argparse.ArgumentParser(description='POST a data object JSON.')

parser.add_argument('-a', '--address', default='http://cloud.genialis.com', help='GenCloud url')
parser.add_argument('-e', '--email', default='anonymous@genialis.com', help='Sign-in e-mail')
parser.add_argument('-p', '--password', default='anonymous', help='Sign-in password')

args = parser.parse_args()


s = sys.stdin.read()
print s

g = genapi.GenCloud(args.email, args.password, args.address)
g.rundata(s)
